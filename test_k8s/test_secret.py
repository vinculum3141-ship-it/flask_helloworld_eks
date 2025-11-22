"""Test Secret integration with pods."""
import base64
import pytest

from .utils import exec_in_pod, deployment_references_resource


def test_secret_exists(secret, secret_name):
    """Verify that the Secret resource exists in the cluster."""
    assert secret is not None, f"Secret '{secret_name}' does not exist in the cluster"
    assert secret["kind"] == "Secret", "Resource is not a Secret"
    assert secret["metadata"]["name"] == secret_name, "Secret has wrong name"
    assert secret["type"] == "Opaque", "Secret should be of type Opaque"
    
    print(f"✓ Secret '{secret_name}' exists")


def test_secret_has_correct_keys(secret):
    """Verify that the Secret contains the expected keys."""
    data = secret.get("data", {})
    
    # Check expected keys exist
    expected_keys = ["API_KEY", "DB_PASSWORD"]
    for key in expected_keys:
        assert key in data, f"Secret missing expected key: {key}"
    
    print(f"✓ Secret has correct keys: {list(data.keys())}")


def test_secret_values_are_base64_encoded(secret):
    """Verify that Secret values are properly base64-encoded."""
    data = secret.get("data", {})
    
    # Test each value can be decoded from base64
    expected_decoded_values = {
        "API_KEY": "somesecretkey",
        "DB_PASSWORD": "password123"
    }
    
    for key, expected_decoded in expected_decoded_values.items():
        assert key in data, f"Secret missing key: {key}"
        
        encoded_value = data[key]
        
        # Verify it's valid base64
        try:
            decoded_value = base64.b64decode(encoded_value).decode('utf-8')
        except Exception as e:
            pytest.fail(f"Failed to decode {key} from base64: {e}")
        
        # Verify decoded value matches expected
        assert decoded_value == expected_decoded, \
            f"Expected {key} to decode to '{expected_decoded}', got '{decoded_value}'"
    
    print(f"✓ All Secret values are correctly base64-encoded")


def test_deployment_references_secret(deployment, secret_name):
    """Verify that the deployment references the Secret correctly."""
    assert deployment_references_resource(deployment, "secret", secret_name), \
        f"Deployment does not reference Secret '{secret_name}' in envFrom"
    
    print(f"✓ Deployment correctly references Secret '{secret_name}'")


def test_secret_applied(running_pods):
    """Verify that Secret environment variables are applied to pods."""
    assert len(running_pods) > 0, "No running pods found to test Secret"
    
    pod_name = running_pods[0]["metadata"]["name"]
    
    # Execute printenv in the pod to check API_KEY variable
    result = exec_in_pod(pod_name, ["printenv", "API_KEY"])
    env_value = result.stdout.strip()
    
    # The value in the pod should be decoded (not base64)
    assert env_value == "somesecretkey", \
        f"Expected API_KEY='somesecretkey', got '{env_value}'"
    
    print(f"✓ Secret applied: API_KEY={env_value}")


def test_all_secret_values_in_pods(running_pods):
    """Verify that all Secret values are correctly injected into pods (decoded)."""
    assert len(running_pods) > 0, "No running pods found to test Secret"
    
    pod_name = running_pods[0]["metadata"]["name"]
    
    # Test all expected environment variables (should be decoded in pod)
    expected_env_vars = {
        "API_KEY": "somesecretkey",
        "DB_PASSWORD": "password123"
    }
    
    for env_var, expected_value in expected_env_vars.items():
        result = exec_in_pod(pod_name, ["printenv", env_var])
        actual_value = result.stdout.strip()
        
        assert actual_value == expected_value, \
            f"Expected {env_var}='{expected_value}', got '{actual_value}'"
    
    print(f"✓ All Secret values correctly injected into pods (decoded): {list(expected_env_vars.keys())}")
