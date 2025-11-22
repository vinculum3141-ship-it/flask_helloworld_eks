"""
Integration tests for /health endpoint in deployed Kubernetes environment.

Educational Purpose:
===================
These tests verify that the /health endpoint works correctly when deployed
to Kubernetes and is accessible via different access methods (NodePort,
port-forward, Ingress). This demonstrates:

1. Health endpoint accessibility in production-like environment
2. Difference between configuration tests (test_liveness_probe.py) and runtime tests
3. How Kubernetes liveness probe would actually access the endpoint
4. Performance characteristics under network conditions

Test Strategy:
=============
Tests are marked based on required service type:
- @pytest.mark.nodeport: Requires NodePort service (direct pod access)
- @pytest.mark.ingress: Requires Ingress with ClusterIP (external access)
- @pytest.mark.educational: Educational/demonstration tests

Running Tests:
=============
- NodePort tests: make health-tests (auto-switches service to NodePort)
- Ingress tests: make k8s-tests (uses default ClusterIP + Ingress)
- All tests: make test-full
"""

import pytest
import requests
import time
from .utils import (
    run_kubectl,
    get_service_url,
    get_minikube_ip,
    wait_for_pods_ready
)


class TestHealthEndpointDeployed:
    """Integration tests for deployed /health endpoint."""
    
    @pytest.mark.nodeport
    def test_health_endpoint_via_nodeport(self):
        """
        Test /health endpoint is accessible via NodePort service.
        
        Educational Note:
        This simulates how Kubernetes liveness probe accesses the endpoint -
        direct pod HTTP access within the cluster network.
        """
        # Get service URL
        service_url = get_service_url("hello-flask")
        health_url = f"{service_url}/health"
        
        # Test health endpoint
        response = requests.get(health_url, timeout=5)
        
        assert response.status_code == 200, \
            f"Health endpoint should return 200, got {response.status_code}"
        
        data = response.json()
        assert data == {"status": "healthy"}, \
            f"Expected {{'status': 'healthy'}}, got {data}"
        
        assert response.headers.get("Content-Type") == "application/json", \
            "Health endpoint should return JSON"
    
    
    @pytest.mark.ingress
    def test_health_endpoint_via_ingress(self):
        """
        Test /health endpoint is accessible via Ingress.
        
        Educational Note:
        While liveness probe uses internal cluster networking, external
        monitoring tools might access /health via Ingress. This verifies
        the health endpoint is externally accessible.
        """
        # Get Minikube IP for Ingress access
        minikube_ip = get_minikube_ip()
        health_url = f"http://{minikube_ip}/health"
        
        # Access via Ingress (using Host header)
        headers = {"Host": "hello-flask.local"}
        response = requests.get(health_url, headers=headers, timeout=5)
        
        assert response.status_code == 200, \
            f"Health via Ingress should return 200, got {response.status_code}"
        
        data = response.json()
        assert data == {"status": "healthy"}
    
    
    @pytest.mark.nodeport
    def test_health_endpoint_performance_in_cluster(self):
        """
        Test that /health responds within liveness probe timeout.
        
        Educational Note:
        Deployment has timeoutSeconds: 5 for liveness probe.
        This test verifies /health responds well under that limit,
        preventing false-positive pod restarts.
        
        Target: < 1s (5x safety margin from 5s timeout)
        """
        service_url = get_service_url("hello-flask")
        health_url = f"{service_url}/health"
        
        # Measure multiple requests to get average latency
        latencies = []
        for _ in range(10):
            start_time = time.time()
            response = requests.get(health_url, timeout=5)
            end_time = time.time()
            
            assert response.status_code == 200
            latencies.append(end_time - start_time)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # Health should respond fast (well under 5s timeout)
        assert avg_latency < 1.0, \
            f"Average health latency {avg_latency:.3f}s exceeds 1s (timeout is 5s)"
        
        assert max_latency < 2.0, \
            f"Max health latency {max_latency:.3f}s exceeds 2s (timeout is 5s)"
        
        print(f"\n[Health Performance] Avg: {avg_latency:.3f}s, Max: {max_latency:.3f}s")
    
    
    @pytest.mark.nodeport
    def test_health_consistency_across_replicas(self):
        """
        Test that /health returns same result from all replicas.
        
        Educational Note:
        With 3 replicas, NodePort service round-robins requests.
        All pods should return identical health status (stateless design).
        """
        service_url = get_service_url("hello-flask")
        health_url = f"{service_url}/health"
        
        # Make multiple requests (should hit different pods)
        responses = []
        for _ in range(15):  # With 3 replicas, should hit each ~5 times
            response = requests.get(health_url, timeout=5)
            responses.append({
                "status_code": response.status_code,
                "content": response.json()
            })
        
        # All should return 200
        for i, resp in enumerate(responses, 1):
            assert resp["status_code"] == 200, \
                f"Request {i} failed with status {resp['status_code']}"
            assert resp["content"] == {"status": "healthy"}, \
                f"Request {i} returned different content: {resp['content']}"
    
    
    @pytest.mark.nodeport
    def test_health_endpoint_during_pod_restart(self):
        """
        Test health endpoint behavior during rolling update/restart.
        
        Educational Note:
        Demonstrates how readiness vs liveness probes work together:
        - Liveness (/health): Kills unhealthy pods
        - Readiness (/): Removes pods from service during startup
        
        During restart, old pods serve traffic until new pods are ready.
        """
        # Get current pods
        result = run_kubectl("get", "pods", "-l", "app=hello-flask", "-o", "name")
        initial_pods = [line for line in result.stdout.strip().split('\n') if line]
        
        assert len(initial_pods) >= 1, "Should have at least 1 replica"
        
        # Trigger restart
        run_kubectl("rollout", "restart", "deployment/hello-flask")
        
        # Health endpoint should remain accessible during restart
        # (old pods serve until new pods ready)
        service_url = get_service_url("hello-flask")
        health_url = f"{service_url}/health"
        
        # Poll health during restart
        accessible_count = 0
        for _ in range(20):  # Check over 20 seconds
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    accessible_count += 1
            except requests.exceptions.RequestException:
                pass  # Expected during brief service disruption
            
            time.sleep(1)
        
        # Should be accessible most of the time (rolling update)
        assert accessible_count >= 15, \
            f"Health was only accessible {accessible_count}/20 times during restart"
        
        # Wait for rollout to complete
        run_kubectl("rollout", "status", "deployment/hello-flask", "--timeout=60s")
        
        # Verify health works after restart
        response = requests.get(health_url, timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    
    @pytest.mark.nodeport
    def test_health_vs_root_response_time_comparison(self):
        """
        Compare /health vs / endpoint performance.
        
        Educational Note:
        Health endpoints should be faster than application endpoints:
        - /health: Minimal logic, just returns status
        - /: May include environment variables, config lookups
        
        This demonstrates why we use separate endpoints for probes.
        """
        service_url = get_service_url("hello-flask")
        
        # Measure /health
        health_latencies = []
        for _ in range(10):
            start = time.time()
            requests.get(f"{service_url}/health", timeout=5)
            health_latencies.append(time.time() - start)
        
        # Measure /
        root_latencies = []
        for _ in range(10):
            start = time.time()
            requests.get(f"{service_url}/", timeout=5)
            root_latencies.append(time.time() - start)
        
        avg_health = sum(health_latencies) / len(health_latencies)
        avg_root = sum(root_latencies) / len(root_latencies)
        
        print(f"\n[Latency Comparison]")
        print(f"/health: {avg_health:.3f}s (avg)")
        print(f"/      : {avg_root:.3f}s (avg)")
        
        # Health should be at least as fast (usually faster)
        # Note: In this simple app they're similar, but principle holds
        assert avg_health <= avg_root * 1.5, \
            "/health should not be slower than / (health checks should be lightweight)"
    
    
    @pytest.mark.nodeport
    def test_health_endpoint_without_readiness(self):
        """
        Test that /health endpoint works even if readiness probe fails.
        
        Educational Note:
        Demonstrates key difference between probes:
        - Liveness (/health): Can pod run? If not, kill it.
        - Readiness (/): Should pod receive traffic? If not, remove from service.
        
        A pod can be "alive" but "not ready". Liveness probe must work
        independently of readiness probe.
        """
        # This test verifies /health is a separate endpoint from /
        # In this app, both always succeed, but architecture supports independence
        
        service_url = get_service_url("hello-flask")
        
        # Both endpoints should work
        health_response = requests.get(f"{service_url}/health", timeout=5)
        root_response = requests.get(f"{service_url}/", timeout=5)
        
        assert health_response.status_code == 200
        assert root_response.status_code == 200
        
        # They return different content (different purposes)
        assert health_response.json() != root_response.json(), \
            "/health and / should be independent endpoints"
        
        # Health is simpler (just status)
        health_data = health_response.json()
        assert health_data == {"status": "healthy"}, \
            "/health should return simple status, not application data"


class TestHealthEndpointEducational:
    """Educational tests demonstrating health check concepts."""
    
    @pytest.mark.nodeport
    def test_liveness_probe_configuration_matches_health_endpoint(self):
        """
        Verify deployment's liveness probe configuration matches /health behavior.
        
        Educational Note:
        Shows the connection between:
        1. Kubernetes config (deployment.yaml)
        2. Flask route (/health)
        3. Actual runtime behavior
        """
        # Get deployment config
        result = run_kubectl(
            "get", "deployment", "hello-flask",
            "-o", "jsonpath={.spec.template.spec.containers[0].livenessProbe}"
        )
        
        import json
        liveness_config = json.loads(result.stdout)
        
        # Verify configuration
        assert liveness_config["httpGet"]["path"] == "/health", \
            "Liveness probe should use /health endpoint"
        assert liveness_config["httpGet"]["port"] == 5000
        assert liveness_config["timeoutSeconds"] == 5
        
        # Verify endpoint actually exists and responds fast enough
        service_url = get_service_url("hello-flask")
        start = time.time()
        response = requests.get(f"{service_url}/health", timeout=5)
        latency = time.time() - start
        
        assert response.status_code == 200, \
            "Health endpoint must return 200 for liveness probe"
        
        assert latency < liveness_config["timeoutSeconds"], \
            f"Health latency {latency:.3f}s exceeds timeout {liveness_config['timeoutSeconds']}s"
        
        print(f"\n[Config Validation]")
        print(f"Liveness probe: {liveness_config['httpGet']['path']}")
        print(f"Timeout: {liveness_config['timeoutSeconds']}s")
        print(f"Actual latency: {latency:.3f}s")
        print(f"Safety margin: {liveness_config['timeoutSeconds'] - latency:.3f}s")
    
    
    @pytest.mark.educational
    def test_demonstrate_probe_frequency(self):
        """
        Demonstrate how often Kubernetes probes the health endpoint.
        
        Educational Note:
        Liveness probe config: periodSeconds=10
        This means Kubernetes calls /health every 10 seconds per pod.
        With multiple replicas, probe frequency scales linearly.
        
        Health endpoints must be lightweight!
        """
        # Get probe config
        result = run_kubectl(
            "get", "deployment", "hello-flask",
            "-o", "jsonpath={.spec.template.spec.containers[0].livenessProbe.periodSeconds}"
        )
        period_seconds = int(result.stdout.strip())
        
        # Get replica count
        result = run_kubectl(
            "get", "deployment", "hello-flask",
            "-o", "jsonpath={.spec.replicas}"
        )
        replicas = int(result.stdout.strip())
        
        # Calculate probe frequency
        probes_per_minute_per_pod = 60 / period_seconds
        total_probes_per_minute = probes_per_minute_per_pod * replicas
        
        print(f"\n[Probe Frequency Analysis]")
        print(f"Period: Every {period_seconds}s")
        print(f"Replicas: {replicas}")
        print(f"Probes/min per pod: {probes_per_minute_per_pod}")
        print(f"Total probes/min: {total_probes_per_minute}")
        print(f"\nImplication: /health must be fast and have no side effects!")
        
        # Verify configuration (educational - should be flexible)
        assert period_seconds == 10, "Liveness probe period should be 10s"
        assert replicas >= 1, f"Should have at least 1 replica (current: {replicas})"
        
        # Educational message about scaling
        if replicas < 3:
            print(f"\nNote: Deployment has {replicas} replicas. With 3 replicas, total would be {probes_per_minute_per_pod * 3} probes/min")
