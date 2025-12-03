import pandas as pd
import argparse
import os
import json # 用于模拟保存元数据

parser = argparse.ArgumentParser(description="MNIST Data Preprocessor")
# 可选的原始数据输入目录（Artifact 输入）
parser.add_argument("--input-dir", type=str, required=False, help="Directory path containing raw data.")
# KFP 会提供这个目录路径
parser.add_argument("--output-data-dir", type=str, required=True, help="Directory path to save the processed data.") 
args = parser.parse_args()

print("Starting MNIST data preprocessing and saving to Artifact Store...")

try:
    # 若提供了输入目录，尝试从其中读取原始CSV
    df = None
    if args.input_dir and os.path.isdir(args.input_dir):
        candidates = [f for f in os.listdir(args.input_dir) if f.lower().endswith('.csv')]
        if candidates:
            src = os.path.join(args.input_dir, candidates[0])
            df = pd.read_csv(src)
    # 如果没有提供输入或读取失败，则生成模拟数据
    if df is None:
        df = pd.DataFrame({
            'pixel_sum': [2550, 2400, 2600],
            'label': [1, 7, 3],
            'is_normalized': [True, True, True]
        })
    
    # 4. KFP 产出机制：将结果保存到指定的输出目录
    os.makedirs(args.output_data_dir, exist_ok=True)
    
    # 保存处理后的数据集 (CSV 文件作为 Artifact)
    output_path = os.path.join(args.output_data_dir, 'processed_data.csv')
    df.to_csv(output_path, index=False)
    
    # 模拟保存一些元数据文件，KFP 也会将其视为 Artifact
    with open(os.path.join(args.output_data_dir, 'metadata.json'), 'w') as f:
        json.dump({"rows": len(df), "columns": len(df.columns)}, f)

    print(f"Data processing complete. Saved {len(df)} rows to: {output_path}")

except Exception as e:
    print(f"Error during preprocessing: {e}")
    exit(1)
