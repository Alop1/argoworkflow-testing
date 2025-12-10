import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def setup_tracing(service_name: str, service_namespace: str | None = "otel-demo"):
    resource_attrs = {"service.name": service_name}
    if service_namespace:
        resource_attrs["service.namespace"] = service_namespace

    resource = Resource.create(resource_attrs)

    provider = TracerProvider(resource=resource)

    # OTLP HTTP exporter to otel-collector inside the cluster
    span_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(span_exporter))

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
