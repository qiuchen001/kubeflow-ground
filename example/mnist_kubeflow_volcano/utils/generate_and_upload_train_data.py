import argparse
import os
import sys
import tempfile
import subprocess
import csv

def generate_csv(path: str, rows: int):
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pixel_sum", "label", "is_normalized"]) 
        for i in range(rows):
            writer.writerow([int(2000 + i % 600), i % 10, True])

def upload_minio(local_path: str, endpoint: str, bucket: str, object_key: str, access_key: str, secret_key: str):
    try:
        from minio import Minio
    except Exception:
        print("minio SDK 未安装，改用 --method kubectl 或先安装: pip install minio")
        sys.exit(3)
    secure = endpoint.startswith("https://")
    host = endpoint.replace("http://", "").replace("https://", "")
    client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    with open(local_path, "rb") as f:
        stat = os.stat(local_path)
        client.put_object(bucket, object_key, f, stat.st_size, content_type="text/csv")

def ensure_dir_in_pod(namespace: str, pod: str, dest_path: str):
    dir_path = os.path.dirname(dest_path).replace("\\", "/")
    subprocess.run(["kubectl", "-n", namespace, "exec", pod, "--", "sh", "-lc", f"mkdir -p '{dir_path}'"], check=True)

def upload_kubectl(local_path: str, namespace: str, pod: str, dest_path: str):
    ensure_dir_in_pod(namespace, pod, dest_path)
    subprocess.run(["kubectl", "-n", namespace, "cp", local_path, f"{pod}:{dest_path}"], check=True)

def discover_minio_pod(namespace: str) -> str:
    try:
        name = subprocess.check_output(["kubectl", "-n", namespace, "get", "pods", "-l", "app=minio", "-o", "jsonpath={.items[0].metadata.name}"]).decode().strip()
        if name:
            return name
    except Exception:
        pass
    raise RuntimeError("failed to discover minio pod")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--bucket", type=str, default="kubeflow-pipeline")
    parser.add_argument("--object", type=str, default="raw/train_data.csv")
    parser.add_argument("--method", choices=["minio", "kubectl"], default="minio")
    parser.add_argument("--endpoint", type=str, default="http://localhost:30099")
    parser.add_argument("--access-key", type=str, default=os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("MINIO_ROOT_USER") or "minio")
    parser.add_argument("--secret-key", type=str, default=os.environ.get("MINIO_SECRET_KEY") or os.environ.get("MINIO_ROOT_PASSWORD") or "minio123")
    parser.add_argument("--namespace", type=str, default="kubeflow")
    parser.add_argument("--pod", type=str, default="")
    args = parser.parse_args()

    tmpdir = tempfile.mkdtemp()
    local_path = os.path.join(tmpdir, "train_data.csv")
    generate_csv(local_path, args.rows)

    if args.method == "minio":
        if not args.access_key or not args.secret_key:
            print("missing minio credentials")
            sys.exit(2)
        upload_minio(local_path, args.endpoint, args.bucket, args.object, args.access_key, args.secret_key)
        print(f"uploaded: {args.endpoint}/{args.bucket}/{args.object}")
        return

    pod = args.pod or discover_minio_pod(args.namespace)
    dest_path = f"/data/{args.bucket}/{args.object}".replace("\\", "/")
    upload_kubectl(local_path, args.namespace, pod, dest_path)
    print(f"copied: {local_path} -> {pod}:{dest_path}")

if __name__ == "__main__":
    main()
