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

PROCESSING_TIMEOUT = "30s"  # 1) processing_timeout=30s
RETRY_LIMIT = 10             # 3 attempts total


def build_wf(svc: WorkflowsService):
    # Build workflow and return workflow object directly
    with Workflow(
        generate_name="p3-s1-retries-wf-",
        entrypoint="main",
        namespace="argo",
        service_account_name="argo-workflow",
        ttl_strategy={"secondsAfterCompletion": 3600},
        workflows_service=svc,
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

        # step2: this is the step under test (with timeout + retries)
        # In a real test, your code here would run ~45s twice (timing out),
        # then ~25s (succeeds under the 30s timeout).
        step2 = Script(
            name="step2",
            image=IMAGE,
            command=["python"],
            source=(
                'import random, sys, time\n'
                'time.sleep(45)  # simulate long processing that may time out\n'
                'exit_code = random.choice([0, 2])\n'
                'print(f"Simulating failure with exit code {exit_code}")\n'
                'sys.exit(exit_code)'
            ),
            inputs=[Parameter(name="message")],
            timeout='5s',
            retry_strategy=RetryStrategy(
                limit=10,
                # expression='(lastRetry.exitCode != 0) || (lastRetry.duration >= 5)',
                expression= "lastRetry.message matches 'Pod was active on the node longer than the specified deadline'",
                backoff=m.Backoff(
                    duration= "1",  # Must be a string. Default unit is seconds. Could also be a Duration, e.g.: "2m", "6h"
                    factor= "2",
                    max_duration= "1m",  # Must be a string. Default unit is seconds. Could also be a Duration, e.g.: "2m", "6h"

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