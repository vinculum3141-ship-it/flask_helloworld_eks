"""
Pytest configuration and fixtures for Kubernetes tests.

This module provides shared fixtures and configuration for all tests
in the test_k8s directory.
"""
import pytest
import time
from typing import Dict, Any, List

from .utils import (
    get_pods,
    get_running_pods,
    get_deployment,
    get_service,
    get_ingress,
    is_ci_environment,
    print_debug_info,
    KubectlError
)


def pytest_configure(config):
    """Configure custom markers for test organization."""
    config.addinivalue_line(
        "markers", 
        "manual: marks tests as manual (not run in automated CI/CD)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (may take longer than usual)"
    )
    config.addinivalue_line(
        "markers",
        "ingress: marks tests that require Ingress controller"
    )
    config.addinivalue_line(
        "markers",
        "nodeport: marks tests that require NodePort service type"
    )


@pytest.fixture(scope="session")
def ci_environment() -> bool:
    """
    Fixture that detects if tests are running in CI/CD environment.
    
    Returns:
        True if running in CI/CD, False otherwise
        
    Example:
        def test_something(ci_environment):
            if ci_environment:
                timeout = 120  # Longer timeout in CI
            else:
                timeout = 30
    """
    return is_ci_environment()


@pytest.fixture(scope="session")
def deployment_name() -> str:
    """
    Fixture that provides the deployment name.
    
    Returns:
        Name of the hello-flask deployment
    """
    return "hello-flask"


@pytest.fixture(scope="session")
def service_name() -> str:
    """
    Fixture that provides the service name.
    
    Returns:
        Name of the hello-flask service
    """
    return "hello-flask"


@pytest.fixture(scope="session")
def ingress_name() -> str:
    """
    Fixture that provides the ingress name.
    
    Returns:
        Name of the hello-flask ingress
    """
    return "hello-flask-ingress"


@pytest.fixture(scope="session")
def configmap_name() -> str:
    """
    Fixture that provides the ConfigMap name.
    
    Returns:
        Name of the hello-flask ConfigMap
    """
    return "hello-config"


@pytest.fixture(scope="session")
def secret_name() -> str:
    """
    Fixture that provides the Secret name.
    
    Returns:
        Name of the hello-flask Secret
    """
    return "hello-secrets"



@pytest.fixture(scope="session")
def label_selector() -> str:
    """
    Fixture that provides the label selector for hello-flask pods.
    
    Returns:
        Kubernetes label selector string
    """
    return "app=hello-flask"


@pytest.fixture(scope="function")
def pods(label_selector) -> List[Dict[str, Any]]:
    """
    Fixture that provides current list of pods.
    
    Returns:
        List of pod dictionaries
        
    Example:
        def test_pods_exist(pods):
            assert len(pods) > 0, "No pods found"
    """
    return get_pods(label_selector)


@pytest.fixture(scope="function")
def running_pods(label_selector) -> List[Dict[str, Any]]:
    """
    Fixture that provides list of running and ready pods.
    
    Returns:
        List of running pod dictionaries
        
    Example:
        def test_all_pods_running(running_pods, deployment):
            desired = deployment['spec']['replicas']
            assert len(running_pods) == desired
    """
    return get_running_pods(label_selector)


@pytest.fixture(scope="function")
def deployment(deployment_name) -> Dict[str, Any]:
    """
    Fixture that provides the deployment object.
    
    Returns:
        Deployment dictionary
        
    Raises:
        pytest.skip: If deployment not found
        
    Example:
        def test_replicas(deployment):
            replicas = deployment['spec']['replicas']
            assert replicas >= 2
    """
    dep = get_deployment(deployment_name)
    if not dep:
        pytest.skip(f"Deployment '{deployment_name}' not found")
    return dep


@pytest.fixture(scope="function")
def configmap(configmap_name):
    """
    Fixture that provides the ConfigMap object.
    
    Returns:
        ConfigMap dictionary
        
    Raises:
        pytest.skip: If ConfigMap not found
        
    Example:
        def test_configmap_data(configmap):
            data = configmap.get('data', {})
            assert 'APP_ENV' in data
    """
    from .utils import get_configmap
    cm = get_configmap(configmap_name)
    if not cm:
        pytest.skip(f"ConfigMap '{configmap_name}' not found")
    return cm


@pytest.fixture(scope="function")
def secret(secret_name):
    """
    Fixture that provides the Secret object.
    
    Returns:
        Secret dictionary
        
    Raises:
        pytest.skip: If Secret not found
        
    Example:
        def test_secret_data(secret):
            data = secret.get('data', {})
            assert 'API_KEY' in data
    """
    from .utils import get_secret
    sec = get_secret(secret_name)
    if not sec:
        pytest.skip(f"Secret '{secret_name}' not found")
    return sec

@pytest.fixture(scope="function")
def service(service_name) -> Dict[str, Any]:
    """
    Fixture that provides the service object.
    
    Returns:
        Service dictionary
        
    Raises:
        pytest.skip: If service not found
        
    Example:
        def test_service_type(service):
            assert service['spec']['type'] in ['ClusterIP', 'NodePort']
    """
    svc = get_service(service_name)
    if not svc:
        pytest.skip(f"Service '{service_name}' not found")
    return svc


@pytest.fixture(scope="function")
def ingress(ingress_name) -> Dict[str, Any]:
    """
    Fixture that provides the ingress object.
    
    Returns:
        Ingress dictionary
        
    Raises:
        pytest.skip: If ingress not found
        
    Example:
        def test_ingress_rules(ingress):
            rules = ingress['spec']['rules']
            assert len(rules) > 0
    """
    ing = get_ingress(ingress_name)
    if not ing:
        pytest.skip(f"Ingress '{ingress_name}' not found")
    return ing


@pytest.fixture(scope="function", autouse=False)
def debug_on_failure(request, label_selector):
    """
    Fixture that prints debug information when a test fails.
    
    Use by adding to test function parameters:
        def test_something(debug_on_failure):
            ...
    
    Or enable for all tests in a module by adding at top:
        pytestmark = pytest.mark.usefixtures("debug_on_failure")
    """
    yield
    
    if request.node.rep_call.failed:
        print("\n" + "!" * 60)
        print("TEST FAILED - Printing debug information")
        print("!" * 60)
        print_debug_info(label_selector)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to make test results available to fixtures.
    
    This allows the debug_on_failure fixture to know if a test failed.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def wait_for_stable_state(label_selector):
    """
    Fixture that provides a function to wait for pods to reach stable state.
    
    Returns:
        Function that waits for pods to stabilize
        
    Example:
        def test_after_changes(wait_for_stable_state):
            # Make some changes...
            wait_for_stable_state(desired_count=3, timeout=60)
            # Verify state...
    """
    def wait(desired_count: int, timeout: int = 60, poll_interval: int = 2) -> bool:
        """Wait for desired number of pods to be running and ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            running = get_running_pods(label_selector)
            if len(running) >= desired_count:
                # Wait a bit more to ensure stability
                time.sleep(poll_interval)
                running_check = get_running_pods(label_selector)
                if len(running_check) >= desired_count:
                    return True
            
            time.sleep(poll_interval)
        
        return False
    
    return wait


@pytest.fixture(scope="session")
def k8s_timeouts(ci_environment) -> Dict[str, int]:
    """
    Fixture that provides appropriate timeouts based on environment.
    
    Returns:
        Dictionary of timeout values in seconds
        
    Example:
        def test_something(k8s_timeouts):
            timeout = k8s_timeouts['pod_ready']
            # Use timeout for waiting...
    """
    if ci_environment:
        return {
            'pod_ready': 120,      # Time for pod to become ready
            'pod_delete': 60,      # Time for pod deletion
            'deployment_ready': 180,  # Time for deployment rollout
            'service_ready': 60,   # Time for service endpoint
            'ingress_ready': 120,  # Time for ingress address assignment
            'http_request': 10,    # HTTP request timeout
        }
    else:
        return {
            'pod_ready': 60,
            'pod_delete': 30,
            'deployment_ready': 90,
            'service_ready': 30,
            'ingress_ready': 60,
            'http_request': 5,
        }
