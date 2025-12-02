from kfp.v2.dsl import component, Output, Input, Dataset, Artifact
from typing import NamedTuple

# 替换为你的实际仓库地址
REPO = "qiuchen123/kfp-mlops" 

@component(
    base_image=f"{REPO}:mnist-prep-v1",
    output_component_file="mnist_preprocess_component.yaml",
)
def preprocess_data(processed_data: Output[Dataset]):
    import subprocess
    import sys
    
    # 调用容器内的脚本
    # 注意：KFP 会自动挂载 output artifact 的路径
    cmd = [
        "python", "/app/mnist_preprocess.py",
        "--output-data-dir", processed_data.path
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        sys.exit(result.returncode)

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
    import subprocess
    import sys
    import json
    from collections import namedtuple
    
    # 调用容器内的脚本
    # 注意：training_data.path 指向的是输入 artifact 的路径
    # trained_model.path 指向的是输出 artifact 的路径
    
    cmd = [
        "python", "/app/mnist_train.py",
        "--input-dir", training_data.path,
        "--output-model-dir", trained_model.path,
        "--epochs", str(epochs),
        "--lr", str(lr)
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        sys.exit(result.returncode)
        
    # 读取脚本输出的 accuracy
    # 脚本中写到了 /tmp/accuracy_output
    try:
        with open('/tmp/accuracy_output', 'r') as f:
            accuracy = float(f.read().strip())
    except Exception as e:
        print(f"Failed to read accuracy: {e}")
        accuracy = 0.0
        
    outputs = namedtuple('Outputs', ['accuracy'])
    return outputs(accuracy)

# 执行生成（直接运行 Python 脚本）
# python component_defs.py 

print("--- KFP 组件 YAML 定义文件编写完成 ---")