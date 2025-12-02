import os
from kfp import dsl
from kfp import kubernetes

from kfp.compiler import Compiler
from kfp.client import Client
from kfp.components import load_component_from_file

# --- 辅助函数：加载组件 YAML ---
def get_component_op(yaml_file):
    # 假设 YAML 文件在与此脚本同级的目录
    return load_component_from_file(os.path.join(os.path.dirname(__file__), "..", yaml_file))

# 加载组件 (确保组件 YAML 已经生成)
try:
    preprocess_op = load_component_from_file('./mnist_preprocess_component.yaml')
    train_op = load_component_from_file('./mnist_train_component.yaml')
except FileNotFoundError:
    print("错误: 找不到组件 YAML 文件。请先运行组件生成步骤。")
    exit(1)


# --- Pipeline 定义：DAG 结构和 Volcano 注入 ---
@dsl.pipeline(
    name='mnist-volcano-training',
    # 🌟 替换为你的实际 Artifact Store (e.g., gs://my-bucket/runs 或 s3://my-bucket/runs)
    pipeline_root='s3://your-kfp-artifact-store/mnist-runs' 
)
def mnist_pipeline(
    epochs: int = 10, 
    lr: float = 0.001
):
    # 1. 数据预处理任务 (使用默认 K8s 调度器)
    prep_task = preprocess_op()
    
    # 2. 模型训练任务 (配置 Volcano 调度)
    train_task = train_op(
        # 串行依赖：数据传递 (KFP 自动处理路径映射)
        training_data=prep_task.outputs['processed_data'], 
        epochs=epochs,
        lr=lr
    )
    
    # --- 🌟 关键：Volcano 调度注入点 ---
    # 这将确保这个训练任务的 Pod 由 Volcano 调度器处理
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