#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Main execution
print_header "Kubernetes Integration Tests"
echo ""
run_pytest "test_k8s/" "-v -m 'not manual and not nodeport and not educational'" "Testing deployment, services, configmaps, ingress, liveness & readiness probes"
log_success "Kubernetes tests completed!"
log_note "Note: Manual, NodePort, and Educational tests excluded."
log_note "To run manual tests: pytest test_k8s/ -v -m manual"
log_note "To run NodePort tests: make health-tests (auto-switches service type)"
log_note "To run educational tests: make educational-tests"
echo ""
