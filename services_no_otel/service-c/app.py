import os
import json
import time
import logging
import redis

from opentelemetry import trace
from opentelemetry.propagate import extract
from common import setup_tracing, setup_metrics

SERVICE_NAME = os.getenv("SERVICE_NAME", "service-c")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_QUEUE = os.getenv("REDIS_QUEUE", "tasks")

# tracer = setup_tracing(SERVICE_NAME)
# enable OTEL metrics export for this service
# setup_metrics(SERVICE_NAME)
logger = logging.getLogger(__name__)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def main_loop():
    logger.info("Service C started, waiting for tasks...")
    while True:
        _, raw = redis_client.brpop(REDIS_QUEUE)
        envelope = json.loads(raw)
        otel_context_carrier = envelope.get("otel_context", {})
        task = envelope.get("task", {})


        # ctx = extract(otel_context_carrier)

        # with tracer.start_as_current_span("process-task", context=ctx):
        logger.info("Service C processing task", extra={"payload": task.get("payload")})

        time.sleep(0.5)

if __name__ == "__main__":
    main_loop()
