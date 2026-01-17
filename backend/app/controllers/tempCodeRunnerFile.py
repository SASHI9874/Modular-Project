@router.post("/save-module")
async def save_module(
    name: str = Form(...),
    graph_json: str = Form(...), # Send graph as stringified JSON
    reqs_json: str = Form(...)
):
    import json
    graph = json.loads(graph_json)
    reqs = json.loads(reqs_json)
    
    return generator.save_workflow_as_module(name, graph, reqs)