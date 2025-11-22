"""Test Ingress resource configuration and status."""
import time
import pytest

from .utils import get_ingress, run_kubectl


@pytest.mark.ingress
def test_ingress_exists(ingress):
    """Check that Ingress resource exists."""
    ingress_name = ingress.get("metadata", {}).get("name")
    assert ingress_name == "hello-flask-ingress", \
        f"Expected ingress 'hello-flask-ingress', got '{ingress_name}'"
    
    print("✓ Ingress resource 'hello-flask-ingress' exists")


@pytest.mark.ingress
def test_ingress_has_rules(ingress, service_name):
    """Check that Ingress has proper routing rules."""
    rules = ingress.get("spec", {}).get("rules", [])
    
    assert len(rules) > 0, "Ingress has no rules defined"
    
    # Check first rule has a host
    first_rule = rules[0]
    assert "host" in first_rule, "Ingress rule missing host"
    
    # Check rule has http paths
    paths = first_rule.get("http", {}).get("paths", [])
    assert len(paths) > 0, "Ingress rule has no paths"
    
    # Check path points to hello-flask service
    backend = paths[0].get("backend", {})
    backend_service_name = backend.get("service", {}).get("name")
    
    assert backend_service_name == service_name, \
        f"Expected service '{service_name}', got '{backend_service_name}'"
    
    print(f"✓ Ingress routes {first_rule.get('host')} → {service_name} service")


@pytest.mark.ingress
def test_ingress_has_address(ingress_name, k8s_timeouts):
    """
    Check that Ingress has been assigned an address.
    
    This indicates the Ingress controller is working and has processed the resource.
    """
    # Wait up to timeout for address to be assigned
    max_wait = k8s_timeouts.get('ingress_ready', 60)
    
    for i in range(max_wait):
        ing = get_ingress(ingress_name)
        
        if not ing:
            time.sleep(1)
            continue
        
        # Check for address in status
        load_balancer = ing.get("status", {}).get("loadBalancer", {})
        ingress_list = load_balancer.get("ingress", [])
        
        if ingress_list and len(ingress_list) > 0:
            address = ingress_list[0].get("ip") or ingress_list[0].get("hostname")
            if address:
                print(f"✓ Ingress has address: {address}")
                return
        
        if i < max_wait - 1:
            time.sleep(1)
    
    # If we get here, no address was assigned
    pytest.fail(
        f"Ingress has no address assigned after {max_wait} seconds. "
        f"This may indicate the Ingress controller is not running. "
        f"For Minikube, run: minikube addons enable ingress"
    )


@pytest.mark.ingress
def test_ingress_class(ingress):
    """Verify Ingress has the correct ingress class annotation."""
    annotations = ingress.get("metadata", {}).get("annotations", {})
    
    ingress_class = (
        annotations.get("kubernetes.io/ingress.class") or
        ingress.get("spec", {}).get("ingressClassName")
    )
    
    assert ingress_class == "nginx", \
        f"Unexpected ingress class: {ingress_class}. Expected 'nginx' for Minikube"
    
    print(f"✓ Ingress class: {ingress_class}")
