# otel-demo – 3 serwisy w Pythonie + OpenTelemetry + Loki + VictoriaMetrics + Jaeger

Ten chart Helma deployuje demo-aplikację z **trzema serwisami w Pythonie** oraz **OpenTelemetry Collectorem** i **Jaegerem**:

- **Service A** – Flask API  
  - endpoint `/start`  
  - woła **Service B** po HTTP

- **Service B** – Flask API  
  - endpoint `/process`  
  - przyjmuje request od A  
  - tworzy task i wrzuca go do kolejki w **Redisie**  
  - do taska dokłada **kontekst OTel** (traceparent, tracestate)

- **Service C** – worker (zwykły proces)  
  - czyta taski z kolejki Redis (`BRPOP`)  
  - odtwarza kontekst OTel (`extract`)  
  - kontynuuje trace → **A, B i C mają wspólny `trace_id`**

Do tego:

- **OpenTelemetry Collector (DaemonSet)**:
  - zbiera **traces/metrics** przez OTLP (HTTP/GRPC) od serwisów
  - zbiera **logi z stdout** przez `filelog` z `/var/log/containers`
  - wysyła:
    - **traces → Jaeger (OTLP)**
    - **logs → Loki**
    - **metrics → VictoriaMetrics (remote_write)**

- **Jaeger all-in-one** – backend na trace’y + UI (port 16686)


Wszystkie serwisy:

- używają **OpenTelemetry SDK** (tracing + log correlation),
- logują w **stdout**,
- logi są zbierane przez **OTel Collectora**, a nie przez aplikację.



# 2. Instalacja
```shell
 minikube image load service-a:latest
 minikube image load service-b:latest
 minikube image load service-c:latest

```



```shell
export NAMESPACE=otel-demo
kubectl create namespace $NAMESPACE  

helm upgrade --install otel-demo . -n $NAMESPACE 

# SERVICE A
kubectl port-forward -n $NAMESPACE svc/service-a 8000:8000
curl http://localhost:8000/start

kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000
kubectl port-forward -n $NAMESPACE svc/jaeger 4317:4317
#http://localhost:16686


#GRAFANA
http://localhost:3000
```