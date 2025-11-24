import argparse, os, requests
from hera.workflows import (
    Workflow,
    Steps,
    Suspend,
    Parameter,
    WorkflowsService,
    Script,
    script, RetryStrategy, RetryPolicy,
)
from hera.workflows.models import ValueFrom, TTLStrategy

IMAGE = "python:3.9"
DEFAULT_HOST = "http://localhost:2746"



@script()
def step1() -> str:
    import time
    print("Hello from step 1!")
    # time.sleep(2000)
    time.sleep(1)


@script(retry_strategy=RetryStrategy(limit=3, retry_policy=RetryPolicy.always))
def step2() -> str:
    import time
    print("Hello from step 2!")
    time.sleep(2000)
    time.sleep(1)


@script()
def step3() -> str:
    import time
    print("Hello from step 3!")
    time.sleep(2000)


def build_wf(svc: WorkflowsService):
    # Build workflow and return workflow object directly
    with Workflow(
            generate_name="p2-crach-recovery-wf-",
            entrypoint="main",
            namespace="argo",
            service_account_name="argo-workflow",
            ttl_strategy=TTLStrategy(seconds_after_completion=3600),
            workflows_service=svc,
    ) as wf:
        with Steps(name="main"):
            step1(name="step-1")
            step2(name="step-2")
            step3(name="step-3")
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
# pod "p2-crach-recovery-wf-b9ndf-step3-3530564701" deleted