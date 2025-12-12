"""
Structured JSON logging configuration for FastAPI.

This module provides JSON-formatted logging with request context including
request_id, timestamp, method, path, and status_code for all HTTP requests.
"""

import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request, Response
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds standard fields to all log records.
    """
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO 8601 format
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Ensure message is present
        if "message" not in log_record:
            log_record["message"] = record.getMessage()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests with structured JSON format.
    
    Each log entry includes:
    - request_id: Unique identifier for the request
    - timestamp: ISO 8601 formatted timestamp
    - method: HTTP method (GET, POST, etc.)
    - path: Request path
    - status_code: HTTP response status code
    - duration_ms: Request processing time in milliseconds
    - client_ip: Client IP address
    """
    
    def __init__(self, app: FastAPI, logger: logging.Logger = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("app.requests")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store request_id in request state for access in handlers
        request.state.request_id = request_id
        
        # Record start time
        start_time = datetime.now(timezone.utc)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log the request with structured data
        self.logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }
        )
        
        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_json_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure JSON logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    # Configure JSON formatter
    formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    # Also configure the requests logger
    requests_logger = logging.getLogger("app.requests")
    requests_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    requests_logger.handlers = []
    requests_logger.addHandler(handler)
    requests_logger.propagate = False  # Prevent duplicate logs
    
    return logger


def setup_request_logging(app: FastAPI, log_level: str = "INFO") -> None:
    """
    Set up structured JSON logging middleware for FastAPI.
    
    Args:
        app: FastAPI application instance
        log_level: Logging level for request logs
    """
    # Setup JSON logging
    setup_json_logging(log_level)
    
    # Get the requests logger
    logger = logging.getLogger("app.requests")
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
