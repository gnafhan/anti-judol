"""
Prometheus metrics instrumentation for FastAPI.

This module sets up Prometheus metrics collection for the FastAPI application,
exposing request count, latency histogram, status codes, and active connections.
"""

from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app):
    """
    Set up Prometheus metrics for the FastAPI application.
    
    Creates and configures the Prometheus instrumentator, then attaches it
    to the FastAPI app and exposes the /metrics endpoint.
    
    Args:
        app: FastAPI application instance
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,  # Always enable metrics
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        inprogress_name="http_requests_in_progress",
        inprogress_labels=True,
    )
    
    instrumentator.instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=True,
        tags=["monitoring"]
    )
