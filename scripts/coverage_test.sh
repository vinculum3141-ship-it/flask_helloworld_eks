#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Default coverage type
COVERAGE_TYPE="${1:-terminal}"

# Main execution
print_header "Python Unit Tests with Coverage"
echo ""

case "$COVERAGE_TYPE" in
    terminal|term)
        log_info "Running tests with terminal coverage report..."
        echo ""
        run_pytest "app/tests/" "--cov=app --cov-report=term-missing -v" "Generating coverage report for terminal"
        ;;
    html)
        log_info "Running tests with HTML coverage report..."
        echo ""
        run_pytest "app/tests/" "--cov=app --cov-report=html --cov-report=term -v" "Generating HTML coverage report"
        log_success "Coverage report generated!"
        log_note "📊 Open ${BLUE}htmlcov/index.html${NC} in your browser to view the report"
        ;;
    xml)
        log_info "Running tests with XML coverage report (for CI/CD)..."
        echo ""
        run_pytest "app/tests/" "--cov=app --cov-report=xml --cov-report=term -v" "Generating XML coverage report"
        log_success "Coverage report generated!"
        log_note "📊 XML report saved to ${BLUE}coverage.xml${NC}"
        ;;
    all)
        log_info "Running tests with all coverage report formats..."
        echo ""
        run_pytest "app/tests/" "--cov=app --cov-report=term-missing --cov-report=html --cov-report=xml -v" "Generating all coverage formats"
        log_success "All coverage reports generated!"
        echo ""
        log_note "📊 Coverage reports:"
        log_note "   - Terminal: Displayed above"
        log_note "   - HTML: ${BLUE}htmlcov/index.html${NC}"
        log_note "   - XML: ${BLUE}coverage.xml${NC}"
        ;;
    *)
        log_error "Invalid coverage type: $COVERAGE_TYPE"
        echo ""
        echo "Usage: $0 [terminal|html|xml|all]"
        echo ""
        echo "  terminal (default) - Display coverage in terminal with missing lines"
        echo "  html              - Generate HTML coverage report"
        echo "  xml               - Generate XML coverage report (for CI/CD)"
        echo "  all               - Generate all report formats"
        exit 1
        ;;
esac

log_success "Coverage analysis completed!"
echo ""
