"""
Test service accessibility via NodePort.

This test verifies that the Flask application can be reached through
a NodePort service type using Minikube's service URL feature.
"""
import requests
import time
import pytest

from .utils import get_service, get_service_url


@pytest.mark.nodeport
def test_service_is_nodeport(service):
    """Verify that the service is configured as NodePort type."""
    service_type = service["spec"]["type"]
    
    if service_type != "NodePort":
        pytest.skip(
            f"Service type is '{service_type}', not 'NodePort'. "
            f"This test only runs with NodePort service type."
        )
    
    print(f"✓ Service type: {service_type}")


@pytest.mark.nodeport
def test_nodeport_service_reachable(service, k8s_timeouts):
    """
    Test that the service is reachable via NodePort.
    
    Uses 'minikube service hello-flask --url' to get the accessible URL.
    """
    service_type = service["spec"]["type"]
    
    if service_type != "NodePort":
        pytest.skip(f"Service type is '{service_type}', not 'NodePort'")
    
    print(f"Testing NodePort service accessibility...")
    
    # Get the service URL from Minikube
    url = None
    for attempt in range(5):
        url = get_service_url("hello-flask")
        if url:
            break
        time.sleep(1)
    
    assert url, (
        "minikube returned an empty URL for service 'hello-flask'. "
        "Is the service deployed with type NodePort?"
    )
    
    assert url.startswith(("http://", "https://")), \
        f"Service URL does not include scheme: {url!r}"
    
    print(f"Service URL: {url}")
    
    # Test the URL
    timeout = k8s_timeouts.get('http_request', 5)
    
    try:
        resp = requests.get(url, timeout=timeout)
        assert resp.status_code == 200, \
            f"Unexpected status {resp.status_code} from {url}"
        assert "Hello" in resp.text, \
            f"Expected 'Hello' in response from {url}"
        
        print(f"✓ Service is reachable at {url}")
        print(f"✓ Response: {resp.text[:100]}...")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(
            f"Failed to reach service at {url}. "
            f"Error: {e}. "
            f"Ensure: 1) Minikube is running, 2) Service is deployed, "
            f"3) Pods are ready."
        )


@pytest.mark.nodeport
def test_nodeport_in_range(service):
    """Verify that the NodePort is in the valid Kubernetes range (30000-32767)."""
    service_type = service["spec"]["type"]
    
    if service_type != "NodePort":
        pytest.skip(f"Service type is '{service_type}', not 'NodePort'")
    
    ports = service["spec"]["ports"]
    assert len(ports) > 0, "Service has no ports configured"
    
    for port in ports:
        if "nodePort" in port:
            node_port = port["nodePort"]
            assert 30000 <= node_port <= 32767, \
                f"NodePort {node_port} is outside valid range (30000-32767)"
            print(f"✓ NodePort {node_port} is in valid range")
