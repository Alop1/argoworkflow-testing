# pip install "hera-workflows>=5"
from hera.workflows import WorkflowsService
from hera.workflows.models import (
    WorkflowResumeRequest,
    WorkflowSetRequest,
)


ws = WorkflowsService(
    host="http://localhost:2746",
    namespace="argo",
    verify_ssl=False,
    token=None,
)


# List all workflows and find first suspended one
wl = ws.list_workflows(namespace="argo")
print("Workflows:")
print("-" * 60)

workflow_name = None
node_display_name = None

for w in wl.items:
    name = w.metadata.name
    phase = (w.status.phase if w.status else "Unknown")
    print(f"{name:40s} {phase}")

    # Find first suspended workflow if not already found
    if workflow_name is None and phase == "Running" and w.status and w.status.nodes:
        for node_id, node in w.status.nodes.items():
            if node.type == "Suspend" and node.phase == "Running":
                workflow_name = name
                node_display_name = node.display_name or node.name
                print(f"  → Found suspended node: {node_display_name}")
                break

print("-" * 60)

if workflow_name is None:
    print("\n No suspended workflows found.")
    exit(0)

print(f"\n✓ Resuming workflow: {workflow_name}")
print(f"  Node: {node_display_name}")

set_req = WorkflowSetRequest(
    node_field_selector=f"displayName={node_display_name}",
    output_parameters='{"approved":"true"}',   # << JSON string
    # message="Approved via Hera",
)
ws.set_workflow(namespace="argo", name=workflow_name, req=set_req)
print(f"  ✓ Set approved=true")

ws.resume_workflow(
    namespace="argo",
    name=workflow_name,
    req=WorkflowResumeRequest()
)
print(f"  ✓ Workflow resumed")

#   alternative resume with node selector in resume call
# ws.resume_workflow(
#     namespace="argo",
#     name=workflow_name,
#     req=WorkflowResumeRequest(node_field_selector=f"displayName={node_display_name}")
# )
