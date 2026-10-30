"""OpenTelemetry setup for FastAPI.

This module is intentionally defensive: the repo can run without telemetry when the
installed OpenTelemetry packages are mismatched or unavailable in a local dev env.
"""
from fastapi import FastAPI
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except Exception as exc:  # pragma: no cover - runtime robustness for mismatched installs
    trace = None
    OTLPSpanExporter = None
    FastAPIInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    _otel_import_error = exc
else:
    _otel_import_error = None


def configure_telemetry(app: FastAPI) -> None:
    if not settings.otel_exporter_otlp_endpoint:
        logger.info("otel_disabled", reason="OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return

    if trace is None or OTLPSpanExporter is None or FastAPIInstrumentor is None:
        logger.warning(
            "otel_disabled",
            reason="opentelemetry_import_failed",
            error=str(_otel_import_error),
        )
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    logger.info("otel_configured", service=settings.otel_service_name)


def get_tracer(name: str):
    if trace is None:
        return None
    return trace.get_tracer(name)
