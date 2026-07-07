"""Prometheus metrics."""
from prometheus_client import Counter, Histogram, Gauge

# API metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)

# AI metrics
ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI provider requests",
    ["provider", "tenant_id"],
)

ai_tokens_used_total = Counter(
    "ai_tokens_used_total",
    "Total tokens consumed",
    ["provider", "token_type", "tenant_id"],
)

# Workflow metrics
workflow_started_total = Counter(
    "workflow_started_total",
    "Total workflows started",
    ["definition_id", "tenant_id"],
)

workflow_completed_total = Counter(
    "workflow_completed_total",
    "Total workflows completed",
    ["definition_id", "status", "tenant_id"],
)

# System
active_tenants = Gauge("active_tenants", "Number of active tenants")
