#  start workflow and wait for suspend

```shell
run_workflow.py --submit
```

# kill pods from wf execution

```shell
kubectl -n argo delete pod -l workflows.argoproj.io/workflow=<workflow-name>
```

# resume workflow after pod restarts

```shell
python ../../resume_workflow.py --approved false --workflow <wf name>
```
----------------------------------------------------


#  start workflow and wait for suspend

```shell
run_workflow.py --submit
```

# kill all argo controller()

```shell
k delete pod -n argo -l  app=workflow-controller
```

# resume workflow after pod restarts

```shell
python ../../resume_workflow.py --approved true --workflow  <wf name>
```