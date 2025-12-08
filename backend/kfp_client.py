import os
from kfp import Client

KFP_ENDPOINT = os.getenv("KFP_ENDPOINT", "http://localhost:30088")
PIPELINE_ROOT = os.getenv("PIPELINE_ROOT", os.getenv("KFP_PIPELINE_ROOT", "s3://mlpipeline/test-pipeline-root"))

def submit_pipeline(pipeline_file_path: str, run_name: str):
    client = Client(host=KFP_ENDPOINT)
    try:
        run_result = client.create_run_from_pipeline_package(
            pipeline_file=pipeline_file_path,
            arguments={},
            run_name=run_name,
            experiment_name="Default",
            pipeline_root=PIPELINE_ROOT,
        )
        return run_result
    except Exception as e:
        print(f"Failed to submit pipeline: {e}")
        raise e
