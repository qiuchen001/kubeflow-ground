import kfp
from kfp import dsl, components, compiler
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
                yaml_lines.append(f"      - '--{orig_key}'")
                yaml_lines.append(f"      - {{inputValue: {san_key}}}")
            if has_minio:
                yaml_lines.append("      - '--minio-endpoint'")
                yaml_lines.append("      - {inputValue: minio_endpoint}")

            input_section = []
            for san_key in sanitized_inputs:
                input_section.append(f"  - name: {san_key}")
                input_section.append("    type: string")
            if has_minio:
                input_section.append("  - name: minio_endpoint")
                input_section.append("    type: string")
            if input_section:
                yaml_lines.insert(1, "inputs:")
                yaml_lines[2:2] = input_section
            return "\n".join(yaml_lines)

        loaded_components = {}
        for comp_name, cfg in components_by_name.items():
            comp_yaml = build_component_yaml(cfg)
            loaded_components[comp_name] = components.load_component_from_text(comp_yaml)

        tasks = {}
        final_inputs_map: Dict[str, Dict[str, str]] = {}
        orig_to_san_keys: Dict[str, Dict[str, str]] = {}
        for comp_name, cfg in components_by_name.items():
            inputs_map = dict(cfg.get("inputs", {}))
            san_map = {sanitize_name(k): v for k, v in inputs_map.items()}
            final_inputs_map[comp_name] = san_map
            orig_to_san_keys[comp_name] = {k: sanitize_name(k) for k in inputs_map.keys()}
        for target_comp, depend_comps in interface.dependencies.items():
            target_inputs_san = final_inputs_map.get(target_comp, {})
            target_orig_to_san = orig_to_san_keys.get(target_comp, {})
            for depend_comp in depend_comps:
                depend_cfg = components_by_name[depend_comp]
                for orig_input_key, san_input_key in target_orig_to_san.items():
                    if orig_input_key in depend_cfg.get("outputs", {}):
                        target_inputs_san[san_input_key] = depend_cfg["outputs"][orig_input_key]
        for comp_name, cfg in components_by_name.items():
            comp = loaded_components[comp_name]
            call_kwargs = {}
            for k, v in final_inputs_map.get(comp_name, {}).items():
                call_kwargs[k] = v
            if interface.minio_config:
                call_kwargs["minio_endpoint"] = interface.minio_config["endpoint"]
            task = comp(**call_kwargs)
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
        "endpoint": "minio-service.kubeflow:9000",
        "secret_name": "minio-credentials"  # 已创建的K8s Secret
    }

    # 配置工作流、组件、依赖关系
    pipeline_interface = PipelineInterface(
        pipeline_name="Dynamic Configuration - Data Preprocessing + Model Training",
        pipeline_root="s3://kubeflow-pipeline/pipeline-root/",
        components=[
            # 组件1：数据预处理
            {
                "name": "preprocess",
                "image": "qiuchen123/kfp-mlops:mnist-prep-v1",
                "command": ["python", "/app/mnist_preprocess.py"],
                "inputs": {"raw-data": "s3://kubeflow-pipeline/raw/train_data.csv"},
                "outputs": {"clean-data": "s3://kubeflow-pipeline/processed/clean_data.csv"}
            },
            # 组件2：模型训练
            {
                "name": "train",
                "image": "qiuchen123/kfp-mlops:mnist-train-v1",
                "command": ["python", "/app/mnist_train.py"],
                "arguments": ["--epochs", 10, "--learning-rate", 0.001],
                "inputs": {"train-data": "s3://kubeflow-pipeline/processed/clean_data.csv"},  # 后续会被依赖替换
                "outputs": {"trained-model": "s3://kubeflow-pipeline/models/trained_model.pkl"}
            }
        ],
        dependencies={
            "train": ["preprocess"]  # train依赖preprocess
        },
        minio_config=minio_config
    )

    # 生成Pipeline并编译
    dynamic_pipeline = create_dynamic_pipeline(pipeline_interface)
    compiler.Compiler().compile(
        pipeline_func=dynamic_pipeline,
        package_path="dynamic-minio-pipeline.yaml"
    )
    print("Pipeline已生成：dynamic-minio-pipeline.yaml")

    # 提交到KFP API Server运行
    from kfp import Client
    client = Client(host="http://localhost:30088")
    run = client.create_run_from_pipeline_package(
        pipeline_file="dynamic-minio-pipeline.yaml",
        arguments={}
    )
    # print("Run URL:", run.run.url if hasattr(run.run, "url") else run.run.id)
    print("Run:", run)

