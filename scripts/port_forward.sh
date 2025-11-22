#!/bin/bash
# -----------------------------------------------------------------------------
# Manual helper: Port-forward the hello-flask Kubernetes service for a quick
# local check. Works with both NodePort and ClusterIP services.
#
# CI coverage: Service reachability is validated in pytest via
#   test_k8s/test_service_nodeport.py (NodePort service type)
#   test_k8s/test_service_ingress.py (ClusterIP with Ingress)
#
# Requirements:
# - Minikube is running and configured (uses `minikube kubectl -- ...`).
# - Service `svc/hello-flask` exists in the default namespace.
#
# Behavior:
# - Starts `kubectl port-forward` (5000:5000) in the background,
#   waits briefly, curls http://localhost:5000, then kills the forward.
# - Curl failures are logged but do not cause a non-zero exit code.
#
# Usage:
#   bash scripts/port_forward.sh
#
# Note: For an interactive tunnel, run the port-forward manually and stop with
# Ctrl+C:
#   kubectl port-forward svc/hello-flask 5000:5000
# -----------------------------------------------------------------------------
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

port_forward_app() {
    log_info "Checking service type..."
    SERVICE_TYPE=$(kubectl get svc hello-flask -o jsonpath='{.spec.type}' 2>/dev/null || echo "NotFound")
    
    if [ "$SERVICE_TYPE" = "NotFound" ]; then
        echo "[ERROR] Service 'hello-flask' not found. Please deploy it first."
        exit 1
    fi
    
    echo "[INFO] Service type: $SERVICE_TYPE"
    
    echo "[INFO] Forwarding port 5000 from hello-flask service to localhost..."
    echo "[INFO] Starting port forward in background..."
    kubectl port-forward svc/hello-flask 5000:5000 &
    PORT_FORWARD_PID=$!

    echo "[INFO] Port forward PID: $PORT_FORWARD_PID"
    echo "[INFO] Waiting 3 seconds for port forward to establish..."
    sleep 3

    echo "[INFO] Testing the service..."
    if curl -s http://localhost:5000; then
        echo ""
        echo "[SUCCESS] Service is responding!"
    else
        echo "[ERROR] Curl failed"
    fi

    echo "[INFO] Killing port forward process..."
    kill $PORT_FORWARD_PID || true

    echo "[INFO] Done!"
    echo ""
    echo "Note: Port-forward works with both NodePort and ClusterIP services."
    if [ "$SERVICE_TYPE" = "ClusterIP" ]; then
        echo "Detected ClusterIP service. You can also access via Ingress if configured."
    fi
}

# Run function
port_forward_app
