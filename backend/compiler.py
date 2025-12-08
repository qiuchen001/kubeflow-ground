from kfp import dsl
from kfp import compiler
from kfp.components import load_component_from_text
import tempfile
import os
from typing import Dict
from models import Pipeline, Component
import storage

def compile_pipeline(pipeline: Pipeline) -> str:
    """
    Compiles a Pipeline model into a KFP YAML file.
    Returns the path to the compiled YAML file.
    """
    
    # 1. Load all referenced components
    component_map: Dict[str, Component] = {}
    for node in pipeline.nodes:
        comp = storage.get_component(node.component_id)
        if not comp:
            raise ValueError(f"Component {node.component_id} not found for node {node.id}")
        component_map[node.component_id] = comp

    # 2. Define the pipeline function dynamically
    def _sanitize(name: str) -> str:
        s = ''.join(ch if (ch.isalnum() or ch == '_') else '_' for ch in name)
        if s and s[0].isdigit():
            s = '_' + s
        return s

    def _build_component_yaml(comp: Component, artifact_inputs: set):
        in_map = {i.name: _sanitize(i.name) for i in comp.inputs}
        out_map = {o.name: _sanitize(o.name) for o in comp.outputs}
        lines = []
        lines.append(f"name: {comp.name}")
        if comp.inputs:
            lines.append("inputs:")
            for inp in comp.inputs:
                lines.append(f"  - name: {in_map[inp.name]}")
                lines.append(f"    type: {'Dataset' if inp.name in artifact_inputs else 'string'}")
        if comp.outputs:
            lines.append("outputs:")
            for out in comp.outputs:
                lines.append(f"  - name: {out_map[out.name]}")
                lines.append(f"    type: Dataset")
        lines.append("implementation:")
        lines.append("  container:")
        lines.append(f"    image: {comp.image}")
        if comp.command:
            lines.append("    command:")
            for c in comp.command:
                lines.append(f"    - {c}")
        if comp.args:
            lines.append("    args:")
            # Map args: parameters and outputs
            output_names = {o.name for o in comp.outputs}
            for a in comp.args:
                replaced = False
                # parameter placeholder {{inputs.parameters.<name>}}
                if a.startswith("{{") and "inputs.parameters." in a:
                    name = a.split("inputs.parameters.", 1)[1].split("}}", 1)[0]
                    san = in_map.get(name, _sanitize(name))
                    if name in artifact_inputs:
                        lines.append(f"    - {{inputPath: {san}}}")
                    else:
                        lines.append(f"    - {{inputValue: {san}}}")
                    replaced = True
                else:
                    # output path mapping for tokens containing /tmp/outputs/<out>
                    for out in output_names:
                        token = f"/tmp/outputs/{out}"
                        if a == token:
                            san_out = out_map.get(out, _sanitize(out))
                            lines.append(f"    - {{outputPath: {san_out}}}")
                            replaced = True
                            break
                if not replaced:
                    sa = str(a)
                    sa = sa.replace('\\', '\\\\').replace('"', '\\"')
                    lines.append(f"    - \"{sa}\"")
        return "\n".join(lines), in_map, out_map

    @dsl.pipeline(
        name=pipeline.name,
        description=pipeline.description
    )
    def dynamic_pipeline():
        tasks = {}
        
        # Build adjacency list for topological sort
        adj_list = {node.id: [] for node in pipeline.nodes}
        in_degree = {node.id: 0 for node in pipeline.nodes}
        
        for edge in pipeline.edges:
            if edge.source in adj_list and edge.target in in_degree:
                adj_list[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Kahn's algorithm for topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []
        
        while queue:
            u = queue.pop(0)
            sorted_nodes.append(u)
            
            for v in adj_list[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        # Check for cycles
        if len(sorted_nodes) != len(pipeline.nodes):
            raise ValueError("Pipeline contains a cycle")
            
        # Create tasks in topological order
        for node_id in sorted_nodes:
            # Find the node object
            node = next(n for n in pipeline.nodes if n.id == node_id)
            comp = component_map[node.component_id]
            incoming_edges = [e for e in pipeline.edges if e.target == node.id and e.targetHandle]
            artifact_inputs = set(e.targetHandle for e in incoming_edges if e.targetHandle)
            spec_text, in_map, out_map = _build_component_yaml(comp, artifact_inputs)
            comp_func = load_component_from_text(spec_text)
            # Build kwargs for component call
            kwargs = {}
            # Edge-based inputs
            for edge in incoming_edges:
                source_task = tasks.get(edge.source)
                if source_task and edge.sourceHandle:
                    target_key = in_map.get(edge.targetHandle, _sanitize(edge.targetHandle))
                    src_out_key = _sanitize(edge.sourceHandle)
                    kwargs[target_key] = source_task.outputs[src_out_key]
            # Constant inputs from node.args
            if node.args:
                for arg_name, arg_value in node.args.items():
                    key = in_map.get(arg_name, _sanitize(arg_name))
                    if key not in kwargs:
                        kwargs[key] = arg_value
            task = comp_func(**kwargs)

            
            # Set resources (Component defaults)
            cpu_request = comp.resources.cpu_request
            cpu_limit = comp.resources.cpu_limit
            memory_request = comp.resources.memory_request
            memory_limit = comp.resources.memory_limit
            gpu_limit = comp.resources.gpu_limit

            # Override with Node specific resources
            if node.resources:
                if node.resources.get("cpu_request"): cpu_request = node.resources["cpu_request"]
                if node.resources.get("cpu_limit"): cpu_limit = node.resources["cpu_limit"]
                if node.resources.get("memory_request"): memory_request = node.resources["memory_request"]
                if node.resources.get("memory_limit"): memory_limit = node.resources["memory_limit"]
                # GPU override not implemented in UI yet, but logic would be similar

            try:
                if cpu_request: task.set_cpu_request(cpu_request)
                if cpu_limit: task.set_cpu_limit(cpu_limit)
                if memory_request: task.set_memory_request(memory_request)
                if memory_limit: task.set_memory_limit(memory_limit)
                if gpu_limit: task.set_gpu_limit(gpu_limit)
            except Exception:
                pass
            
            # Volcano annotations
            try:
                if comp.volcano_enabled:
                    task.add_pod_annotation("scheduling.k8s.io/group-name", f"pipeline-{pipeline.id}")
                    task.add_pod_annotation("schedulerName", "volcano")
            except Exception:
                pass
            
            tasks[node.id] = task
            
            # Establish execution dependencies for edges without handles (pure ordering)
            # We only need to do this for edges that were NOT used for data passing?
            # Or just do it for all edges to be safe?
            # If we passed data, dependency is implicit. But explicit .after() doesn't hurt.
            incoming_edges_all = [e for e in pipeline.edges if e.target == node.id]
            for edge in incoming_edges_all:
                source_task = tasks.get(edge.source)
                if source_task:
                    task.after(source_task)

    # 3. Compile
    output_file = os.path.join(tempfile.gettempdir(), f"{pipeline.id}.yaml")
    compiler.Compiler().compile(dynamic_pipeline, output_file)
    return output_file
