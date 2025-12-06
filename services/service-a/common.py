import os
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def setup_tracing(service_name: str):
    resource = Resource.create({"service.name": service_name})

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://otel-collector:4318/v1/traces"),
    )
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)

    # log correlation
    LoggingInstrumentor().instrument(set_logging_format=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s "
               "[service=%(otelServiceName)s trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
               "%(message)s",
    )

    return trace.get_tracer(service_name)

