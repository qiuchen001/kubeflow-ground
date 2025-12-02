import pandas as pd
import argparse
import os
import random
import json
import numpy as np

# --- KFP 命令行参数 ---
parser = argparse.ArgumentParser(description="Simulated Model Trainer")
# KFP 会将上一步的输出目录映射到这里
parser.add_argument("--input-dir", type=str, required=True, help="Directory path containing the processed data.")
parser.add_argument("--output-model-dir", type=str, required=True, help="Directory path to save the trained model artifact.")
parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs.")
parser.add_argument("--lr", type=float, default=0.01, help="Learning rate.")
args = parser.parse_args()
# --------------------------------------------------

print(f"Starting model training (Volcano Scheduled Task)...")
processed_file = os.path.join(args.input_dir, 'processed_data.csv')
print(f"Reading data from Preprocess task's output: {processed_file}")
print(f"Training parameters: Epochs={args.epochs}, LR={args.lr}")

try:
    # 1. 🌟 读取上一步的输出 (Input Artifacts)
    # 实际中: df = pd.read_csv(processed_file)
    df = pd.read_csv(processed_file) 
    
    # 模拟分布式训练的资源确认
    print(f"Simulating distributed training on 1 GPU...")
    
    # 模拟训练结果
    final_loss = random.uniform(0.1, 0.5)
    final_accuracy = random.uniform(0.90, 0.98) 
    
    print(f"Training finished. Final Loss: {final_loss:.4f}, Accuracy: {final_accuracy:.4f}")

    # 2. 🌟 KFP 产出机制：保存模型和指标
    
    # A. 保存模型状态 (模拟保存一个大型 NumPy 数组作为权重文件)
    os.makedirs(args.output_model_dir, exist_ok=True)
    model_path = os.path.join(args.output_model_dir, 'model_weights.npz')
    np.savez(model_path, weights=np.random.rand(100, 10))
    print(f"Model weights saved to: {model_path}")

    # B. 保存指标 (用于 KFP UI 显示，KFP 可以识别metrics.json)
    metric_path = os.path.join(args.output_model_dir, 'metrics.json')
    metrics = {'loss': final_loss, 'accuracy': final_accuracy}
    with open(metric_path, 'w') as f:
        json.dump(metrics, f)
    print(f"Metrics saved to: {metric_path}")
    
    # 模拟返回 accuracy 作为 KFP output
    with open('/tmp/accuracy_output', 'w') as f:
        f.write(str(final_accuracy))
    
except Exception as e:
    print(f"Error during training: {e}")
    exit(1)