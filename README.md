# Argo Workflows Demo

This repository shows a minimal setup of Argo Workflows in a Kubernetes cluster plus example workflows (basic, human-in-loop) and an automation script.

## Contents
- `test_cmds.sh` – reference commands to install and exercise Argo Workflows
- `rbac.yaml` – service account + Role/RoleBinding (adds workflowtaskresults permissions)
- `demo1.yaml` – simple multi-step workflow passing a parameter
- `human_in_loop.yaml` – workflow with a suspend (manual approval) gate
- `human_in_loop_automation.py` – Python script automating approval via Argo API/SDK

## Prerequisites
- Kubernetes cluster and `kubectl` configured
- `argo` CLI installed (https://github.com/argoproj/argo-workflows/releases)
- Optional: Python 3.9+ for automation script (`pip install argo-workflows pyyaml requests`)

## Install Argo Workflows
```bash
kubectl create namespace argo || true
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml
```

## Apply RBAC (adds workflowtaskresults + pod log access)
```bash
kubectl apply -f rbac.yaml
```
Role grants verbs: create, get, list, watch, patch, update on `workflowtaskresults` plus read access to pods/pod logs.

Verify:
```bash
kubectl get ns argo
kubectl -n argo get sa argo-workflow
kubectl -n argo get role argo-workflowtaskresults -o json | grep '"verbs"'
kubectl get pods -n argo
```

## Run Sample Workflow
```bash
argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/main/examples/hello-world.yaml
argo list -n argo
argo get -n argo @latest
```

## Local Demo Workflow (Parameter Passing)
```bash
argo submit -n argo demo1.yaml --watch
```
Step 1 writes message to a file; Argo exposes it as an output parameter consumed by step 2.

## Enable Server Auth Mode (optional)
```bash
kubectl -n argo patch deploy argo-server \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--auth-mode=server"}]'
```
Disable TLS (optional for local testing):
```bash
kubectl -n argo patch deploy argo-server \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--secure=false"}]'
```
Wait for rollout:
```bash
kubectl -n argo rollout status deploy/argo-server
```
Port-forward API/UI:
```bash
kubectl -n argo port-forward svc/argo-server 2746:2746
# UI at: http://localhost:2746
```

## Human-in-Loop Workflow (Manual Approval)
Submit:
```bash
argo submit -n argo human_in_loop.yaml
```
Workflow will suspend at `wait-for-approval`. After it reaches Suspended phase, set the output parameter then resume:
```bash
argo node set <workflow-name> -n argo \
  --output-parameter approved=true \
  --node-field-selector displayName=wait-for-approval
argo resume <workflow-name> -n argo
```
Replace `<workflow-name>` (e.g. `conditional-step-xxxxx`). Use `argo get -n argo @latest` to find it.

## Automating Approval (Python Script)
```bash
pip install argo-workflows pyyaml requests
kubectl -n argo port-forward svc/argo-server 2746:2746 &
export ARGO_SERVER=http://localhost:2746
python human_in_loop_automation.py --file human_in_loop.yaml --approve true
```
Environment overrides:
- `ARGO_SERVER` (default http://localhost:2746)
- `ARGO_NAMESPACE` (default argo)
- `WORKFLOW_FILE`
- `SUSPEND_NODE` (default wait-for-approval)
- `APPROVED_VALUE` (true/false)
- `ARGO_TOKEN` (optional Bearer token when auth-mode=server)

## Logs
```bash
argo logs <workflow-name> -n argo
argo logs <workflow-name> -n argo --step produce-message
kubectl logs <pod-name> -n argo
```
If pod GC deletes pods quickly, adjust `ttlStrategy` or remove aggressive `podGC` settings.

## Pros (Argo Workflows)
- Large community
- Native Kubernetes integration (can create K8s objects during workflow)
- Many template types (scripts, container, suspend, HTTP, etc.)
- Volume handling (PVCs, volume affinity)
- Extensibility (custom tasks/controllers)
- Ecosystem: Argo Events, Argo CD, Argo Rollouts, Argo Artifacts

## Cons
- Configuration complexity
- Requires Kubernetes knowledge
- Cluster resource overhead
- Security considerations (RBAC, isolation)
- Monitoring/log aggregation can be non-trivial

## References
- Swagger / API: https://argo-workflows.readthedocs.io/en/latest/swagger/
- Template types: https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#template-types
- Examples: https://github.com/argoproj/argo-workflows/tree/main/examples

## Troubleshooting
- Permission error creating `workflowtaskresults`: ensure `rbac.yaml` applied and service account set (`spec.serviceAccountName: argo-workflow`).
- Empty logs: pod GC might have removed pods; fetch logs while running or adjust retention.
- Suspend not resuming: verify `approved` parameter set to `true` and resume command succeeded.

## License
Not specified – add if needed.

