#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Cleanup function
cleanup_app() {
    echo ""
    log_info "Deleting Ingress..."
    minikube kubectl -- delete -f k8s/ingress.yaml --ignore-not-found
    
    log_info "Deleting Service..."
    minikube kubectl -- delete -f k8s/service.yaml --ignore-not-found
    
    log_info "Deleting Deployment..."
    minikube kubectl -- delete -f k8s/deployment.yaml --ignore-not-found
    
    log_info "Deleting ConfigMap..."
    minikube kubectl -- delete -f k8s/configmap.yaml --ignore-not-found
    
    log_info "Deleting Secret..."
    minikube kubectl -- delete -f k8s/secret.yaml --ignore-not-found

    log_info "Cleanup complete."
}

# Main execution
print_header "Cleaning Up Deployment"
cleanup_app
log_success "All resources deleted!"
log_note "Minikube cluster is still running. Use 'minikube stop' to shut it down."
echo ""
