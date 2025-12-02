from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class ComponentInput(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class ComponentOutput(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class ComponentResources(BaseModel):
    cpu_request: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_request: Optional[str] = None
    memory_limit: Optional[str] = None
    gpu_type: Optional[str] = None
    gpu_limit: Optional[str] = None

class Component(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    image: str
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    inputs: List[ComponentInput] = []
    outputs: List[ComponentOutput] = []
    resources: ComponentResources = ComponentResources()
    volcano_enabled: bool = False

class PipelineNode(BaseModel):
    id: str
    component_id: str
    label: str
    position: Dict[str, float] # {x: 0, y: 0}
    args: Optional[Dict[str, str]] = {}
    resources: Optional[Dict[str, str]] = {}

class PipelineEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None # output name
    targetHandle: Optional[str] = None # input name

class Pipeline(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    nodes: List[PipelineNode] = []
    edges: List[PipelineEdge] = []
