"""Test deployment and pod status."""
import pytest

from .utils import get_pods


def test_pods_running(running_pods, deployment):
    """Check that deployment has running pods."""
    assert len(running_pods) > 0, "No running pods found"
    
    desired_replicas = deployment['spec']['replicas']
    
    # Verify we have the desired number of running pods
    assert len(running_pods) == desired_replicas, \
        f"Expected {desired_replicas} running pods, but found {len(running_pods)}"
    
    # Double-check all pods are actually in Running state
    for pod in running_pods:
        pod_name = pod["metadata"]["name"]
        status = pod["status"]["phase"]
        
        assert status == "Running", \
            f"Pod {pod_name} not running (status={status})"
    
    print(f"✓ All {len(running_pods)} pod(s) are running (matches desired replicas: {desired_replicas})")
