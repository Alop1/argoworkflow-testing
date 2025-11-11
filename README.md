# Argo Workflows Demo

This repository shows a minimal setup of Argo Workflows in a Kubernetes cluster plus example workflows (basic, human-in-loop) and an automation script.

## Contents
- `infra/install.yaml` – argo "installation"
- `infra/rbac.yaml` – service account + Role/RoleBinding (adds workflowtaskresults permissions)
- `demo1.yaml` – simple multi-step workflow passing a parameter, example of  retry strategy, resource limitation
- `human_in_loop.yaml` – workflow with a suspend (manual approval) gate
- `create_human_in_loop_wf.py` – Python script creating WF via Argo SDK
- `resume_workflow.py` – Argo SDK example for listing workflows, setting parameters, and resuming

## Prerequisites
- Kubernetes cluster(e.g minikube, k0s) and `kubectl` configured
- Innstalled `argo` CLI:
```bash
# Detect OS
ARGO_OS="darwin"
if [[ "$(uname -s)" != "Darwin" ]]; then
  ARGO_OS="linux"
fi

# Download the binary
curl -sLO "https://github.com/argoproj/argo-workflows/releases/download/v3.7.3/argo-$ARGO_OS-amd64.gz"

# Unzip
gunzip "argo-$ARGO_OS-amd64.gz"

# Make binary executable
chmod +x "argo-$ARGO_OS-amd64"

# Move binary to path
mv "./argo-$ARGO_OS-amd64" /usr/local/bin/argo

# Test installation
argo version
```
https://github.com/argoproj/argo-workflows/releases/


## Install Argo Workflows
```bash
kubectl create namespace argo || true
kubectl apply -n argo -f infra/install
```

### Apply RBAC (adds workflowtaskresults + pod log access)
```bash
kubectl apply -f infra/rbac.yaml
```
Role grants verbs: create, get, list, watch, patch, update on `workflowtaskresults` plus read access to pods/pod logs.

Verify:
```bash
kubectl get ns argo
kubectl -n argo get sa argo-workflow
kubectl get pods -n argo
```

### Port-forward API/UI:
IMPORTANT!!!
```bash
kubectl -n argo port-forward svc/argo-server 2746:2746
```
UI at: http://localhost:2746


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


## Human-in-Loop Workflow (YAML base)
Submit:
```bash
argo submit -n argo human_in_loop.yaml
```
Workflow will suspend at `wait-for-approval`. After it reaches Suspended phase, set the output parameter then resume:
```bash
argo list -n argo
argo node set <workflow-name> -n argo \
  --output-parameter approved=true \
  --node-field-selector displayName=wait-for-approval
argo resume <workflow-name> -n argo
```
Replace `<workflow-name>` (e.g. `conditional-step-xxxxx`). Use `argo get -n argo @latest` to find it.

### Automating Approval (Python Script)
```bash
pip install argo-workflows pyyaml requests
# kubectl -n argo port-forward svc/argo-server 2746:2746 &
export ARGO_SERVER=http://localhost:2746
python human_in_loop_automation.py --file human_in_loop.yaml --approve true
```

## Human-in-Loop Workflow (Code base)
This script recreates `submit_human_in_loop_wf.py.yaml` using the Hera SDK instead of raw YAML.

Render the workflow YAML (no submit):
```bash
python create_human_in_loop_wf.py --print-yaml > hera_rendered.yaml
```
Submit directly (after port-forwarding the Argo server):
```bash
#kubectl -n argo port-forward svc/argo-server 2746:2746 &
python create_human_in_loop_wf.py --submit --server http://localhost:2746
```
### Managing Workflows with Hera SDK (resume_workflow.py)

The `resume_workflow.py` script demonstrates programmatic workflow management using the Hera SDK:

#### Features
- **List workflows**: See all running/completed workflows
- **Set output parameters**: Programmatically approve/reject suspended steps
- **Resume workflows**: Continue execution after setting parameters

Run:
```bash
python resume_workflow.py --server http://localhost:2746
```

The script will:
1. List all workflows in the `argo` namespace
2. Set the `approved` parameter to `"true"` on the suspended node
3. Resume the workflow

To reject instead, change:
```python
output_parameters='{"approved":"false"}'
```



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
- node selectors 
- nodeStatusOffload

## Cons
- Requires Kubernetes knowledge
- Cluster resource overhead
- Security considerations (RBAC, isolation)



## References
- Swagger / API: https://argo-workflows.readthedocs.io/en/latest/swagger/
- Template types: https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#template-types
- Examples: https://github.com/argoproj/argo-workflows/tree/main/examples


## License
Not specified – add if needed.
