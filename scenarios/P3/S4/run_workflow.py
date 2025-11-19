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
    with Workflow(
        generate_name="p3-s4-different-retries-and-failed-wf-",
        entrypoint="main",
        namespace="argo",
        service_account_name="argo-workflow",
        ttl_strategy={"secondsAfterCompletion": 3600},
        workflows_service=svc,
        pod_spec_patch='{"terminationGracePeriodSeconds":0}',
    ) as wf:

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
            # TODO clean belo script to make it more readable
            source=(
                "import sys, time, pathlib\n"
                'attempt = int(\"{{retries}}\") + 1\n'
                "error_type = \"OK\"\n"
                "status_code = 0\n"
                "\n"
                "# --- SLEEP tylko przy pierwszym retry ---\n"
                "if attempt == 1:\n"
                "    sleep_secs = 45\n"
                "    error_type = 'TIMEOUT'\n"
                "elif attempt == 2:\n"
                "    sleep_secs = 0\n"
                "    error_type = 'NETWORK_ERROR'\n"
                "elif attempt == 3:\n"
                "    sleep_secs = 0\n"
                "    error_type = 'HTTP_ERROR'\n"
                "    status_code = 503\n"
                "else:\n"
                "    sleep_secs = 0\n"
                "    error_type = 'VALIDATION_ERROR'\n"
                "    status_code = 400\n"
                "\n"
                "print(f'Attempt {attempt}: sleep={sleep_secs}s, error_type={error_type}, status_code={status_code}')\n"
                "\n"
                "if sleep_secs > 0:\n"
                "    time.sleep(sleep_secs)\n"
                "\n"
                "\n"
                "if error_type == 'NETWORK_ERROR':\n"
                "    sys.exit(100)\n"
                "elif status_code == 503:\n"
                "    sys.exit(150)\n"
                "elif error_type == 'VALIDATION_ERROR':\n"
                "    sys.exit(200)\n"
                "sys.exit(0)\n"
            ),
            inputs=[Parameter(name="message")],
            timeout="10s",
            retry_strategy=RetryStrategy(
                limit=5,
                expression=(
                    "lastRetry.message matches 'Pod was active on the node longer than the specified deadline'"
                    " || asInt(lastRetry.exitCode) == 100"
                    " || asInt(lastRetry.exitCode) == 150"
                ),
                backoff=m.Backoff(duration='1s', factor='2'),
            )
        )

        main = Steps(name="main")
        with main:
            step1(name="produce-message")
            step2(
                name="consume-message",
                arguments={
                    "message": "{{steps.produce-message.outputs.parameters.message}}"
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
            print("Submission failed (HTTP mode): {}\n".format(e))
    else:
        p.print_help()


if __name__ == "__main__":
    main()