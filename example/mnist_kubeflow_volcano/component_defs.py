from kfp.v2.dsl import component, Output, Input, Dataset, Artifact
from typing import NamedTuple

# 替换为你的实际仓库地址
REPO = "qiuchen123/kfp-mlops" 

@component(
    base_image=f"{REPO}:mnist-prep-v1",
    output_component_file="mnist_preprocess_component.yaml",
)
def preprocess_data(processed_data: Output[Dataset]):
    # KFP 自动将 output_data_dir 映射到预处理脚本的 --output-data-dir
    pass

@component(
    base_image=f"{REPO}:mnist-train-v1",
    output_component_file="mnist_train_component.yaml",
)
def train_model(
    training_data: Input[Dataset],
    epochs: int,
    lr: float,
    trained_model: Output[Artifact]
) -> NamedTuple('Outputs', [('accuracy', float)]): # 模拟返回 Accuracy
    # KFP 自动处理命令行参数映射
    pass

# 执行生成（直接运行 Python 脚本）
# python component_defs.py 

print("--- KFP 组件 YAML 定义文件编写完成 ---")