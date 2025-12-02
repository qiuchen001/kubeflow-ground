import pandas as pd
import argparse
import os
import json # 用于模拟保存元数据

parser = argparse.ArgumentParser(description="MNIST Data Preprocessor")
# KFP 会提供这个目录路径
parser.add_argument("--output-data-dir", type=str, required=True, help="Directory path to save the processed data.") 
args = parser.parse_args()

print("Starting MNIST data preprocessing and saving to Artifact Store...")

try:
    # --- 模拟数据下载和处理 ---
    # 实际中应该是下载并处理 MNIST 数据
    
    # 模拟创建处理后的数据 (包含 features 和 labels)
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