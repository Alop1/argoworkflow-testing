import argparse, os, requests
from hera.workflows import Workflow, Steps, Suspend, Parameter, WorkflowsService, Script

IMAGE = "python:3.9"
DEFAULT_HOST = "http://localhost:2746"


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
        # step1 writes message to file like original YAML
        step1 = Script(
            name="step1",
            image=IMAGE,
            command=["python"],
            source='''print("Hello from step 1!")\nwith open("/tmp/message.txt","w") as f: f.write("Hello from step 1!")''',
            outputs=[Parameter(name="message", value_from={"path": "/tmp/message.txt"})],
        )
        # suspend template
        wait_for_approval = Suspend(
            name="wait-for-approval",
            outputs=[Parameter(name="approved", value_from={"supplied": {}})],
        )
        # set-allow script consumes approved param; writes allow value to file
        set_allow = Script(
            name="set-allow",
            image=IMAGE,
            command=["python"],
            source='''approved = "{{inputs.parameters.approved}}"\nallow = "true" if approved == "true" else "false"\nwith open("/tmp/allow.txt","w") as f: f.write(allow)''',
            inputs=[Parameter(name="approved")],
            outputs=[Parameter(name="allow", value_from={"path": "/tmp/allow.txt"})],
        )
        # step2 consumes message
        step2 = Script(
            name="step2",
            image=IMAGE,
            command=["python"],
            source='''msg = "{{inputs.parameters.message}}"\nprint("Step 2 received message:", msg)''',
            inputs=[Parameter(name="message")],
        )
        # gate steps template replicating original, exposes allow param
        gate = Steps(name="gate")
        with gate:
            wait_for_approval()
            set_allow(arguments={"approved": "{{steps.wait-for-approval.outputs.parameters.approved}}"})
        gate.outputs = [Parameter(name="allow", value_from={"parameter": "{{steps.set-allow.outputs.parameters.allow}}"})]

        # main steps template
        main = Steps(name="main")
        with main:
            step1(name="produce-message")
            gate(name="check-message")
            step2(
                name="consume-message",
                when="{{steps.check-message.outputs.parameters.allow}} == true",
                arguments={"message": "{{steps.produce-message.outputs.parameters.message}}"},
            )
    return wf



def make_service(server: str | None, verify_ssl: bool, no_check: bool) -> WorkflowsService:
    host = server or os.getenv("ARGO_SERVER") or DEFAULT_HOST
    token = os.getenv("ARGO_TOKEN")
    return WorkflowsService(host=host, token=token, verify_ssl=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--print-yaml", action="store_true")
    p.add_argument("--submit", action="store_true")
    p.add_argument("--server", default=os.getenv("ARGO_SERVER", DEFAULT_HOST))
    p.add_argument("--verify-ssl", action="store_true", help="(ignored, HTTP only)")
    p.add_argument("--no-host-check", action="store_true", help="(ignored, HTTP only)")
    args = p.parse_args()

    svc = make_service(args.server, args.verify_ssl, args.no_host_check)
    wf = build_wf(svc)

    if args.print_yaml:
        yaml_body = wf.to_yaml()
        if not yaml_body.startswith("apiVersion:"):
            yaml_body = "apiVersion: argoproj.io/v1alpha1\n" + yaml_body
        print(yaml_body)
        return

    if args.submit:
        try:
            wf.create()
            print(f"Submitted workflow over HTTP. Host used: {svc.host}")
        except Exception as e:
            print("Submission failed (HTTP mode): {}\nEnsure argo-server started with --secure=false and is reachable.".format(e))
    else:
        p.print_help()

if __name__ == "__main__":
    main()
