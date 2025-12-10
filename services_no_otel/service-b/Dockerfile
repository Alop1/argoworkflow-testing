FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY common.py ./common.py
COPY app.py ./app.py

ENV SERVICE_NAME=service-b \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_QUEUE=tasks \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4318/v1/traces

EXPOSE 8000

CMD ["python", "app.py"]
