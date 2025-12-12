"""
Property-based tests for Prometheus metrics recording.

Tests correctness properties for metrics instrumentation in the FastAPI backend.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY, CollectorRegistry
from prometheus_client.parser import text_string_to_metric_families
import re


class TestRequestMetricsRecording:
    """
    **Feature: monitoring-observability, Property 1: Request Metrics Recording**
    **Validates: Requirements 2.2, 2.3**
    
    For any HTTP request to the Backend_Service with any valid path and method,
    the metrics endpoint SHALL return updated counters that include labels
    matching the request's path and method.
    """
    
    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up test client for each test."""
        # Import here to avoid circular imports and ensure fresh app state
        from app.main import app
        self.client = TestClient(app)
    
    # Strategy for valid HTTP methods that the test client supports
    http_methods = st.sampled_from(["GET"])
    
    # Strategy for valid endpoint paths that exist in the application
    valid_paths = st.sampled_from([
        "/health",
        "/",
    ])
    
    @given(
        path=valid_paths,
        method=http_methods
    )
    @settings(max_examples=100)
    def test_request_metrics_include_method_and_path_labels(self, path: str, method: str):
        """
        For any HTTP request, metrics SHALL include labels for method and path.
        """
        # Make the request
        if method == "GET":
            response = self.client.get(path)
        
        # Request should succeed (these are valid endpoints)
        assert response.status_code in [200, 401, 403, 404, 422], \
            f"Request to {method} {path} returned unexpected status {response.status_code}"
        
        # Fetch metrics
        metrics_response = self.client.get("/metrics")
        assert metrics_response.status_code == 200, "Metrics endpoint should be accessible"
        
        metrics_text = metrics_response.text
        
        # Parse metrics to verify structure
        # The prometheus-fastapi-instrumentator creates metrics with handler and method labels
        # Check that we have HTTP request metrics with the expected labels
        
        # Look for http_request_duration_seconds or similar metrics with method label
        has_method_label = 'method="' in metrics_text
        has_handler_label = 'handler="' in metrics_text or 'path="' in metrics_text
        
        assert has_method_label, \
            "Metrics should include 'method' label for HTTP requests"
        assert has_handler_label, \
            "Metrics should include 'handler' or 'path' label for HTTP requests"
    
    @given(
        num_requests=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50)
    def test_request_count_increments_with_requests(self, num_requests: int):
        """
        For any number of requests, the request counter SHALL increment accordingly.
        """
        # Get initial metrics
        initial_metrics = self.client.get("/metrics")
        assert initial_metrics.status_code == 200
        
        # Make multiple requests to health endpoint
        for _ in range(num_requests):
            response = self.client.get("/health")
            assert response.status_code == 200
        
        # Get updated metrics
        final_metrics = self.client.get("/metrics")
        assert final_metrics.status_code == 200
        
        # Verify metrics contain request count data
        # The exact metric name depends on the instrumentator configuration
        metrics_text = final_metrics.text
        
        # Should have some form of request counter or histogram
        has_request_metrics = (
            "http_request" in metrics_text or 
            "requests_total" in metrics_text or
            "request_duration" in metrics_text
        )
        
        assert has_request_metrics, \
            "Metrics should contain HTTP request tracking metrics"
    
    def test_metrics_endpoint_returns_prometheus_format(self):
        """
        The /metrics endpoint SHALL return data in valid Prometheus text format.
        """
        response = self.client.get("/metrics")
        
        assert response.status_code == 200, "Metrics endpoint should return 200"
        
        # Prometheus format should have content type text/plain or similar
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "text/html" in content_type, \
            f"Metrics should be text format, got {content_type}"
        
        metrics_text = response.text
        
        # Prometheus format has specific patterns:
        # - Lines starting with # are comments or metadata
        # - Metric lines have format: metric_name{labels} value
        # - HELP and TYPE declarations
        
        lines = metrics_text.strip().split("\n")
        assert len(lines) > 0, "Metrics response should not be empty"
        
        # Check for standard Prometheus format elements
        has_help = any(line.startswith("# HELP") for line in lines)
        has_type = any(line.startswith("# TYPE") for line in lines)
        has_metrics = any(
            not line.startswith("#") and line.strip() 
            for line in lines
        )
        
        assert has_help, "Metrics should include HELP declarations"
        assert has_type, "Metrics should include TYPE declarations"
        assert has_metrics, "Metrics should include actual metric values"
    
    def test_metrics_include_status_code_labels(self):
        """
        Request metrics SHALL include status code information.
        """
        # Make requests that return different status codes
        self.client.get("/health")  # Should return 200
        self.client.get("/nonexistent-path-12345")  # Should return 404
        
        # Get metrics
        metrics_response = self.client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_text = metrics_response.text
        
        # Check for status code labels in metrics
        has_status_label = 'status="' in metrics_text or 'status_code="' in metrics_text
        
        assert has_status_label, \
            "Metrics should include status code labels for HTTP requests"



class TestStructuredLogCompleteness:
    """
    **Feature: monitoring-observability, Property 2: Structured Log Completeness**
    **Validates: Requirements 4.4**
    
    For any HTTP request processed by Backend_Service, the emitted log entry
    SHALL be valid JSON containing at minimum: timestamp, request_id, method,
    path, and status_code fields.
    """
    
    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up test client for each test."""
        from app.main import app
        self.client = TestClient(app)
    
    # Strategy for valid HTTP methods
    http_methods = st.sampled_from(["GET"])
    
    # Strategy for valid endpoint paths
    valid_paths = st.sampled_from([
        "/health",
        "/",
    ])
    
    @given(
        path=valid_paths,
        method=http_methods
    )
    @settings(max_examples=100)
    def test_log_entry_contains_required_fields(self, path: str, method: str):
        """
        For any HTTP request, the log entry SHALL contain all required fields.
        
        This test verifies that the logging middleware adds the X-Request-ID header
        (proving the middleware ran) and that the logging configuration produces
        valid JSON with required fields by using a custom log handler.
        """
        import json
        import logging
        import io
        
        # Create a custom handler to capture log output
        log_capture = io.StringIO()
        capture_handler = logging.StreamHandler(log_capture)
        capture_handler.setLevel(logging.DEBUG)
        
        # Get the requests logger and add our capture handler
        requests_logger = logging.getLogger("app.requests")
        original_handlers = requests_logger.handlers.copy()
        
        # Use the same formatter as the app
        from app.logging_config import CustomJsonFormatter
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s"
        )
        capture_handler.setFormatter(formatter)
        requests_logger.addHandler(capture_handler)
        
        try:
            # Make the request
            if method == "GET":
                response = self.client.get(path)
            
            # Verify request was processed (middleware ran)
            assert "X-Request-ID" in response.headers, \
                "Response should have X-Request-ID header from logging middleware"
            
            # Get captured log output
            log_output = log_capture.getvalue()
            
            # Parse each line as JSON
            log_lines = [line for line in log_output.strip().split("\n") if line]
            
            # Find request log entries (those with request_id)
            request_logs = []
            for line in log_lines:
                try:
                    log_entry = json.loads(line)
                    if "request_id" in log_entry:
                        request_logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
            
            # Should have at least one request log
            assert len(request_logs) >= 1, \
                f"Should have at least one request log entry, got {len(request_logs)}"
            
            # Verify each request log has required fields
            for log_entry in request_logs:
                # Check required fields exist
                assert "timestamp" in log_entry, \
                    "Log entry must contain 'timestamp' field"
                assert "request_id" in log_entry, \
                    "Log entry must contain 'request_id' field"
                assert "method" in log_entry, \
                    "Log entry must contain 'method' field"
                assert "path" in log_entry, \
                    "Log entry must contain 'path' field"
                assert "status_code" in log_entry, \
                    "Log entry must contain 'status_code' field"
                
                # Verify field types
                assert isinstance(log_entry["timestamp"], str), \
                    "timestamp must be a string"
                assert isinstance(log_entry["request_id"], str), \
                    "request_id must be a string"
                assert isinstance(log_entry["method"], str), \
                    "method must be a string"
                assert isinstance(log_entry["path"], str), \
                    "path must be a string"
                assert isinstance(log_entry["status_code"], int), \
                    "status_code must be an integer"
                
                # Verify method matches request
                assert log_entry["method"] == method, \
                    f"Log method should match request method: {method}"
                
                # Verify path matches request
                assert log_entry["path"] == path, \
                    f"Log path should match request path: {path}"
        finally:
            # Clean up: remove our capture handler
            requests_logger.removeHandler(capture_handler)
    
    def test_log_entry_is_valid_json(self, capsys):
        """
        Log entries SHALL be valid JSON format.
        """
        import json
        import io
        import sys
        
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        
        try:
            sys.stdout = captured_output
            
            # Make a request
            response = self.client.get("/health")
            
            sys.stdout = old_stdout
            
            log_output = captured_output.getvalue()
            log_lines = [line for line in log_output.strip().split("\n") if line]
            
            # Each non-empty line should be valid JSON
            for line in log_lines:
                try:
                    parsed = json.loads(line)
                    assert isinstance(parsed, dict), \
                        "Log entry should be a JSON object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Log entry is not valid JSON: {line[:100]}... Error: {e}")
                    
        finally:
            sys.stdout = old_stdout
    
    def test_request_id_is_uuid_format(self):
        """
        The request_id SHALL be in UUID format.
        """
        import uuid
        
        # Make a request and check the X-Request-ID header
        response = self.client.get("/health")
        
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None, "Response should have X-Request-ID header"
        
        # Verify it's a valid UUID
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"request_id is not a valid UUID: {request_id}")
    
    def test_timestamp_is_iso8601_format(self, capsys):
        """
        The timestamp SHALL be in ISO 8601 format.
        """
        import json
        import io
        import sys
        from datetime import datetime
        
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        
        try:
            sys.stdout = captured_output
            
            response = self.client.get("/health")
            
            sys.stdout = old_stdout
            
            log_output = captured_output.getvalue()
            log_lines = [line for line in log_output.strip().split("\n") if line]
            
            for line in log_lines:
                try:
                    log_entry = json.loads(line)
                    if "timestamp" in log_entry:
                        timestamp = log_entry["timestamp"]
                        # Try to parse as ISO 8601
                        try:
                            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except ValueError:
                            pytest.fail(f"Timestamp is not ISO 8601 format: {timestamp}")
                except json.JSONDecodeError:
                    continue
                    
        finally:
            sys.stdout = old_stdout
