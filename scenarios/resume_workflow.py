#!/usr/bin/env python3
# pip install "hera-workflows>=5"
import argparse
from hera.workflows import WorkflowsService
from hera.workflows.models import (
    WorkflowResumeRequest,
    WorkflowSetRequest,
)

def main():
    parser = argparse.ArgumentParser(
        description="Resume a specific suspended Argo workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python resume_workflow.py --server http://localhost:2746 --workflow my-wf --approved true
        """
    )

    parser.add_argument(
        "--server",
        required=False,
        default="http://localhost:2746",
        help="Argo server URL (e.g., http://localhost:2746)"
    )
    parser.add_argument(
        "--namespace",
        default="argo",
        help="Kubernetes namespace (default: argo)"
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Name of the workflow to unsuspend"
    )
    parser.add_argument(
        "--approved",
        required=True,
        choices=["true", "false"],
        help="Approval decision to pass to the workflow"
    )

    args = parser.parse_args()

    ws = WorkflowsService(
        host=args.server,
        namespace=args.namespace,
        verify_ssl=False,
        token=None,
    )

    # Fetch only the selected workflow
    try:
        wf = ws.get_workflow(namespace=args.namespace, name=args.workflow)
    except Exception:
        print(f"Error: Workflow '{args.workflow}' not found.")
        exit(1)

    # Find suspended node in the workflow
    node_display_name = None

    if wf.status and wf.status.nodes:
        for node in wf.status.nodes.values():
            if node.type == "Suspend" and node.phase == "Running":
                node_display_name = node.display_name or node.name
                break

    if node_display_name is None:
        print(f"Workflow '{args.workflow}' is not currently suspended.")
        exit(0)

    print(f"✓ Workflow: {args.workflow}")
    print(f"✓ Suspended node: {node_display_name}")
    print(f"✓ Approved: {args.approved}")

    # JSON string payload
    output_params = f'{{"approved":"{args.approved}"}}'

    # Set output parameters
    set_req = WorkflowSetRequest(
        node_field_selector=f"displayName={node_display_name}",
        output_parameters=output_params,
    )
    ws.set_workflow(namespace=args.namespace, name=args.workflow, req=set_req)
    print("✓ Output parameter set")

    # Resume workflow
    ws.resume_workflow(
        namespace=args.namespace,
        name=args.workflow,
        req=WorkflowResumeRequest()
    )
    print("✓ Workflow resumed")


if __name__ == "__main__":
    main()