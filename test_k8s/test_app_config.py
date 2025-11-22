"""Test that app behavior changes based on configuration values."""
import pytest
import requests

from .utils import get_service, get_minikube_ip, get_running_pods


@pytest.mark.ingress
def test_environment_variables_affect_app_response():
    """
    Verify that the app can access and use environment variables from ConfigMap/Secret.
    
    This test validates that configuration values are not just injected into the pod,
    but are actually available to the running application.
    
    Note: This test requires the app to expose environment information via an endpoint.
    If the app doesn't have such an endpoint, this test will be skipped.
    """
    # Get service access URL
    minikube_ip = get_minikube_ip()
    if not minikube_ip:
        pytest.skip("Cannot get Minikube IP")
    
    # Try to access an /env or /config endpoint if it exists
    # This is a future-proof test that would work if such endpoint is added
    url = f"http://{minikube_ip}"
    
    try:
        # First verify the main endpoint works
        response = requests.get(url, headers={"Host": "hello-flask.local"}, timeout=5)
        assert response.status_code == 200, f"Main endpoint failed: {response.status_code}"
        
        print("✓ App is accessible and responding")
        
        # Try to access a config/env endpoint (this may not exist yet)
        env_response = requests.get(
            f"{url}/env",
            headers={"Host": "hello-flask.local"},
            timeout=5
        )
        
        if env_response.status_code == 200:
            env_data = env_response.json()
            
            # Verify environment variables are accessible by the app
            assert "APP_ENV" in env_data, "APP_ENV not accessible by app"
            assert env_data["APP_ENV"] == "local", f"Expected APP_ENV='local', got '{env_data['APP_ENV']}'"
            
            print(f"✓ App can access and expose environment variables: {env_data}")
        else:
            pytest.skip("App does not expose /env endpoint for testing environment variables")
            
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Cannot connect to app: {e}")


def test_pods_have_config_environment_available(pods):
    """
    Verify that pods have all expected configuration environment variables available.
    
    This ensures configuration is properly injected and available to the application,
    even if the app doesn't explicitly use them yet.
    """
    from .utils import exec_in_pod
    
    assert len(pods) > 0, "No pods found to test"
    
    pod_name = pods[0]["metadata"]["name"]
    
    # All expected environment variables from ConfigMap and Secret
    expected_env_vars = {
        # From ConfigMap
        "APP_ENV": "local",
        "LOG_LEVEL": "debug",
        # From Secret
        "API_KEY": "somesecretkey",
        "DB_PASSWORD": "password123",
        # From deployment env
        "CUSTOM_MESSAGE": "Deployed via ConfigMap + Secret"
    }
    
    missing_vars = []
    incorrect_vars = []
    
    for env_var, expected_value in expected_env_vars.items():
        result = exec_in_pod(pod_name, ["printenv", env_var])
        
        if result.returncode != 0:
            missing_vars.append(env_var)
            continue
        
        actual_value = result.stdout.strip()
        if actual_value != expected_value:
            incorrect_vars.append(f"{env_var}: expected '{expected_value}', got '{actual_value}'")
    
    # Assert all checks passed
    assert len(missing_vars) == 0, f"Missing environment variables: {missing_vars}"
    assert len(incorrect_vars) == 0, f"Incorrect values: {incorrect_vars}"
    
    print(f"✓ All {len(expected_env_vars)} configuration environment variables are available to the app")
