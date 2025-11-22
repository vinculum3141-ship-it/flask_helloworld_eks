"""Test ConfigMap integration with pods."""
import pytest

from .utils import exec_in_pod, deployment_references_resource


def test_configmap_exists(configmap, configmap_name):
    """Verify that the ConfigMap resource exists in the cluster."""
    assert configmap is not None, f"ConfigMap '{configmap_name}' does not exist in the cluster"
    assert configmap["kind"] == "ConfigMap", "Resource is not a ConfigMap"
    assert configmap["metadata"]["name"] == configmap_name, "ConfigMap has wrong name"
    
    print(f"✓ ConfigMap '{configmap_name}' exists")


def test_configmap_has_correct_keys(configmap):
    """Verify that the ConfigMap contains the expected keys and values."""
    data = configmap.get("data", {})
    
    # Check expected keys exist
    expected_keys = ["APP_ENV", "LOG_LEVEL"]
    for key in expected_keys:
        assert key in data, f"ConfigMap missing expected key: {key}"
    
    # Check expected values
    assert data["APP_ENV"] == "local", f"Expected APP_ENV='local', got '{data['APP_ENV']}'"
    assert data["LOG_LEVEL"] == "debug", f"Expected LOG_LEVEL='debug', got '{data['LOG_LEVEL']}'"
    
    print(f"✓ ConfigMap has correct keys and values: {data}")


def test_deployment_references_configmap(deployment, configmap_name):
    """Verify that the deployment references the ConfigMap correctly."""
    assert deployment_references_resource(deployment, "configmap", configmap_name), \
        f"Deployment does not reference ConfigMap '{configmap_name}' in envFrom"
    
    print(f"✓ Deployment correctly references ConfigMap '{configmap_name}'")


def test_configmap_applied(pods):
    """Verify that ConfigMap environment variables are applied to pods."""
    assert len(pods) > 0, "No pods found to test ConfigMap"
    
    pod_name = pods[0]["metadata"]["name"]
    
    # Execute printenv in the pod to check APP_ENV variable
    result = exec_in_pod(pod_name, ["printenv", "APP_ENV"])
    env_value = result.stdout.strip()
    
    assert env_value == "local", \
        f"Expected APP_ENV='local', got '{env_value}'"
    
    print(f"✓ ConfigMap applied: APP_ENV={env_value}")


def test_all_configmap_values_in_pods(pods):
    """Verify that all ConfigMap values are correctly injected into pods."""
    assert len(pods) > 0, "No pods found to test ConfigMap"
    
    pod_name = pods[0]["metadata"]["name"]
    
    # Test all expected environment variables
    expected_env_vars = {
        "APP_ENV": "local",
        "LOG_LEVEL": "debug"
    }
    
    for env_var, expected_value in expected_env_vars.items():
        result = exec_in_pod(pod_name, ["printenv", env_var])
        actual_value = result.stdout.strip()
        
        assert actual_value == expected_value, \
            f"Expected {env_var}='{expected_value}', got '{actual_value}'"
    
    print(f"✓ All ConfigMap values correctly injected into pods: {expected_env_vars}")

