#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Main execution
print_header "Running Smoke Tests"
echo ""
log_info "Running smoke tests to verify deployment..."
log_note "This includes: deployment, configmap, service access, liveness & readiness probe configuration"
echo ""

# Run all K8s tests except manual tests (fast configuration checks only)
# Timing-dependent behavioral tests are excluded via @pytest.mark.manual
# NodePort tests are excluded since service is ClusterIP by default
run_pytest "test_k8s/" "-v -m 'not manual and not nodeport'"

log_success "Smoke tests completed successfully!"
log_note "Note: Manual and NodePort tests excluded."
log_note "To run manual tests: pytest test_k8s/ -v -m manual"
log_note "To run NodePort tests: pytest test_k8s/ -v -m nodeport"
echo ""