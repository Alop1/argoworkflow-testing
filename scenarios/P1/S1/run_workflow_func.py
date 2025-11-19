import argparse, os, requests
from hera.workflows import (
    Workflow,
    Steps,
    Suspend,
    Parameter,
    WorkflowsService,
    Script,
    script,
)
from hera.workflows.models import ValueFrom

IMAGE = "python:3.9"
DEFAULT_HOST = "http://localhost:2746"



@script()
def step1() -> str:
    print("Hello from step 1!")


@script()
def step2_approved(message: str):
    print("Step 2 (APPROVED) received message:", message)


@script()
def step2_rejected(message: str):
    print("Step 2 (REJECTED) received message:", message)


@script(outputs=[ Parameter(name="allow", value_from=ValueFrom(path="/tmp/allow.txt")),])
def set_allow(approved: str):
    allow = "true" if approved == "true" else "false"
    print(f"set-allow: approved={approved} -> allow={allow}")
    with open("/tmp/allow.txt", "w") as f: f.write(allow)


def build_wf(svc: WorkflowsService):
    # Build workflow and return workflow object directly
    with Workflow(
            generate_name="p1-long-running-wf-",
            entrypoint="main",
            namespace="argo",
            service_account_name="argo-workflow",
            ttl_strategy={"secondsAfterCompletion": 3600},
            workflows_service=svc,
    ) as wf:
        # Suspend template – zostaje w klasycznym stylu
        wait_for_approval = Suspend(
            name="wait-for-approval",
            outputs=[Parameter(name="approved", value_from={"supplied": {}})],
        )


        with Steps(name="main"):
            hello_step = step1(name="produce-message")
            step_wait_for_approval = wait_for_approval()
            step_set_allow = set_allow(name="set-allow",
                                       arguments={"approved": step_wait_for_approval.get_parameter("approved").value})


            step2_approved(
                name="consume-message-approved",
                when=f"{step_set_allow.get_parameter('allow')} == true",
                arguments={
                    "message": hello_step.result,
                },
            )

            step2_rejected(
                name="consume-message-rejected",
                when=f"{step_set_allow.get_parameter('allow')} == false",
                arguments={
                    "message": hello_step.result,
                },
            )

    return wf


def make_service(server: str | None) -> WorkflowsService:
    host = server or os.getenv("ARGO_SERVER") or DEFAULT_HOST
    return WorkflowsService(host=host, token=None, verify_ssl=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--print-yaml", action="store_true")
    p.add_argument("--submit", action="store_true")
    p.add_argument("--server", default=os.getenv("ARGO_SERVER", DEFAULT_HOST))
    args = p.parse_args()

    svc = make_service(args.server)
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
            print(
                f"Submitted workflow over HTTP. Host used: {svc.host}\n\n"
                f"{wf.name}"
            )
        except Exception as e:
            print(
                "Submission failed (HTTP mode): {}\n"
                "Ensure argo-server started with --secure=false and is reachable.".format(
                    e
                )
            )
    else:
        p.print_help()


if __name__ == "__main__":
    main()
