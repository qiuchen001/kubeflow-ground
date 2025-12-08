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

def get_run_status(run_id: str) -> str:
    client = Client(host=KFP_ENDPOINT)
    try:
        run = client.get_run(run_id)
        # Try common attributes across KFP v1/v2
        for obj in (run, getattr(run, 'run', None)):
            if obj is None:
                continue
            for attr in ('state', 'status', 'phase'):
                try:
                    val = getattr(obj, attr)
                    if isinstance(val, str) and val:
                        return val
                except Exception:
                    pass
        # Try dict/json conversions if available
        try:
            if hasattr(run, 'to_dict'):
                d = run.to_dict()
                status = d.get('state') or d.get('status') or (d.get('run') or {}).get('state') or (d.get('run') or {}).get('status')
                if status:
                    return status
        except Exception:
            pass
        try:
            if hasattr(run, 'to_json'):
                import json
                jd = json.loads(run.to_json())
                status = jd.get('state') or jd.get('status') or (jd.get('run') or {}).get('state') or (jd.get('run') or {}).get('status')
                if status:
                    return status
        except Exception:
            pass
        return "unknown"
    except Exception as e:
        print(f"Failed to get run status: {e}")
        raise e
