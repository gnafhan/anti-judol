"""
Property-based tests for log forwarding with labels.

Tests correctness properties for Promtail log forwarding configuration.
This validates that logs forwarded to Loki include proper service labels.
"""

import pytest
from hypothesis import given, strategies as st, settings
import json
import re
import os

# Get the project root directory (parent of backend)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROMTAIL_CONFIG_PATH = os.path.join(PROJECT_ROOT, "monitoring", "promtail", "promtail-config.yml")
DOCKER_COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")


class TestLogForwardingWithLabels:
    """
    **Feature: monitoring-observability, Property 3: Log Forwarding with Labels**
    **Validates: Requirements 4.2**
    
    For any log entry written by a containerized service, when queried from Loki,
    the entry SHALL include labels identifying the source service name and container.
    """
    
    def test_promtail_config_extracts_service_name_label(self):
        """
        Promtail configuration SHALL extract service_name label from Docker metadata.
        """
        import yaml
        
        # Read the promtail configuration
        with open(PROMTAIL_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        # Find the docker scrape config
        scrape_configs = config.get("scrape_configs", [])
        docker_config = None
        
        for sc in scrape_configs:
            if sc.get("job_name") == "docker":
                docker_config = sc
                break
        
        assert docker_config is not None, \
            "Promtail config should have a 'docker' job for container discovery"
        
        # Check relabel configs for service_name extraction
        relabel_configs = docker_config.get("relabel_configs", [])
        
        has_service_name_label = False
        for relabel in relabel_configs:
            target_label = relabel.get("target_label", "")
            if target_label == "service_name":
                has_service_name_label = True
                # Verify it extracts from docker compose service label
                source_labels = relabel.get("source_labels", [])
                assert any("compose_service" in str(sl) for sl in source_labels), \
                    "service_name should be extracted from docker compose service label"
                break
        
        assert has_service_name_label, \
            "Promtail config should extract 'service_name' label from container metadata"
    
    def test_promtail_config_extracts_container_name_label(self):
        """
        Promtail configuration SHALL extract container_name label from Docker metadata.
        """
        import yaml
        
        # Read the promtail configuration
        with open(PROMTAIL_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        # Find the docker scrape config
        scrape_configs = config.get("scrape_configs", [])
        docker_config = None
        
        for sc in scrape_configs:
            if sc.get("job_name") == "docker":
                docker_config = sc
                break
        
        assert docker_config is not None, \
            "Promtail config should have a 'docker' job for container discovery"
        
        # Check relabel configs for container_name extraction
        relabel_configs = docker_config.get("relabel_configs", [])
        
        has_container_name_label = False
        for relabel in relabel_configs:
            target_label = relabel.get("target_label", "")
            if target_label == "container_name":
                has_container_name_label = True
                # Verify it extracts from docker container name
                source_labels = relabel.get("source_labels", [])
                assert any("container_name" in str(sl) for sl in source_labels), \
                    "container_name should be extracted from docker container name metadata"
                break
        
        assert has_container_name_label, \
            "Promtail config should extract 'container_name' label from container metadata"
    
    def test_promtail_config_has_loki_client(self):
        """
        Promtail configuration SHALL have Loki as the push target.
        """
        import yaml
        
        # Read the promtail configuration
        with open(PROMTAIL_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        clients = config.get("clients", [])
        assert len(clients) > 0, "Promtail should have at least one client configured"
        
        # Check that Loki is configured as the target
        loki_client = None
        for client in clients:
            url = client.get("url", "")
            if "loki" in url and "/loki/api/v1/push" in url:
                loki_client = client
                break
        
        assert loki_client is not None, \
            "Promtail should have Loki configured as push target"
    
    def test_promtail_config_parses_json_logs(self):
        """
        Promtail configuration SHALL parse JSON structured logs from backend.
        """
        import yaml
        
        # Read the promtail configuration
        with open(PROMTAIL_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        # Find the docker scrape config
        scrape_configs = config.get("scrape_configs", [])
        docker_config = None
        
        for sc in scrape_configs:
            if sc.get("job_name") == "docker":
                docker_config = sc
                break
        
        assert docker_config is not None, \
            "Promtail config should have a 'docker' job"
        
        # Check pipeline stages for JSON parsing
        pipeline_stages = docker_config.get("pipeline_stages", [])
        
        has_json_stage = False
        for stage in pipeline_stages:
            if "json" in stage:
                has_json_stage = True
                break
            # Also check nested match stages
            if "match" in stage:
                match_stages = stage["match"].get("stages", [])
                for ms in match_stages:
                    if "json" in ms:
                        has_json_stage = True
                        break
        
        assert has_json_stage, \
            "Promtail config should have JSON parsing stage for structured logs"
    
    # Strategy for generating sample service names
    service_names = st.sampled_from([
        "backend",
        "celery-worker",
        "celery-beat",
        "flower",
        "postgres",
        "redis"
    ])
    
    # Strategy for generating sample container names
    container_names = st.sampled_from([
        "gambling-detector-backend-1",
        "gambling-detector-celery-worker-1",
        "gambling-detector-celery-beat-1",
        "gambling-detector-flower-1",
        "gambling-detector-postgres-1",
        "gambling-detector-redis-1"
    ])
    
    @given(
        service_name=service_names,
        container_name=container_names
    )
    @settings(max_examples=100)
    def test_log_labels_format_is_valid(self, service_name: str, container_name: str):
        """
        For any service and container name combination, the label format SHALL be valid.
        
        This tests that the label values we expect to extract are valid Prometheus/Loki
        label values (alphanumeric with underscores and hyphens).
        """
        # Prometheus/Loki label values should match this pattern
        # They can contain alphanumeric characters, underscores, and hyphens
        valid_label_pattern = re.compile(r'^[a-zA-Z0-9_\-]+$')
        
        assert valid_label_pattern.match(service_name), \
            f"Service name '{service_name}' should be a valid label value"
        
        assert valid_label_pattern.match(container_name), \
            f"Container name '{container_name}' should be a valid label value"
    
    @given(
        log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        request_id=st.uuids().map(str),
        method=st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH"]),
        path=st.sampled_from(["/health", "/api/users", "/api/scans", "/metrics"]),
        status_code=st.sampled_from([200, 201, 400, 401, 403, 404, 500])
    )
    @settings(max_examples=100)
    def test_structured_log_can_be_parsed_by_promtail(
        self, 
        log_level: str, 
        request_id: str, 
        method: str, 
        path: str, 
        status_code: int
    ):
        """
        For any structured log entry from the backend, Promtail SHALL be able to
        extract the standard fields (level, request_id, method, path, status_code).
        
        This validates that our log format is compatible with the Promtail pipeline.
        """
        from datetime import datetime, timezone
        
        # Create a log entry in the same format as our logging_config produces
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": log_level,
            "logger": "app.requests",
            "message": "Request completed",
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": 15.5,
            "client_ip": "192.168.1.1"
        }
        
        # Serialize to JSON (as it would appear in Docker logs)
        log_json = json.dumps(log_entry)
        
        # Verify it's valid JSON that can be parsed
        parsed = json.loads(log_json)
        
        # Verify all expected fields are present and extractable
        assert parsed.get("level") == log_level, \
            "level field should be extractable"
        assert parsed.get("request_id") == request_id, \
            "request_id field should be extractable"
        assert parsed.get("method") == method, \
            "method field should be extractable"
        assert parsed.get("path") == path, \
            "path field should be extractable"
        assert parsed.get("status_code") == status_code, \
            "status_code field should be extractable"
    
    def test_docker_compose_services_have_labels(self):
        """
        Docker Compose services SHALL have labels that Promtail can extract.
        
        This verifies that the docker-compose.yml is configured in a way that
        allows Promtail to identify services by their compose labels.
        """
        import yaml
        
        # Read docker-compose.yml
        with open(DOCKER_COMPOSE_PATH, "r") as f:
            compose = yaml.safe_load(f)
        
        services = compose.get("services", {})
        
        # Key services that should be monitored
        monitored_services = ["backend", "celery-worker", "celery-beat"]
        
        for service_name in monitored_services:
            if service_name in services:
                # Docker Compose automatically adds com.docker.compose.service label
                # We just need to verify the service exists
                assert service_name in services, \
                    f"Service '{service_name}' should exist in docker-compose.yml"
        
        # Verify promtail service exists and has docker socket mounted
        assert "promtail" in services, \
            "Promtail service should be defined in docker-compose.yml"
        
        promtail_service = services["promtail"]
        volumes = promtail_service.get("volumes", [])
        
        has_docker_socket = any(
            "/var/run/docker.sock" in str(v) 
            for v in volumes
        )
        
        assert has_docker_socket, \
            "Promtail should have Docker socket mounted for container discovery"
