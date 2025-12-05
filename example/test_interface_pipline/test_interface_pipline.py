import kfp
from kfp import dsl, components, compiler, kubernetes
from typing import List, Dict, Optional

# --------------------------
# 1. 定义接口输入数据结构（标准化配置）
# --------------------------
class PipelineInterface:
    """Pipeline接口配置类，统一接收工作流参数"""
    def __init__(
        self,
        pipeline_name: str,
        pipeline_root: str,
        components: List[Dict],
        dependencies: Optional[Dict] = None,
        minio_config: Optional[Dict] = None
    ):
        """
        Args:
            pipeline_name: 工作流名称
            pipeline_root: 流水线根路径（MinIO的s3://bucket/路径）
            components: 组件配置列表，每个组件包含：
                {
                    "name": 组件名称（唯一）,
                    "image": 镜像地址,
                    "command": 入口命令（如["python", "/app/script.py"]）,
                    "arguments": 固定参数（如["--epochs", 10]）,
                    "inputs": 输入路径配置（如{"raw_data": "s3://bucket/raw/data.csv"}）,
                    "outputs": 输出路径配置（如{"clean_data": "s3://bucket/processed/data.csv"}）
                }
            dependencies: 依赖关系（如{"train": ["preprocess"]}，表示train依赖preprocess）
            minio_config: MinIO配置（{"endpoint": "xxx", "secret_name": "xxx"}）
        """
        self.pipeline_name = pipeline_name
        self.pipeline_root = pipeline_root
        self.components = components
        self.dependencies = dependencies or {}
        self.minio_config = minio_config or {}

# --------------------------
# 2. 核心Pipeline生成函数（接口实现）
# --------------------------
def create_dynamic_pipeline(interface: PipelineInterface):
    """根据接口配置动态生成Pipeline"""
    def _sanitize_pipeline_name(name: str) -> str:
        s = ''.join(ch if ch.isalnum() or ch == '-' else '-' for ch in name.lower())
        s = s.strip('-')
        if not s or not s[0].isalnum():
            s = f"p-{s}" if s else "pipeline"
        return s[:128]

    @dsl.pipeline(
        # name="dynamic-pipeline",
        name=_sanitize_pipeline_name(interface.pipeline_name),
        pipeline_root=interface.pipeline_root,
        description=f"动态生成的工作流：{interface.pipeline_name}",
        display_name=interface.pipeline_name
    )
    def dynamic_pipeline():
        components_by_name = {cfg["name"]: cfg for cfg in interface.components}

        def apply_minio_config(task):
            # 注入 Region
            task.set_env_variable('AWS_REGION', 'us-east-1')
            # 注入 Endpoint (使用 IP 绕过 DNS 问题)
            task.set_env_variable('AWS_ENDPOINT_URL', 'http://10.96.1.54:9000')
            task.set_env_variable('AWS_ENDPOINT_URL_S3', 'http://10.96.1.54:9000')
            # 强制 Path Style
            task.set_env_variable('S3_FORCE_PATH_STYLE', 'true')
            task.set_env_variable('AWS_S3_FORCE_PATH_STYLE', 'true')
            task.set_env_variable('AWS_USE_PATH_STYLE_REQUESTS', 'true')
            task.set_env_variable('AWS_S3_USE_PATH_STYLE', 'true')
            
            # 注入凭证
            if interface.minio_config:
                 secret_name = interface.minio_config.get('secret_name', 'mlpipeline-minio-artifact')
                 kubernetes.use_secret_as_env(
                    task=task,
                    secret_name=secret_name,
                    secret_key_to_env={
                        'accesskey': 'AWS_ACCESS_KEY_ID',
                        'secretkey': 'AWS_SECRET_ACCESS_KEY'
                    }
                )
            
            # 禁用缓存
            task.set_caching_options(False)

        def sanitize_name(name: str) -> str:
            s = ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in name)
            if s and s[0].isdigit():
                s = '_' + s
            return s

        def build_component_yaml(cfg: Dict) -> str:
            name = cfg["name"]
            image = cfg["image"]
            command = cfg.get("command", [])
            orig_inputs = list(cfg.get("inputs", {}).keys())
            sanitized_inputs = [sanitize_name(k) for k in orig_inputs]
            orig_outputs = list(cfg.get("outputs", {}).keys())
            sanitized_outputs = [sanitize_name(k) for k in orig_outputs]
            args_const = [str(a) for a in cfg.get("arguments", [])]
            has_minio = bool(interface.minio_config)
            yaml_lines = [
                f"name: {name}",
                "implementation:",
                "  container:",
                f"    image: {image}",
            ]
            if command:
                yaml_lines.append("    command:")
                for c in command:
                    yaml_lines.append(f"      - '{c}'")
            yaml_lines.append("    args:")
            for a in args_const:
                yaml_lines.append(f"      - '{a}'")
            for orig_key, san_key in zip(orig_inputs, sanitized_inputs):
                # 预处理脚本仅接受 --output-data-dir，不注入其它输入参数
                if name == "preprocess":
                    continue
                # 训练镜像使用 --input-dir 读取数据集目录，注入 inputPath
                if name == "train" and orig_key.replace('-', '_') == "train_data":
                    yaml_lines.append("      - '--input-dir'")
                    yaml_lines.append(f"      - {{inputPath: {san_key}}}")
                else:
                    yaml_lines.append(f"      - '--{orig_key}'")
                    yaml_lines.append(f"      - {{inputValue: {san_key}}}")
            # 输出目录使用 OutputPath，占位符由后端注入
            for orig_key, san_key in zip(orig_outputs, sanitized_outputs):
                if name == "preprocess":
                    yaml_lines.append("      - '--output-data-dir'")
                    yaml_lines.append(f"      - {{outputPath: {san_key}}}")
                elif name == "train" and orig_key in orig_outputs:
                    yaml_lines.append("      - '--output-model-dir'")
                    yaml_lines.append(f"      - {{outputPath: {san_key}}}")
                else:
                    yaml_lines.append(f"      - '--{orig_key}'")
                    yaml_lines.append(f"      - {{outputPath: {san_key}}}")
            # 不注入 minio-endpoint，当前容器脚本未消费该参数

            input_section = []
            for orig_key, san_key in zip(orig_inputs, sanitized_inputs):
                input_section.append(f"  - name: {san_key}")
                if name == "train" and orig_key.replace('-', '_') == "train_data":
                    input_section.append("    type: Dataset")
                else:
                    input_section.append("    type: string")
            # 不声明未使用的 minio_endpoint 输入
            output_section = []
            for orig_key, san_key in zip(orig_outputs, sanitized_outputs):
                output_section.append(f"  - name: {san_key}")
                if name == "preprocess":
                    output_section.append("    type: Dataset")
                elif name == "train" and orig_key.replace('-', '_') == "trained_model":
                    output_section.append("    type: Artifact")
                else:
                    output_section.append("    type: string")
            insert_index = 1
            if input_section:
                yaml_lines.insert(insert_index, "inputs:")
                yaml_lines[insert_index+1:insert_index+1] = input_section
                insert_index += 1 + len(input_section)
            if output_section:
                yaml_lines.insert(insert_index, "outputs:")
                yaml_lines[insert_index+1:insert_index+1] = output_section
            return "\n".join(yaml_lines)

        loaded_components = {}
        for comp_name, cfg in components_by_name.items():
            # 优先使用已定义的 v2 组件以获得 Artifact 语义
            if comp_name == "preprocess":
                import os
                v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mnist_kubeflow_volcano", "mnist_preprocess_component.yaml"))
                loaded_components[comp_name] = components.load_component_from_file(v2_path)
                continue
            if comp_name == "train":
                import os
                v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mnist_kubeflow_volcano", "mnist_train_component.yaml"))
                loaded_components[comp_name] = components.load_component_from_file(v2_path)
                continue
            # 其它组件使用通用文本规范
            comp_yaml = build_component_yaml(cfg)
            loaded_components[comp_name] = components.load_component_from_text(comp_yaml)

        tasks = {}
        final_inputs_map: Dict[str, Dict[str, str]] = {}
        orig_to_san_keys: Dict[str, Dict[str, str]] = {}
        orig_to_san_outputs: Dict[str, Dict[str, str]] = {}
        for comp_name, cfg in components_by_name.items():
            inputs_map = dict(cfg.get("inputs", {}))
            san_map = {sanitize_name(k): v for k, v in inputs_map.items()}
            final_inputs_map[comp_name] = san_map
            orig_to_san_keys[comp_name] = {k: sanitize_name(k) for k in inputs_map.keys()}
            orig_to_san_outputs[comp_name] = {k: sanitize_name(k) for k in cfg.get("outputs", {}).keys()}
        # 构建任务时，若存在依赖，使用上游 task.outputs 作为下游输入
        for comp_name, cfg in components_by_name.items():
            comp = loaded_components[comp_name]
            call_kwargs = {}
            # 解析 arguments 中的数值参数（如 epochs, lr）
            def parse_args_to_kwargs(args_list):
                m = {}
                for i in range(0, len(args_list), 2):
                    try:
                        flag = str(args_list[i])
                        val = args_list[i+1]
                    except Exception:
                        continue
                    if flag == "--epochs":
                        m["epochs"] = int(val)
                    elif flag in ("--lr", "--learning-rate"):
                        m["lr"] = float(val)
                return m
            args_kwargs = parse_args_to_kwargs(cfg.get("arguments", []))

            # 针对 v2 预处理组件：支持可选外部原始数据 Dataset
            if comp_name == "preprocess":
                raw_data_uri = final_inputs_map.get("preprocess", {}).get("raw_data")
                if raw_data_uri:
                    raw_import = dsl.importer(
                        artifact_uri=raw_data_uri,
                        artifact_class=dsl.Dataset
                    )
                    task = comp(raw_data=raw_import.outputs['artifact'])
                else:
                    task = comp()
                apply_minio_config(task)
                tasks[comp_name] = task
                continue

            # 针对 v2 训练组件：仅传入 training_data、epochs、lr
            if comp_name == "train":
                # 依赖映射：来自预处理的 Dataset Artifact
                if "preprocess" in tasks:
                    call_kwargs["training_data"] = tasks["preprocess"].outputs["processed_data"]
                # 数值参数
                for k, v in args_kwargs.items():
                    call_kwargs[k] = v
                task = comp(**call_kwargs)
                apply_minio_config(task)
                tasks[comp_name] = task
                continue

            # 其它组件：使用通用输入映射与依赖替换
            for k, v in final_inputs_map.get(comp_name, {}).items():
                call_kwargs[k] = v
            if comp_name in interface.dependencies:
                for depend_comp in interface.dependencies[comp_name]:
                    if depend_comp in tasks:
                        for orig_input_key, san_input_key in orig_to_san_keys.get(comp_name, {}).items():
                            if orig_input_key in orig_to_san_outputs.get(depend_comp, {}):
                                up_san_out = orig_to_san_outputs[depend_comp][orig_input_key]
                                call_kwargs[san_input_key] = tasks[depend_comp].outputs[up_san_out]
            task = comp(**call_kwargs)
            apply_minio_config(task)
            tasks[comp_name] = task
        for target_comp, depend_comps in interface.dependencies.items():
            target_task = tasks[target_comp]
            for depend_comp in depend_comps:
                target_task.after(tasks[depend_comp])

    return dynamic_pipeline

# --------------------------
# 3. 接口调用示例（实际使用时只需修改此配置）
# --------------------------
if __name__ == "__main__":
    # 配置MinIO
    minio_config = {
        "endpoint": "http://10.96.1.54:9000",
        "secret_name": "mlpipeline-minio-artifact"  # 已创建的K8s Secret
    }

    # 配置工作流、组件、依赖关系
    pipeline_interface = PipelineInterface(
        pipeline_name="Dynamic Configuration - Data Preprocessing + Model Training",
        pipeline_root="s3://mlpipeline/test-pipeline-root",
        components=[
            # 组件1：数据预处理
            {
                "name": "preprocess",
                "image": "qiuchen123/kfp-mlops:mnist-prep-v2",
                "command": ["python", "/app/mnist_preprocess.py"],
                # "inputs": {"raw-data": "s3://mlpipeline/raw/train_data.csv"},
                "inputs": {"raw-data": "s3://mlpipeline/raw"},
                "outputs": {"clean-data": "s3://mlpipeline/processed/clean_data.csv"}
            },
            # 组件2：模型训练
            {
                "name": "train",
                "image": "qiuchen123/kfp-mlops:mnist-train-v1",
                "command": ["python", "/app/mnist_train.py"],
                "arguments": ["--epochs", 10, "--lr", 0.001],
                "inputs": {"train-data": "s3://mlpipeline/processed/clean_data.csv"},  # 后续会被依赖替换
                "outputs": {"trained-model": "s3://mlpipeline/models/trained_model.pkl"}
            }
        ],
        dependencies={
            "train": ["preprocess"]  # train依赖preprocess
        },
        minio_config=minio_config
    )

    # 生成Pipeline并编译
    dynamic_pipeline = create_dynamic_pipeline(pipeline_interface)
    out_path = __file__.rsplit(".", 1)[0].replace("test_interface_pipline", "test_interface_pipline")
    package_path = __file__.replace("test_interface_pipline.py", "dynamic-minio-pipeline.yaml")
    compiler.Compiler().compile(
        pipeline_func=dynamic_pipeline,
        package_path=package_path
    )
    print(f"Pipeline已生成：{package_path}")

    # 提交到KFP API Server运行（此示例暂不自动提交）
    from kfp import Client
    client = Client(host="http://localhost:30088")
    run = client.create_run_from_pipeline_package(
        pipeline_file=package_path,
        arguments={}
    )
    # print("Run URL:", run.run.url if hasattr(run.run, "url") else run.run.id)
    print("Run:", run)

