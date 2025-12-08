from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import models
import storage
import compiler
import kfp_client
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Components
@app.post("/components", response_model=models.Component)
def create_component(component: models.Component):
    return storage.save_component(component)

@app.get("/components", response_model=List[models.Component])
def get_components():
    return storage.list_components()

@app.get("/components/{component_id}", response_model=models.Component)
def get_component(component_id: str):
    comp = storage.get_component(component_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
    return comp

@app.delete("/components/{component_id}")
def delete_component(component_id: str):
    success = storage.delete_component(component_id)
    if not success:
        raise HTTPException(status_code=404, detail="Component not found")
    return {"status": "deleted"}

# Pipelines
@app.post("/pipelines", response_model=models.Pipeline)
def create_pipeline(pipeline: models.Pipeline):
    return storage.save_pipeline(pipeline)

@app.get("/pipelines", response_model=List[models.Pipeline])
def get_pipelines():
    return storage.list_pipelines()

@app.get("/pipelines/{pipeline_id}", response_model=models.Pipeline)
def get_pipeline(pipeline_id: str):
    pipe = storage.get_pipeline(pipeline_id)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipe

@app.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: str):
    pipe = storage.get_pipeline(pipeline_id)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    try:
        # Compile
        yaml_file = compiler.compile_pipeline(pipe)
        
        # Submit
        run_name = f"Run {pipe.name}"
        result = kfp_client.submit_pipeline(yaml_file, run_name)
        # Robust run_id extraction across KFP versions
        run_id = getattr(result, 'run_id', None)
        if not run_id:
            try:
                run_obj = getattr(result, 'run', None)
                run_id = getattr(run_obj, 'id', None) or getattr(result, 'id', None)
            except Exception:
                run_id = None
        pipe.last_run_id = run_id
        storage.save_pipeline(pipe)
        return {"status": "submitted", "run_id": run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/{pipeline_id}/status")
def get_pipeline_status(pipeline_id: str):
    pipe = storage.get_pipeline(pipeline_id)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    if not pipe.last_run_id:
        return {"status": "unknown"}
    try:
        status = kfp_client.get_run_status(pipe.last_run_id)
        return {"run_id": pipe.last_run_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
