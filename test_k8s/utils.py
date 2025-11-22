"""
Shared utilities for Kubernetes testing.

This module provides common helper functions used across multiple test files
to reduce code duplication and improve maintainability.
"""
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple


class KubectlError(Exception):
    """Raised when a kubectl command fails."""
    pass


def run_kubectl(*args: str, check: bool = True, use_minikube: bool = False) -> subprocess.CompletedProcess:
    """
    Run a kubectl command and return the result.
    
    Args:
        *args: Arguments to pass to kubectl
        check: If True, raise KubectlError on non-zero exit code
        use_minikube: If True, use 'minikube kubectl --' instead of 'kubectl'
        
    Returns:
        CompletedProcess with stdout, stderr, and returncode
        
    Raises:
        KubectlError: If check=True and command fails
        
    Example:
        result = run_kubectl("get", "pods", "-o", "json")
        pods = json.loads(result.stdout)
    """
    if use_minikube:
        cmd = ["minikube", "kubectl", "--"] + list(args)
    else:
        cmd = ["kubectl"] + list(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if check and result.returncode != 0:
        raise KubectlError(
            f"kubectl command failed: {' '.join(args)}\n"
            f"Exit code: {result.returncode}\n"
            f"Stderr: {result.stderr}"
        )
    
    return result


def get_pods(label_selector: str = "app=hello-flask", namespace: str = "default") -> List[Dict[str, Any]]:
    """
    Get all pods matching the label selector.
    
    Args:
        label_selector: Kubernetes label selector (default: "app=hello-flask")
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        List of pod dictionaries from Kubernetes API
        
    Raises:
        KubectlError: If kubectl command fails
        
    Example:
        pods = get_pods()
        for pod in pods:
            print(pod['metadata']['name'])
    """
    result = run_kubectl(
        "get", "pods",
        "-l", label_selector,
        "-n", namespace,
        "-o", "json",
        check=True
    )
    
    data = json.loads(result.stdout)
    return data.get("items", [])


def get_pod_by_name(pod_name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get a specific pod by name.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Pod dictionary or None if not found
        
    Example:
        pod = get_pod_by_name("hello-flask-abc123")
        if pod:
            print(pod['status']['phase'])
    """
    result = run_kubectl(
        "get", "pod", pod_name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def get_pod_restart_count(pod_name: str, namespace: str = "default") -> Optional[int]:
    """
    Get the restart count for a specific pod's first container.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Restart count (int) or None if pod not found
        
    Example:
        restart_count = get_pod_restart_count("hello-flask-abc123")
        print(f"Pod has restarted {restart_count} times")
    """
    pod = get_pod_by_name(pod_name, namespace)
    if not pod:
        return None
    
    container_statuses = pod.get("status", {}).get("containerStatuses", [])
    if not container_statuses:
        return 0
    
    return container_statuses[0].get("restartCount", 0)


def get_running_pods(label_selector: str = "app=hello-flask", namespace: str = "default") -> List[Dict[str, Any]]:
    """
    Get all running and ready pods matching the label selector.
    Excludes pods that are being terminated.
    
    Args:
        label_selector: Kubernetes label selector (default: "app=hello-flask")
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        List of running and ready pod dictionaries (excluding terminating pods)
        
    Example:
        running_pods = get_running_pods()
        print(f"Found {len(running_pods)} running pods")
    """
    pods = get_pods(label_selector, namespace)
    
    running_pods = [
        pod for pod in pods
        if pod["status"]["phase"] == "Running" and
        all(cs.get("ready", False) for cs in pod["status"].get("containerStatuses", [])) and
        pod["metadata"].get("deletionTimestamp") is None  # Exclude terminating pods
    ]
    
    return running_pods


def wait_for_pods_ready(
    desired_count: int,
    label_selector: str = "app=hello-flask",
    namespace: str = "default",
    timeout: int = 60,
    poll_interval: int = 2
) -> bool:
    """
    Wait for a specific number of pods to be running and ready.
    
    Args:
        desired_count: Number of pods expected to be ready
        label_selector: Kubernetes label selector (default: "app=hello-flask")
        namespace: Kubernetes namespace (default: "default")
        timeout: Maximum time to wait in seconds (default: 60)
        poll_interval: Time between checks in seconds (default: 2)
        
    Returns:
        True if desired count reached, False if timeout
        
    Example:
        if wait_for_pods_ready(3, timeout=120):
            print("All 3 pods are ready!")
        else:
            print("Timeout waiting for pods")
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        running_pods = get_running_pods(label_selector, namespace)
        
        if len(running_pods) >= desired_count:
            return True
        
        time.sleep(poll_interval)
    
    return False


def get_deployment(name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get a deployment by name.
    
    Args:
        name: Name of the deployment
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Deployment dictionary or None if not found
        
    Example:
        deployment = get_deployment("hello-flask")
        replicas = deployment['spec']['replicas']
    """
    result = run_kubectl(
        "get", "deployment", name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def get_service(name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get a service by name.
    
    Args:
        name: Name of the service
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Service dictionary or None if not found
        
    Example:
        service = get_service("hello-flask")
        service_type = service['spec']['type']
    """
    result = run_kubectl(
        "get", "service", name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def get_ingress(name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get an ingress resource by name.
    
    Args:
        name: Name of the ingress
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Ingress dictionary or None if not found
        
    Example:
        ingress = get_ingress("hello-flask-ingress")
        if ingress:
            rules = ingress['spec']['rules']
    """
    result = run_kubectl(
        "get", "ingress", name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def is_ci_environment() -> bool:
    """
    Detect if running in CI/CD environment.
    
    Returns:
        True if running in CI/CD, False otherwise
        
    Example:
        if is_ci_environment():
            print("Running in CI/CD - adjusting timeouts")
    """
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'


def get_minikube_ip() -> Optional[str]:
    """
    Get the Minikube cluster IP address.
    
    Returns:
        IP address string or None if command fails
        
    Example:
        ip = get_minikube_ip()
        url = f"http://{ip}:30000"
    """
    result = subprocess.run(
        ["minikube", "ip"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    return result.stdout.strip()


def get_service_url(service_name: str, namespace: str = "default") -> Optional[str]:
    """
    Get the URL for a Minikube service (NodePort or LoadBalancer).
    
    Args:
        service_name: Name of the service
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Service URL or None if command fails
        
    Example:
        url = get_service_url("hello-flask")
        if url:
            response = requests.get(url)
    """
    result = subprocess.run(
        ["minikube", "service", service_name, "--url", "-n", namespace],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode != 0:
        return None
    
    return result.stdout.strip()


def exec_in_pod(pod_name: str, command: List[str], namespace: str = "default", check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a command inside a pod.
    
    Args:
        pod_name: Name of the pod
        command: Command to execute (as list)
        namespace: Kubernetes namespace (default: "default")
        check: If True, raise KubectlError on failure
        
    Returns:
        CompletedProcess with command output
        
    Raises:
        KubectlError: If check=True and command fails
        
    Example:
        result = exec_in_pod("hello-flask-abc123", ["printenv", "APP_ENV"])
        print(result.stdout)
    """
    args = ["exec", pod_name, "-n", namespace, "--"] + command
    return run_kubectl(*args, check=check)


def delete_pod(pod_name: str, namespace: str = "default", wait: bool = False) -> bool:
    """
    Delete a pod.
    
    Args:
        pod_name: Name of the pod to delete
        namespace: Kubernetes namespace (default: "default")
        wait: If True, wait for deletion to complete
        
    Returns:
        True if successful, False otherwise
        
    Example:
        if delete_pod("hello-flask-abc123"):
            print("Pod deleted successfully")
    """
    wait_arg = "true" if wait else "false"
    result = run_kubectl(
        "delete", "pod", pod_name,
        "-n", namespace,
        f"--wait={wait_arg}",
        check=False
    )
    
    return result.returncode == 0


def get_pod_logs(pod_name: str, namespace: str = "default", tail: Optional[int] = None) -> Optional[str]:
    """
    Get logs from a pod.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: "default")
        tail: If specified, only return last N lines
        
    Returns:
        Log output as string or None if command fails
        
    Example:
        logs = get_pod_logs("hello-flask-abc123", tail=50)
        print(logs)
    """
    args = ["logs", pod_name, "-n", namespace]
    if tail:
        args.extend(["--tail", str(tail)])
    
    result = run_kubectl(*args, check=False)
    
    if result.returncode != 0:
        return None
    
    return result.stdout


def print_debug_info(label_selector: str = "app=hello-flask", namespace: str = "default") -> None:
    """
    Print useful debugging information about pods and deployment.
    
    Args:
        label_selector: Kubernetes label selector (default: "app=hello-flask")
        namespace: Kubernetes namespace (default: "default")
        
    Example:
        print_debug_info()  # Prints current state of all hello-flask resources
    """
    print("\n" + "="*60)
    print("DEBUG INFORMATION")
    print("="*60)
    
    # Pods
    try:
        pods = get_pods(label_selector, namespace)
        print(f"\nPods ({len(pods)} total):")
        for pod in pods:
            name = pod['metadata']['name']
            phase = pod['status']['phase']
            restart_count = get_pod_restart_count(name, namespace) or 0
            print(f"  - {name}: {phase} (restarts: {restart_count})")
    except Exception as e:
        print(f"  Error getting pods: {e}")
    
    # Deployment
    try:
        deployment = get_deployment("hello-flask", namespace)
        if deployment:
            desired = deployment['spec']['replicas']
            ready = deployment['status'].get('readyReplicas', 0)
            print(f"\nDeployment: {ready}/{desired} replicas ready")
    except Exception as e:
        print(f"  Error getting deployment: {e}")
    
    # Service
    try:
        service = get_service("hello-flask", namespace)
        if service:
            svc_type = service['spec']['type']
            print(f"\nService: type={svc_type}")
    except Exception as e:
        print(f"  Error getting service: {e}")
    
    print("="*60 + "\n")


def get_configmap(name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get a ConfigMap by name.
    
    Args:
        name: Name of the ConfigMap
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        ConfigMap dictionary or None if not found
        
    Raises:
        KubectlError: If kubectl command fails for reasons other than not found
        
    Example:
        configmap = get_configmap("hello-config")
        if configmap:
            data = configmap.get("data", {})
            print(f"APP_ENV: {data.get('APP_ENV')}")
    """
    result = run_kubectl(
        "get", "configmap", name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def get_secret(name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
    """
    Get a Secret by name.
    
    Args:
        name: Name of the Secret
        namespace: Kubernetes namespace (default: "default")
        
    Returns:
        Secret dictionary or None if not found
        
    Raises:
        KubectlError: If kubectl command fails for reasons other than not found
        
    Example:
        secret = get_secret("hello-secrets")
        if secret:
            data = secret.get("data", {})
            # Note: Secret data is base64-encoded
            print(f"Keys: {list(data.keys())}")
    """
    result = run_kubectl(
        "get", "secret", name,
        "-n", namespace,
        "-o", "json",
        check=False
    )
    
    if result.returncode != 0:
        return None
    
    return json.loads(result.stdout)


def deployment_references_resource(deployment: Dict[str, Any], resource_type: str, resource_name: str) -> bool:
    """
    Check if a deployment references a ConfigMap or Secret via envFrom.
    
    Args:
        deployment: Deployment dictionary
        resource_type: Type of resource ("configmap" or "secret")
        resource_name: Name of the resource to check for
        
    Returns:
        True if deployment references the resource, False otherwise
        
    Example:
        deployment = get_deployment("hello-flask")
        if deployment_references_resource(deployment, "configmap", "hello-config"):
            print("Deployment references hello-config ConfigMap")
    """
    if not deployment:
        return False
    
    containers = deployment.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    if not containers:
        return False
    
    main_container = containers[0]
    env_from = main_container.get("envFrom", [])
    
    # Determine the reference key based on resource type
    if resource_type.lower() == "configmap":
        ref_key = "configMapRef"
    elif resource_type.lower() == "secret":
        ref_key = "secretRef"
    else:
        return False
    
    # Check if envFrom includes the resource reference
    for ref in env_from:
        if ref_key in ref and ref[ref_key].get("name") == resource_name:
            return True
    
    return False
