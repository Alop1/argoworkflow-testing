kubectl create namespace argo || true
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml

# apply workflow RBAC (now includes patch/update)
kubectl apply -f rbac.yaml

# verify namespace + service account
kubectl get ns argo
kubectl -n argo get sa argo-workflow

# verify Role verbs include patch/update
kubectl -n argo get role argo-workflowtaskresults -o json | grep -E '"verbs"' || true

kubectl get pods -n argo

argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/main/examples/hello-world.yaml

argo list -n argo
argo get -n argo @latest

# submit local workflow (demo1.yaml)
argo submit -n argo demo1.yaml --watch

# add auth-mode=server to argo-server
kubectl -n argo patch deploy argo-server \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--auth-mode=server"}]'

# (optional) disable TLS
kubectl -n argo patch deploy argo-server \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--secure=false"}]'

kubectl -n argo rollout status deploy/argo-server

kubectl -n argo port-forward svc/argo-server 2746:2746
# http://localhost:2746



#resume workflow scenario
argo submit -n argo human_in_loop.yaml

argo node set conditional-step-pl4gv \
  -n argo \
  --output-parameter approved=true \
  --node-field-selector displayName=wait-for-approval

argo resume conditional-step-pl4gv  -n argo

# argo documentation
#https://argo-workflows.readthedocs.io/en/latest/swagger/
# template types
#https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#template-types
#przyklady workflowow
# https://github.com/argoproj/argo-workflows/tree/main/examples

# plusy:
# - duza spolecznosc
# - integracja z kubernetes - tworzenie obiektow k8s na w trakcie workflow
# - duzo gotowych rozwiazan (template types)
#  volumeny https://argo-workflows.readthedocs.io/en/latest/walk-through/volumes/, Volume Node Affinity
# - elastycznosc (custom tasky, custom controller)
# - argo events (event-driven workflows)
# - argo cd (ci/cd dla kubernetes)
# - argo rollouts (strategie wdrozen dla kubernetes)
# - argo artifacts (zarzadzanie artefaktami)


# minusy:
# - zlozonosc konfiguracji
# - wymaga znajomosci kubernetes
# - overhead zarzadzania klastrem kubernetes
# - ograniczenia zasobow klastra kubernetes
# - potencjalne problemy z bezpieczenstwem (RBAC, izolacja)
# - monitoring i logowanie moze byc skomplikowane