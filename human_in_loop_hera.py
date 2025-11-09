#!/usr/bin/env python3
from hera.workflows import Workflow, Steps, Suspend, Parameter, WorkflowsService, script

IMAGE = "python:3.9"

@script(name="step1", image=IMAGE)
def step1():
    # Returning a value becomes the `result` parameter
    return "Hello from step 1!"

@script(name="set-allow", image=IMAGE, inputs=[Parameter(name="approved")])
def set_allow(approved: str):
    return "true" if approved == "true" else "false"

@script(name="step2", image=IMAGE, inputs=[Parameter(name="message")])
def step2(message: str):
    print("Step 2 received message:", message)


def build_wf(svc: WorkflowsService):
    # Build workflow and return workflow object directly
    with Workflow(
        generate_name="conditional-step-",
        entrypoint="main",
        namespace="argo",
        service_account_name="argo-workflow",
        ttl_strategy={"secondsAfterCompletion": 3600},
        workflows_service=svc,
    ) as wf:
        # Gate steps
        with Steps(name="gate") as gate:
            Suspend(name="wait-for-approval", outputs=[Parameter(name="approved", value_from={"supplied": {}})])()
            set_allow(approved="{{steps.wait-for-approval.outputs.parameters.approved}}")
        # Expose allow parameter from set-allow result
        gate.outputs = [Parameter(name="allow", value_from={"parameter": "{{steps.set-allow.outputs.result}}"})]

        # Main steps sequence
        with Steps(name="main"):
            step1(name="produce-message")
            gate(name="check-message")
            step2(
                name="consume-message",
                when="{{steps.check-message.outputs.parameters.allow}} == true",
                message="{{steps.produce-message.outputs.result}}",
            )
    return wf

if __name__ == "__main__":
    import argparse, os
    p = argparse.ArgumentParser()
    p.add_argument("--print-yaml", action="store_true")
    p.add_argument("--submit", action="store_true")
    p.add_argument("--server", default=os.getenv("ARGO_SERVER", "http://localhost:2746"))
    p.add_argument("--verify-ssl", action="store_true")
    args = p.parse_args()

    svc = WorkflowsService(host=args.server, verify_ssl=args.verify_ssl, token=os.getenv("ARGO_TOKEN"))
    wf = build_wf(svc)

    if args.print_yaml:
        print(wf.to_yaml())
    elif args.submit:
        wf.create()
        print("Submitted:", wf.name or wf.generate_name)
    else:
        p.print_help()
