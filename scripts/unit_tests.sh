#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Main execution
print_header "Python Unit Tests"
echo ""
run_pytest "app/tests/" "-v" "Testing Flask application logic independently of Kubernetes"
log_success "Unit tests completed!"
echo ""
