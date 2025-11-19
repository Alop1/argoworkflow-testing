import argparse, os, requests
from hera.workflows import (
    Workflow,
    Steps,
    Parameter,
    WorkflowsService,
    Script,
    RetryStrategy,
)
from hera.workflows import models as m  # for Backoff

IMAGE = "python:3.9"
DEFAULT_HOST = "http://localhost:2746"



def build_wf(svc: WorkflowsService):
    # Build workflow and return workflow object directly
    with Workflow(
        generate_name="p3-s5-exhaust-retry-",
        entrypoint="main",
        namespace="argo",
        service_account_name="argo-workflow",
        ttl_strategy={"secondsAfterCompletion": 3600},
        workflows_service=svc,
        # Instant shutdown (no graceful period) for all pods:
        pod_spec_patch='{"terminationGracePeriodSeconds":0}'
    ) as wf:
        # step1 writes message to file
        step1 = Script(
            name="step1",
            image=IMAGE,
            command=["python"],
            source=(
                'print("Hello from step 1!")\n'
                'with open("/tmp/message.txt","w") as f: f.write("Hello from step 1!")'
            ),
            outputs=[Parameter(name="message", value_from={"path": "/tmp/message.txt"})],
        )

        step2 = Script(
            name="step2",
            image=IMAGE,
            command=["python"],
            # Deterministic retries: attempts 1-2 sleep 45s (timeout), attempt 3 sleeps 25s (success).
            source=(
                'import sys, time\n'
                'time.sleep(45)\n'
                'print("Finished attempt", attempt)\n'
            ),
            inputs=[Parameter(name="message")],
            timeout='30s',
            retry_strategy=RetryStrategy(
                limit=4,
                expression= "lastRetry.message matches 'Pod was active on the node longer than the specified deadline'",
                # expression='(lastRetry.exitCode != 0) || (lastRetry.duration >= 5)',
                backoff=m.Backoff(
                    duration= "1s",
                    factor= "2",

                ),
            ),
        )

        # main steps template
        main = Steps(name="main")
        with main:
            step1(name="produce-message")
            step2(
                name="consume-message",
                arguments={"message": "{{steps.produce-message.outputs.parameters.message}}"},
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
            print("Submission failed (HTTP mode): {}\n".format(e))
    else:
        p.print_help()


if __name__ == "__main__":
    main()