#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Function definitions
run_automated_tests() {
    echo ""
    log_info "Running automated liveness probe configuration tests..."
    log_note "(Behavioral tests available in test_crash_recovery_manual.py)"
    echo ""
    run_pytest "test_k8s/test_liveness_probe.py" "-v -s"
}

run_manual_tests() {
    echo ""
    log_info "Running manual self-healing tests..."
    log_note "(These tests involve timing and may take 60-90 seconds)"
    echo ""
    run_pytest "test_k8s/" "-v -s -m manual"
}

run_config_only() {
    echo ""
    log_info "Running liveness probe configuration check only..."
    echo ""
    run_pytest "test_k8s/test_liveness_probe.py::test_liveness_probe_configured" "-v -s"
}

show_help() {
    echo "Usage: bash scripts/liveness_test.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no option)  Run automated configuration tests (default, fast)"
    echo "  --manual     Run manual behavioral/timing tests (pod deletion, crash recovery)"
    echo "  --config     Run only the liveness probe configuration check"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash scripts/liveness_test.sh           # Automated config tests"
    echo "  bash scripts/liveness_test.sh --manual  # Manual behavioral tests"
    echo "  bash scripts/liveness_test.sh --config  # Configuration check only"
}

# Main execution
print_header "Liveness Probe Configuration Tests"

case "${1:-}" in
    --manual)
        run_manual_tests
        ;;
    --config)
        run_config_only
        ;;
    --help|-h)
        show_help
        ;;
    "")
        run_automated_tests
        ;;
    *)
        log_warning "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

log_success "Tests completed!"
echo ""
