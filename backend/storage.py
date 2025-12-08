import json
import os
import uuid
from typing import List, Optional
from models import Component, Pipeline

DATA_DIR = "data"
COMPONENTS_DIR = os.path.join(DATA_DIR, "components")
PIPELINES_DIR = os.path.join(DATA_DIR, "pipelines")

os.makedirs(COMPONENTS_DIR, exist_ok=True)
os.makedirs(PIPELINES_DIR, exist_ok=True)

def save_component(component: Component) -> Component:
    if not component.id:
        component.id = str(uuid.uuid4())
    file_path = os.path.join(COMPONENTS_DIR, f"{component.id}.json")
    with open(file_path, "w") as f:
        f.write(component.json())
    return component

def list_components() -> List[Component]:
    components = []
    if not os.path.exists(COMPONENTS_DIR):
        return []
    for filename in os.listdir(COMPONENTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(COMPONENTS_DIR, filename), "r") as f:
                try:
                    data = json.load(f)
                    components.append(Component(**data))
                except Exception as e:
                    print(f"Error loading component {filename}: {e}")
    return components

def get_component(component_id: str) -> Optional[Component]:
    file_path = os.path.join(COMPONENTS_DIR, f"{component_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            return Component(**data)
    return None

def delete_component(component_id: str) -> bool:
    file_path = os.path.join(COMPONENTS_DIR, f"{component_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def save_pipeline(pipeline: Pipeline) -> Pipeline:
    if not pipeline.id:
        pipeline.id = str(uuid.uuid4())
    file_path = os.path.join(PIPELINES_DIR, f"{pipeline.id}.json")
    with open(file_path, "w") as f:
        f.write(pipeline.json())
    return pipeline

def list_pipelines() -> List[Pipeline]:
    pipelines = []
    if not os.path.exists(PIPELINES_DIR):
        return []
    for filename in os.listdir(PIPELINES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(PIPELINES_DIR, filename), "r") as f:
                try:
                    data = json.load(f)
                    pipelines.append(Pipeline(**data))
                except Exception as e:
                    print(f"Error loading pipeline {filename}: {e}")
    return pipelines

def get_pipeline(pipeline_id: str) -> Optional[Pipeline]:
    file_path = os.path.join(PIPELINES_DIR, f"{pipeline_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            return Pipeline(**data)
    return None

def delete_pipeline(pipeline_id: str) -> bool:
    file_path = os.path.join(PIPELINES_DIR, f"{pipeline_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
