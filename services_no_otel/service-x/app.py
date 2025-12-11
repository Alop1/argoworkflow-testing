import os
import logging
import sys
from flask import Flask, jsonify
import requests

# from opentelemetry.instrumentation.flask import FlaskInstrumentor
# from opentelemetry.instrumentation.requests import RequestsInstrumentor


SERVICE_NAME = os.getenv("SERVICE_NAME", "service-x")
SERVICE_Y_URL = os.getenv("SERVICE_Y_URL", "http://service-y:8000/process")

app = Flask(__name__)

# setup_tracing(SERVICE_NAME)
# setup_metrics(SERVICE_NAME)
#
# FlaskInstrumentor().instrument_app(app)
# RequestsInstrumentor().instrument()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

@app.route("/start")
def start():
    logger.info("Received request in service X, calling service Y")
    resp = requests.post(SERVICE_Y_URL, json={"payload": "hello-from-X"})
    return jsonify({"status": "ok", "service_y_status": resp.json()}), resp.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
