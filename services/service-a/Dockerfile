FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY common.py ./common.py
COPY app.py ./app.py

ENV SERVICE_NAME=service-a \
    SERVICE_B_URL=http://service-b:8000/process \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4318/v1/traces

EXPOSE 8000

CMD ["python", "app.py"]
