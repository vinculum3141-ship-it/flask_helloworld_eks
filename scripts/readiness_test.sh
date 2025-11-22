#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Function definitions
run_automated_tests() {
    echo ""
    log_info "Running automated readiness probe configuration tests..."
    log_note "(Behavioral tests may be added for traffic routing validation)"
    echo ""
    run_pytest "test_k8s/test_readiness_probe.py" "-v -s"
}

run_manual_tests() {
    echo ""
    log_info "Running manual readiness probe tests..."
    log_note "(These tests may involve timing and traffic routing validation)"
    echo ""
    
    # Use run_pytest_optional to handle exit code 5 (no tests collected)
    run_pytest_optional \
        "test_k8s/" \
        "-v -s -m manual -k readiness" \
        "" \
        "No manual readiness tests found yet. Manual tests are planned for future implementation (traffic routing, pod readiness validation)."
}

run_config_only() {
    echo ""
    log_info "Running readiness probe configuration check only..."
    echo ""
    run_pytest "test_k8s/test_readiness_probe.py::test_readiness_probe_configured" "-v -s"
}

show_help() {
    echo "Usage: bash scripts/readiness_test.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no option)  Run automated configuration tests (default, fast)"
    echo "  --manual     Run manual behavioral/timing tests (traffic routing, pod readiness)"
    echo "  --config     Run only the readiness probe configuration check"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash scripts/readiness_test.sh           # Automated config tests"
    echo "  bash scripts/readiness_test.sh --manual  # Manual behavioral tests"
    echo "  bash scripts/readiness_test.sh --config  # Configuration check only"
}

# Main execution
print_header "Readiness Probe Configuration Tests"

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
