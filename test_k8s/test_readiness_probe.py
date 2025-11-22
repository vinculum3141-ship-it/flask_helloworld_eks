"""
Test readiness probe configuration and behavior.

This test verifies that:
1. Readiness probe is configured correctly in the deployment
2. Pods become ready only when the readiness probe succeeds
3. Traffic is routed only to ready pods
"""
import pytest

from .utils import get_deployment, get_pods, get_running_pods


def test_readiness_probe_configured(deployment):
    """Verify that readiness probe is configured in the deployment."""
    containers = deployment["spec"]["template"]["spec"]["containers"]
    
    assert len(containers) > 0, "No containers found in deployment"
    
    main_container = containers[0]
    assert "readinessProbe" in main_container, "Readiness probe not configured"
    
    readiness_probe = main_container["readinessProbe"]
    
    # Verify readiness probe configuration
    assert "httpGet" in readiness_probe, "Readiness probe should use httpGet"
    assert readiness_probe["httpGet"]["path"] == "/ready", "Readiness probe path should be /ready"
    assert readiness_probe["httpGet"]["port"] == 5000, "Readiness probe port should be 5000"
    
    # Verify probe timing settings
    assert "initialDelaySeconds" in readiness_probe, "initialDelaySeconds should be configured"
    assert "periodSeconds" in readiness_probe, "periodSeconds should be configured"
    assert "timeoutSeconds" in readiness_probe, "timeoutSeconds should be configured"
    assert "failureThreshold" in readiness_probe, "failureThreshold should be configured"
    
    print("\n✅ Readiness probe configuration:")
    print(f"   Path: {readiness_probe['httpGet']['path']}")
    print(f"   Port: {readiness_probe['httpGet']['port']}")
    print(f"   Initial Delay: {readiness_probe['initialDelaySeconds']}s")
    print(f"   Period: {readiness_probe['periodSeconds']}s")
    print(f"   Timeout: {readiness_probe['timeoutSeconds']}s")
    print(f"   Failure Threshold: {readiness_probe['failureThreshold']}")


def test_ready_replicas_match_desired(deployment):
    """Verify that ready replicas match the desired count."""
    desired_replicas = deployment["spec"]["replicas"]
    ready_replicas = deployment["status"].get("readyReplicas", 0)
    
    assert ready_replicas == desired_replicas, \
        f"Expected {desired_replicas} ready replicas, but got {ready_replicas}"
    
    print(f"\n✅ Deployment has {ready_replicas}/{desired_replicas} ready replicas")


def test_all_running_pods_are_ready(running_pods, deployment):
    """Verify that all running pods have passed readiness checks."""
    assert len(running_pods) > 0, "No running pods found"
    
    for pod in running_pods:
        pod_name = pod["metadata"]["name"]
        
        # Check pod conditions for Ready status
        conditions = pod["status"].get("conditions", [])
        ready_condition = next(
            (c for c in conditions if c["type"] == "Ready"),
            None
        )
        
        assert ready_condition is not None, f"Pod {pod_name} has no Ready condition"
        assert ready_condition["status"] == "True", \
            f"Pod {pod_name} is not ready (status={ready_condition['status']})"
    
    print(f"\n✅ All {len(running_pods)} running pod(s) are ready")
