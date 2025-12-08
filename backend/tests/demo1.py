from kfp import Client
import os


KFP_ENDPOINT = os.getenv("KFP_ENDPOINT", "http://localhost:30088")
client = Client(host=KFP_ENDPOINT)

run_id = '905814f3-a244-474b-94c8-8f4f90375676'
run = client.get_run(run_id)

print(run)
import json

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
            print("out:", out)
except Exception:
    pass

statuses = out
mapped = {}
for name, st in statuses.items():
    if isinstance(name, str) and '-' in name:
        nid = name.split('-', 1)[0]
        mapped[nid] = st

print("mapped:", mapped)