import os
from kfp import dsl
try:
    from kfp import kubernetes
    _HAS_KFP_K8S = True
except Exception:
    _HAS_KFP_K8S = False

from kfp.compiler import Compiler
from kfp.client import Client
from kfp.components import load_component_from_file

# --- 辅助函数：加载组件 YAML ---
def get_component_op(yaml_file):
    # 假设 YAML 文件在与此脚本同级的目录
    return load_component_from_file(os.path.join(os.path.dirname(__file__), "..", yaml_file))

# 加载组件 (确保组件 YAML 已经生成)
try:
    preprocess_op = get_component_op('mnist_preprocess_component.yaml')
    train_op = get_component_op('mnist_train_component.yaml')
except FileNotFoundError:
    print("错误: 找不到组件 YAML 文件。请先运行组件生成步骤。")
    exit(1)


# --- Pipeline 定义：DAG 结构和 Volcano 注入 ---
@dsl.pipeline(
    name='mnist-volcano-training',
    # 🌟 替换为你的实际 Artifact Store (e.g., gs://my-bucket/runs 或 s3://my-bucket/runs)
    pipeline_root='minio://minio-service.kubeflow.svc:9000/mlpipeline/mnist-runs' 
)
def mnist_pipeline(
    epochs: int = 10, 
    lr: float = 0.001
):
    # 1. 导入原始数据为 Dataset Artifact（可替换为你的实际路径）
    raw_data_importer = dsl.importer(
        # artifact_uri='s3://kubeflow-pipeline/raw/train_data.csv',
        # artifact_uri='minio://minio-service.kubeflow.svc:9000/mlpipeline/raw/train_data.csv',
        # artifact_uri='s3://minio-service.kubeflow.svc:9000/mlpipeline/raw/train_data.csv',
        artifact_uri='s3://mlpipeline/raw/train_data.csv',
        artifact_class=dsl.Dataset
    )
    # 2. 数据预处理任务
    prep_task = preprocess_op(raw_data=raw_data_importer.outputs['artifact'])
    
    # 3. 模型训练任务 (配置 Volcano 调度)
    train_task = train_op(
        # 串行依赖：数据传递 (KFP 自动处理路径映射)
        training_data=prep_task.outputs['processed_data'], 
        epochs=epochs,
        lr=lr
    )
    
    # --- 🌟 关键：Volcano 调度注入点 ---
    # 这将确保这个训练任务的 Pod 由 Volcano 调度器处理
    if _HAS_KFP_K8S:
        # 注入 MinIO 凭证
        kubernetes.use_secret_as_env(
            task=prep_task,
            secret_name='mlpipeline-minio-artifact',
            secret_key_to_env={
                'accesskey': 'AWS_ACCESS_KEY_ID',
                'secretkey': 'AWS_SECRET_ACCESS_KEY'
            }
        )
        # 注入 Region (S3 Client 需要)
        prep_task.set_env_variable('AWS_REGION', 'us-east-1')
        # 注入 Endpoint (指向集群内 MinIO)
        prep_task.set_env_variable('AWS_ENDPOINT_URL', 'http://minio-service.kubeflow.svc:9000')
        # 强制 Path Style (解决 DNS 解析问题)
        prep_task.set_env_variable('S3_FORCE_PATH_STYLE', 'true')
        prep_task.set_env_variable('AWS_S3_FORCE_PATH_STYLE', 'true')
        prep_task.set_env_variable('AWS_USE_PATH_STYLE_REQUESTS', 'true')
        prep_task.set_env_variable('AWS_S3_USE_PATH_STYLE', 'true')

        kubernetes.use_secret_as_env(
            task=train_task,
            secret_name='mlpipeline-minio-artifact',
            secret_key_to_env={
                'accesskey': 'AWS_ACCESS_KEY_ID',
                'secretkey': 'AWS_SECRET_ACCESS_KEY'
            }
        )
        # 注入 Region (S3 Client 需要)
        train_task.set_env_variable('AWS_REGION', 'us-east-1')
        # 注入 Endpoint (指向集群内 MinIO)
        train_task.set_env_variable('AWS_ENDPOINT_URL', 'http://minio-service.kubeflow.svc:9000')
        # 强制 Path Style (解决 DNS 解析问题)
        train_task.set_env_variable('S3_FORCE_PATH_STYLE', 'true')
        train_task.set_env_variable('AWS_S3_FORCE_PATH_STYLE', 'true')
        train_task.set_env_variable('AWS_USE_PATH_STYLE_REQUESTS', 'true')
        train_task.set_env_variable('AWS_S3_USE_PATH_STYLE', 'true')

        kubernetes.add_pod_annotation(
            task=train_task,
            annotation_key='scheduling.k8s.io/group-name', 
            annotation_value='mnist-gpu-group'
        )
        kubernetes.add_pod_annotation(
            task=train_task,
            annotation_key='scheduling.volcano.sh/schedulerName', 
            annotation_value='volcano' 
        )
    # 请求 GPU 资源，Volcano 将基于此进行批量调度
    train_task.set_cpu_limit('4').set_memory_limit('16G').set_gpu_limit(1)


# --- 编译和运行逻辑 ---

# 编译成可执行 JSON
Compiler().compile(
    pipeline_func=mnist_pipeline,
    package_path='mnist_pipeline.yaml'
)
print("Pipeline 编译成功：mnist_pipeline.yaml")

# 提交到 KFP API Server 运行
try:
    # 🌟 替换为你的 KFP API Endpoint 或直接使用 Kubeconfig
    # 提示: 如果在 K8s 集群内部运行，主机名通常是 'http://ml-pipeline.kubeflow.svc.cluster.local:8888'
    KFP_API_HOST = os.environ.get("KFP_HOST", "http://localhost:30088") 
    
    client = Client(host=KFP_API_HOST)
    
    run = client.create_run_from_pipeline_func(
        mnist_pipeline,
        arguments={'epochs': 15, 'lr': 0.0001},
        experiment_name='MNIST Volcano Training Run'
    )
    print(f"\n--- 工作流运行成功！ ---")
    print(f"Run ID: {run.run_id}")
    print(f"请在 KFP UI 中查看运行状态。")

except Exception as e:
    print(f"\n--- 错误：无法连接或提交工作流到 KFP API Server ---")
    print(f"请检查 KFP_API_HOST ({KFP_API_HOST}) 是否正确，以及 KFP 后端是否在运行。")
    print(f"详细错误: {e}")
