import os
from kfp import Client
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

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

def get_run_node_statuses(run_id: str) -> dict:
    client = Client(host=KFP_ENDPOINT)
    try:
        run = client.get_run(run_id)
        # v1 (Argo) path: parse workflow_manifest
        try:
            pr = getattr(run, 'pipeline_runtime', None)
            wf = getattr(pr, 'workflow_manifest', None)
            if wf:
                import json
                wfj = json.loads(wf)
                nodes = (wfj.get('status') or {}).get('nodes') or {}
                result = {}
                for _, nd in nodes.items():
                    name = nd.get('displayName') or nd.get('name')
                    phase = nd.get('phase') or nd.get('status')
                    if name and phase:
                        result[name] = phase
                if result:
                    return result
        except Exception:
            pass
        # Fallback: search dict/json for task-like entries
        def to_mapping(obj):
            try:
                if hasattr(obj, 'to_dict'):
                    return obj.to_dict()
            except Exception:
                pass
            try:
                if hasattr(obj, 'to_json'):
                    import json
                    return json.loads(obj.to_json())
            except Exception:
                pass
            return None
        d = to_mapping(run) or {}
        # Heuristic: look for arrays/maps containing displayName/name and state/status/phase
        result = {}
        def walk(x):
            if isinstance(x, dict):
                keys = x.keys()
                name = x.get('displayName') or x.get('name') or x.get('taskName')
                st = x.get('state') or x.get('status') or x.get('phase')
                if name and st:
                    result[name] = st
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(d)
        if result:
            return result
        # v2 SDK: parse run_details if present
        try:
            rd = getattr(run, 'run_details', None)
            dd = None

            print(rd)

            if rd is not None:
                if isinstance(rd, dict):
                    dd = rd
                elif hasattr(rd, 'to_dict'):
                    dd = rd.to_dict()
                elif hasattr(rd, 'to_json'):
                    dd = json.loads(rd.to_json())
            print("dd:", dd)
            if dd:
                items = dd.get('task_runs') or dd.get('tasks') or dd.get('nodes') or dd.get('task_details') or []
                out = {}
                for it in items if isinstance(items, list) else []:
                    name = it.get('display_name') or it.get('task_name') or it.get('name')
                    st = it.get('state') or it.get('status') or it.get('phase')
                    if name and st:
                        out[name] = st
                if out:
                    return out
        except Exception:
            pass
        # v2 REST fallback: query task runs
        def try_v2_task_runs(path):
            try:
                qs = urlencode({'run_id': run_id})
                url = f"{KFP_ENDPOINT}{path}?{qs}"
                req = Request(url)
                with urlopen(req) as resp:
                    body = resp.read().decode('utf-8')
                    data = json.loads(body)
                    items = data.get('task_runs') or data.get('tasks') or []
                    out = {}
                    for it in items:
                        name = it.get('display_name') or it.get('task_name') or it.get('name')
                        st = it.get('state') or it.get('status') or it.get('phase')
                        if name and st:
                            out[name] = st
                    return out
            except Exception:
                return {}
        rest_paths = [
            '/pipeline/apis/v2beta1/task_runs',
            '/pipeline/apis/v2beta1/tasks',
        ]
        for p in rest_paths:
            out = try_v2_task_runs(p)
            if out:
                return out
        return {}
    except Exception as e:
        print(f"Failed to get run node statuses: {e}")
        raise e
