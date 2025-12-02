import kfp
import os

KFP_ENDPOINT = os.getenv("KFP_ENDPOINT", "http://localhost:30088")

def submit_pipeline(pipeline_file_path: str, run_name: str):
    client = kfp.Client(host=KFP_ENDPOINT)
    # Create experiment if not exists? Or just default.
    # client.create_run_from_pipeline_package(pipeline_file_path, arguments={})
    # Using run_pipeline for V2 usually, or create_run_from_pipeline_package for V1/V2.
    
    try:
        run_result = client.create_run_from_pipeline_package(
            pipeline_file=pipeline_file_path,
            arguments={},
            run_name=run_name,
            experiment_name="Default"
        )
        return run_result
    except Exception as e:
        print(f"Failed to submit pipeline: {e}")
        raise e
