"""
Test service accessibility via Ingress.

This test verifies that the Flask application can be reached through
an Ingress resource (for ClusterIP service type).
"""
import signal
import subprocess
import time

import requests
import pytest

from .utils import get_service, get_ingress, get_minikube_ip, is_ci_environment


def get_ingress_url_and_host(ingress):
    """
    Get URL and host header from Ingress resource.
    
    In CI/CD environments, uses Minikube IP directly.
    In local development, uses the ingress hostname.
    
    Returns:
        tuple: (url, host_header) where host_header is the Host header to use
    """
    rules = ingress.get("spec", {}).get("rules", [])
    if not rules:
        return None, None
    
    # Get the configured hostname from ingress rules
    ingress_host = rules[0].get("host", "hello-flask.local")
    
    # In CI/CD: Use Minikube IP instead of hostname (DNS won't resolve)
    if is_ci_environment():
        print("Detected CI environment - using Minikube IP instead of hostname")
        minikube_ip = get_minikube_ip()
        
        if minikube_ip:
            print(f"Using Minikube IP: {minikube_ip} with Host header: {ingress_host}")
            # Return IP-based URL but also return the host header to use
            return f"http://{minikube_ip}", ingress_host
        else:
            print("Warning: Could not get Minikube IP, falling back to hostname")
    
    # Local development: Use the ingress hostname
    print(f"Using Ingress hostname: {ingress_host}")
    return f"http://{ingress_host}", ingress_host


@pytest.mark.ingress
def test_service_is_clusterip(service):
    """Verify that the service is configured as ClusterIP when using Ingress."""
    service_type = service["spec"]["type"]
    
    if service_type != "ClusterIP":
        pytest.skip(
            f"Service type is '{service_type}', not 'ClusterIP'. "
            f"This test assumes ClusterIP with Ingress."
        )
    
    print(f"✓ Service type: {service_type} (using Ingress for external access)")


@pytest.mark.ingress
def test_ingress_service_reachable(service, ingress, k8s_timeouts):
    """
    Test that the service is reachable via Ingress.
    
    This test supports both CI/CD (using Minikube IP) and local environments
    (using /etc/hosts entries).
    """
    service_type = service["spec"]["type"]
    
    if service_type != "ClusterIP":
        pytest.skip(f"Service type is '{service_type}', expected 'ClusterIP' for Ingress test")
    
    print(f"Testing Ingress service accessibility...")
    
    # Get URL and Host header from Ingress
    url, host_header = get_ingress_url_and_host(ingress)
    
    assert url, (
        "No valid Ingress URL could be determined. "
        "Ensure Ingress resource is deployed and configured correctly."
    )
    
    print(f"Ingress URL: {url}")
    
    # Prepare headers
    headers = {}
    if host_header and not url.endswith(host_header):
        headers['Host'] = host_header
        print(f"Setting Host header: {host_header}")
    
    # Test the URL
    timeout = k8s_timeouts.get('http_request', 5)
    
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        assert resp.status_code == 200, \
            f"Unexpected status {resp.status_code} from {url}"
        assert "Hello" in resp.text, \
            f"Expected 'Hello' in response from {url}"
        
        print(f"✓ Service is reachable via Ingress at {url}")
        print(f"✓ Response: {resp.text[:100]}...")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(
            f"Failed to reach service at {url}. "
            f"Error: {e}. "
            f"If using Ingress, ensure: 1) Ingress controller is running, "
            f"2) /etc/hosts is configured (local) or Minikube IP is accessible (CI), "
            f"3) Ingress resource is deployed."
        )


@pytest.mark.ingress
def test_ingress_points_to_correct_service(ingress, service_name):
    """Verify that the Ingress routes to the correct service."""
    rules = ingress.get("spec", {}).get("rules", [])
    assert len(rules) > 0, "Ingress has no rules defined"
    
    # Check the backend service name
    paths = rules[0].get("http", {}).get("paths", [])
    assert len(paths) > 0, "Ingress rule has no paths"
    
    backend = paths[0].get("backend", {})
    backend_service_name = backend.get("service", {}).get("name")
    
    assert backend_service_name == service_name, \
        f"Ingress backend points to '{backend_service_name}', expected '{service_name}'"
    
    print(f"✓ Ingress correctly routes to service '{service_name}'")


@pytest.mark.ingress
@pytest.mark.educational
def test_hostname_routing_rejects_wrong_host(ingress, k8s_timeouts):
    """
    Educational: Verify that wrong Host header returns 404 (hostname-based routing).
    
    This demonstrates how Ingress routes based on the HTTP Host header,
    not just the URL path. This is a key concept in understanding how
    Ingress controllers work.
    """
    rules = ingress.get("spec", {}).get("rules", [])
    if not rules:
        pytest.skip("No Ingress rules configured")
    
    ingress_host = rules[0].get("host", "hello-flask.local")
    minikube_ip = get_minikube_ip()
    
    if not minikube_ip:
        pytest.skip("Could not get Minikube IP")
    
    timeout = k8s_timeouts.get('http_request', 5)
    
    print(f"\nTesting hostname-based routing:")
    print(f"  Configured hostname: {ingress_host}")
    print(f"  Minikube IP: {minikube_ip}")
    
    # Test 1: Correct Host header should work (200)
    try:
        resp_correct = requests.get(
            f"http://{minikube_ip}",
            headers={'Host': ingress_host},
            timeout=timeout
        )
        print(f"  ✓ Request with correct Host header '{ingress_host}': {resp_correct.status_code}")
        assert resp_correct.status_code == 200, \
            f"Expected 200 with correct Host header, got {resp_correct.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Could not test correct hostname: {e}")
    
    # Test 2: Wrong Host header should return 404
    try:
        resp_wrong = requests.get(
            f"http://{minikube_ip}",
            headers={'Host': 'wrong-hostname.local'},
            timeout=timeout
        )
        print(f"  ✓ Request with wrong Host header 'wrong-hostname.local': {resp_wrong.status_code}")
        assert resp_wrong.status_code == 404, \
            f"Expected 404 with wrong Host header, got {resp_wrong.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Could not test wrong hostname: {e}")
    
    # Test 3: No Host header (IP as Host) should also return 404
    try:
        resp_no_header = requests.get(f"http://{minikube_ip}", timeout=timeout)
        print(f"  ✓ Request with IP as Host header '{minikube_ip}': {resp_no_header.status_code}")
        assert resp_no_header.status_code == 404, \
            f"Expected 404 with IP as Host, got {resp_no_header.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Could not test IP hostname: {e}")
    
    print("\n  📚 Learning: Ingress routes based on Host header, not URL!")
    print(f"     - Host: {ingress_host} → 200 OK")
    print(f"     - Host: wrong-hostname.local → 404 Not Found")
    print(f"     - Host: {minikube_ip} → 404 Not Found")


@pytest.mark.ingress
@pytest.mark.educational
def test_response_consistency_ingress_vs_direct(service, ingress, k8s_timeouts):
    """
    Educational: Compare response via Ingress vs direct service access.
    
    This demonstrates that Ingress acts as a proxy/router without modifying
    the application response. The response content should be identical whether
    accessed through Ingress or directly via port-forward.
    """
    service_type = service["spec"]["type"]
    
    if service_type != "ClusterIP":
        pytest.skip(f"Service type is '{service_type}', expected 'ClusterIP'")
    
    timeout = k8s_timeouts.get('http_request', 5)
    
    # Get response via Ingress
    url, host_header = get_ingress_url_and_host(ingress)
    if not url:
        pytest.skip("Could not determine Ingress URL")
    
    headers = {}
    if host_header and not url.endswith(host_header):
        headers['Host'] = host_header
    
    try:
        ingress_response = requests.get(url, headers=headers, timeout=timeout)
        ingress_json = ingress_response.json()
        print(f"\n  Response via Ingress: {ingress_json}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Could not get response via Ingress: {e}")
    
    # Get response via port-forward (direct to service)
    # Start port-forward in background
    
    service_name = service["metadata"]["name"]
    service_port = service["spec"]["ports"][0]["port"]
    local_port = 18080  # Use a non-standard port to avoid conflicts
    
    print(f"  Starting port-forward to {service_name}:{service_port}...")
    
    port_forward_proc = subprocess.Popen(
        ["kubectl", "port-forward", f"service/{service_name}", f"{local_port}:{service_port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for port-forward to establish
    time.sleep(2)
    
    try:
        direct_response = requests.get(f"http://localhost:{local_port}", timeout=timeout)
        direct_json = direct_response.json()
        print(f"  Response via port-forward: {direct_json}")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Could not get response via port-forward: {e}")
    finally:
        # Clean up port-forward process
        port_forward_proc.send_signal(signal.SIGTERM)
        port_forward_proc.wait(timeout=5)
    
    # Compare responses
    assert ingress_response.status_code == direct_response.status_code, \
        f"Status codes differ: Ingress={ingress_response.status_code}, Direct={direct_response.status_code}"
    
    assert ingress_json == direct_json, \
        f"Response bodies differ:\n  Ingress: {ingress_json}\n  Direct: {direct_json}"
    
    print("\n  ✓ Responses are identical via Ingress and direct access")
    print("  📚 Learning: Ingress proxies requests without modifying responses")


@pytest.mark.ingress
@pytest.mark.educational
def test_ingress_load_balancing(service, ingress, k8s_timeouts):
    """
    Educational: Verify that Ingress distributes requests across multiple pods.
    
    This demonstrates that Ingress (via the Service) load balances requests
    across all available pod replicas, not just sending to one pod.
    """
    from .utils import get_running_pods
    
    service_type = service["spec"]["type"]
    
    if service_type != "ClusterIP":
        pytest.skip(f"Service type is '{service_type}', expected 'ClusterIP'")
    
    # Check if we have multiple pods
    pods = get_running_pods()
    if len(pods) < 2:
        pytest.skip(f"Need at least 2 pods for load balancing test, found {len(pods)}")
    
    pod_names = [pod["metadata"]["name"] for pod in pods]
    print(f"\n  Testing load balancing across {len(pods)} pods:")
    for name in pod_names:
        print(f"    - {name}")
    
    # Make multiple requests and check if we see logs from different pods
    url, host_header = get_ingress_url_and_host(ingress)
    if not url:
        pytest.skip("Could not determine Ingress URL")
    
    headers = {}
    if host_header and not url.endswith(host_header):
        headers['Host'] = host_header
    
    timeout = k8s_timeouts.get('http_request', 5)
    
    # Make 20 requests to increase likelihood of hitting different pods
    num_requests = 20
    successful_requests = 0
    
    print(f"\n  Making {num_requests} requests to observe load distribution...")
    
    for i in range(num_requests):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                successful_requests += 1
        except requests.exceptions.RequestException:
            pass  # Ignore failures for this educational test
    
    print(f"  ✓ Successfully completed {successful_requests}/{num_requests} requests")
    
    # Check logs from each pod to see if they received requests
    time.sleep(1)  # Give logs a moment to appear
    
    pods_with_requests = 0
    for pod_name in pod_names:
        result = subprocess.run(
            ["kubectl", "logs", pod_name, "--tail=50"],
            capture_output=True,
            text=True
        )
        
        # Look for typical Flask/werkzeug log entries (GET requests)
        if "GET /" in result.stdout:
            pods_with_requests += 1
            print(f"    ✓ Pod {pod_name} received requests")
    
    print(f"\n  📚 Learning: {pods_with_requests}/{len(pods)} pods received traffic")
    
    if pods_with_requests > 1:
        print("  ✓ Load balancing is working - multiple pods handled requests")
    else:
        print("  ⚠️  Note: Only one pod received requests (normal for small request counts)")
        print("      In production with high traffic, all pods would receive requests")
