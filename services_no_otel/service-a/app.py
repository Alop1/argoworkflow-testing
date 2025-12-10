import os
import logging
from flask import Flask, jsonify
import requests

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from common import setup_tracing, setup_metrics

SERVICE_NAME = os.getenv("SERVICE_NAME", "service-a")
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8000/process")

app = Flask(__name__)

# setup_tracing(SERVICE_NAME)
# setup_metrics(SERVICE_NAME)
#
# FlaskInstrumentor().instrument_app(app)
# RequestsInstrumentor().instrument()

logger = logging.getLogger(__name__)

@app.route("/start")
def start():
    logger.info("Received request in service A, calling service B")
    resp = requests.post(SERVICE_B_URL, json={"payload": "hello-from-A"})
    return jsonify({"status": "ok", "service_b_status": resp.json()}), resp.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
