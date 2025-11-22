#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Health Endpoint Testing Script
# Temporarily switches service to NodePort, runs health endpoint tests, then restores ClusterIP

print_header "Health Endpoint Tests (Development)"
echo ""

# Check if deployment exists
if ! kubectl get deployment hello-flask &>/dev/null; then
    log_error "Deployment 'hello-flask' not found. Please deploy first with 'make deploy'"
    exit 1
fi

# Save original service configuration
log_info "Backing up current service configuration..."
kubectl get service hello-flask -o yaml > /tmp/hello-flask-service-backup.yaml

# Function to restore service
restore_service() {
    log_info "Restoring original service configuration..."
    # Simply patch back to ClusterIP (simpler than full restore)
    kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}' > /dev/null 2>&1 || true
    rm -f /tmp/hello-flask-service-backup.yaml
    
    # Wait for service to stabilize after type change
    log_info "Waiting for service to stabilize..."
    sleep 5
    
    # Ensure all pods are ready after any restarts during tests
    kubectl wait --for=condition=ready pod -l app=hello-flask --timeout=60s > /dev/null 2>&1 || true
    
    # Additional wait for ingress to fully recognize the service change
    log_info "Allowing time for ingress controller to update..."
    sleep 3
    
    log_success "Service restored to ClusterIP"
}

# Set trap to restore service on exit
trap restore_service EXIT

# Switch to NodePort temporarily
log_info "Temporarily switching service to NodePort for testing..."
kubectl patch service hello-flask -p '{"spec":{"type":"NodePort"}}' > /dev/null

# Wait a moment for service to update
sleep 2

# Get NodePort URL
log_info "Getting service URL..."
SERVICE_URL=$(minikube service hello-flask --url 2>/dev/null)
if [ -z "$SERVICE_URL" ]; then
    log_error "Failed to get service URL"
    exit 1
fi

log_success "Service available at: $SERVICE_URL"
echo ""

# Run health endpoint tests
log_info "Running health endpoint tests..."
echo ""
run_pytest "test_k8s/test_health_endpoint.py" "-v -m nodeport" "Testing /health endpoint functionality (NodePort tests only)"

echo ""
log_success "Health endpoint tests completed!"
log_note "Service will be automatically restored to ClusterIP"
echo ""
