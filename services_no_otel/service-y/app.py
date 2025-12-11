import os
import json
import logging
import sys
from flask import Flask, request, jsonify
import redis

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import inject
from common import setup_tracing, setup_metrics

SERVICE_NAME = os.getenv("SERVICE_NAME", "service-y")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "tasks")

app = Flask(__name__)

# tracer = setup_tracing(SERVICE_NAME)
# # enable OTEL metrics export (auto-instrumentation)
# setup_metrics(SERVICE_NAME)
# FlaskInstrumentor().instrument_app(app)

# Configure root logger to print to stdout at INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@app.route("/process", methods=["POST"])
def process():
    body = request.get_json() or {}
    logger.info("Service Y received request, pushing task to queue")

    task = {
        "payload": body.get("payload", "no-payload"),
    }

    # otel context -> carrier
    carrier = {}
    inject(carrier)  # wstawi 'traceparent', 'tracestate'

    task_envelope = {
        "task": task,
        "otel_context": carrier,
    }

    redis_client.lpush(REDIS_QUEUE, json.dumps(task_envelope))

    return jsonify({"queued": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
