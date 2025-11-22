import subprocess
import requests
import time
import json
import os

def is_ci_environment():
    """Detect if running in CI/CD environment."""
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

def get_service_type():
    """Determine if service is NodePort or ClusterIP."""
    result = subprocess.run(
        ["kubectl", "get", "svc", "hello-flask", "-o", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    
    svc_data = json.loads(result.stdout)
    return svc_data.get("spec", {}).get("type", "ClusterIP")

def get_nodeport_url():
    """Get service URL for NodePort service type."""
    url = ""
    for i in range(5):
        proc = subprocess.run(
            ["minikube", "service", "hello-flask", "--url"],
            capture_output=True, text=True
        )
        url = proc.stdout.strip()
        if url:
            break
        time.sleep(1)
    return url

def get_ingress_url():
    """Get URL from Ingress resource.
    
    In CI/CD environments, uses Minikube IP directly.
    In local development, uses the ingress hostname.
    
    Returns tuple: (url, host_header) where host_header is the Host header to use
    """
    # Check if ingress exists
    result = subprocess.run(
        ["kubectl", "get", "ingress", "hello-flask-ingress", "-o", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None, None
    
    ingress_data = json.loads(result.stdout)
    rules = ingress_data.get("spec", {}).get("rules", [])
    if not rules:
        return None, None
    
    # Get the configured hostname from ingress rules
    ingress_host = rules[0].get("host", "hello-flask.local")
    
    # In CI/CD: Use Minikube IP instead of hostname (DNS won't resolve)
    if is_ci_environment():
        print("Detected CI environment - using Minikube IP instead of hostname")
        minikube_ip_result = subprocess.run(
            ["minikube", "ip"],
            capture_output=True, text=True
        )
        minikube_ip = minikube_ip_result.stdout.strip()
        
        if minikube_ip:
            print(f"Using Minikube IP: {minikube_ip} with Host header: {ingress_host}")
            # Return IP-based URL but also return the host header to use
            return f"http://{minikube_ip}", ingress_host
        else:
            print("Warning: Could not get Minikube IP, falling back to hostname")
    
    # Local development: Use the ingress hostname
    print(f"Using Ingress hostname: {ingress_host}")
    return f"http://{ingress_host}", ingress_host

def test_service_reachable():
    """Ensure the exposed service URL is responding.
    
    This test supports both NodePort and ClusterIP (with Ingress) service types.
    - For NodePort: Uses 'minikube service hello-flask --url'
    - For ClusterIP with Ingress: Uses the Ingress host (e.g., http://hello-flask.local)
    """
    service_type = get_service_type()
    assert service_type, "Could not determine service type. Is the service deployed?"
    
    print(f"Detected service type: {service_type}")
    
    url = None
    headers = {}
    
    if service_type == "NodePort":
        # Test NodePort access
        url = get_nodeport_url()
        assert url, (
            "minikube returned an empty URL for service 'hello-flask'. "
            "Is the service deployed with type NodePort?"
        )
        assert url.startswith(("http://", "https://")), f"Service URL does not include scheme: {url!r}"
        
    elif service_type == "ClusterIP":
        # Test Ingress access
        url, host_header = get_ingress_url()
        assert url, (
            "No Ingress found for service 'hello-flask'. "
            "For ClusterIP services, you need to deploy an Ingress resource. "
            "Either deploy k8s/ingress.yaml or change service type to NodePort."
        )
        print(f"Testing via Ingress: {url}")
        
        # When using IP address (CI/CD), we need to send the Host header
        # for nginx ingress to route the request correctly
        if host_header and not url.endswith(host_header):
            headers['Host'] = host_header
            print(f"Setting Host header: {host_header}")
        
    else:
        raise AssertionError(f"Unsupported service type: {service_type}")
    
    # Test the URL
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        assert resp.status_code == 200, f"Unexpected status {resp.status_code} from {url}"
        assert "Hello" in resp.text, f"Expected 'Hello' in response from {url}"
        print(f"✓ Service is reachable at {url}")
    except requests.exceptions.RequestException as e:
        raise AssertionError(
            f"Failed to reach service at {url}. "
            f"Error: {e}. "
            f"If using Ingress, ensure: 1) Ingress controller is running, "
            f"2) /etc/hosts is configured, 3) Ingress resource is deployed."
        )
