#!/bin/bash
# Common utilities for all scripts
# Source this file in other scripts: source "$(dirname "$0")/lib/common.sh"

# ==================== Color Definitions ====================
# ANSI color codes for terminal output
export GREEN='\033[0;32m'
export BLUE='\033[0;34m'
export YELLOW='\033[1;33m'
export RED='\033[0;31m'
export NC='\033[0m' # No Color

# ==================== Debug Mode ====================

# Enable debug mode if DEBUG or VERBOSE environment variable is set
# Usage: Call this function after sourcing common.sh
# Example: DEBUG=1 bash scripts/liveness_test.sh
enable_debug_mode() {
    if [[ "${DEBUG:-0}" == "1" ]] || [[ "${VERBOSE:-0}" == "1" ]]; then
        set -x
        log_info "Debug mode enabled (set -x active)"
        echo ""
    fi
}

# ==================== Logging Functions ====================

# Print a blue header with border
# Usage: print_header "Title Text"
print_header() {
    local title="$1"
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  ${title}${NC}"
    echo -e "${BLUE}================================================${NC}"
}

# Print an info message in green with [INFO] prefix
# Usage: log_info "Processing started..."
log_info() {
    echo -e "${GREEN}[INFO] $*${NC}"
}

# Print a success message in green with checkmark
# Usage: log_success "Operation completed!"
log_success() {
    echo -e "\n${GREEN}✅ $*${NC}"
}

# Print a warning message in yellow with [WARNING] prefix
# Usage: log_warning "This might take a while..."
log_warning() {
    echo -e "${YELLOW}[WARNING] $*${NC}"
}

# Print an error message in red with [ERROR] prefix
# Usage: log_error "Failed to connect"
log_error() {
    echo -e "${RED}[ERROR] $*${NC}" >&2
}

# Print a note/tip in yellow
# Usage: log_note "Tip: Use --help for more options"
log_note() {
    echo -e "${YELLOW}$*${NC}"
}

# ==================== Pytest Helpers ====================

# Run pytest with consistent formatting and error handling
# Usage: run_pytest "test_k8s/" "-v -s"
# Usage: run_pytest "app/tests/" "-v" "Testing Flask application"
run_pytest() {
    local test_path="${1:-test_k8s/}"
    local pytest_args="${2:--v}"
    local description="${3:-}"
    
    if [ -n "$description" ]; then
        log_note "$description"
        echo ""
    fi
    
    # Convert pytest_args string to array for proper argument handling
    # This preserves quoted strings within the arguments
    local -a args_array
    eval "args_array=($pytest_args)"
    
    # Run pytest with arguments properly expanded
    if pytest "$test_path" "${args_array[@]}"; then
        return 0
    else
        local exit_code=$?
        log_error "Pytest failed with exit code $exit_code"
        return $exit_code
    fi
}

# ==================== Validation Helpers ====================

# Check if a command exists
# Usage: command_exists "kubectl" || { log_error "kubectl not found"; exit 1; }
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in a git repository
# Usage: check_git_repo
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository"
        return 1
    fi
    return 0
}

# ==================== Script Initialization ====================

# Get the absolute path to the scripts directory
# Usage: SCRIPTS_DIR=$(get_scripts_dir)
get_scripts_dir() {
    local script_path
    script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    echo "$script_path"
}

# Get the project root directory (parent of scripts/)
# Usage: PROJECT_ROOT=$(get_project_root)
get_project_root() {
    local script_path
    script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    echo "$script_path"
}

# ==================== Advanced Pytest Helpers ====================

# Run pytest with optional tests (handles exit code 5 gracefully)
# Exit code 5 means "no tests were collected" which is okay for optional tests
# Usage: run_pytest_optional "test_k8s/" "-v -m manual -k readiness" "Running optional readiness tests"
run_pytest_optional() {
    local test_path="${1:-test_k8s/}"
    local pytest_args="${2:--v}"
    local description="${3:-}"
    local no_tests_message="${4:-No tests found matching criteria (this is okay for optional tests)}"
    
    if [ -n "$description" ]; then
        log_note "$description"
        echo ""
    fi
    
    # Convert pytest_args string to array for proper argument handling
    local -a args_array
    eval "args_array=($pytest_args)"
    
    # Temporarily disable exit on error to capture exit code
    set +e
    pytest "$test_path" "${args_array[@]}"
    local exit_code=$?
    set -e
    
    # Handle exit codes
    if [ $exit_code -eq 0 ]; then
        return 0
    elif [ $exit_code -eq 5 ]; then
        # Exit code 5 = no tests collected (okay for optional tests)
        log_warning "$no_tests_message"
        return 0
    else
        # Any other exit code is a real failure
        log_error "Pytest failed with exit code $exit_code"
        return $exit_code
    fi
}

# ==================== Kubernetes Helpers ====================

# Run kubectl command with error context and logging
# Provides better error messages and consistent logging
# Usage: kubectl_safe "Applying deployment" apply -f k8s/deployment.yaml
kubectl_safe() {
    local description="$1"
    shift
    
    log_info "$description"
    
    if ! kubectl "$@"; then
        log_error "kubectl command failed: $description"
        log_error "Command: kubectl $*"
        return 1
    fi
    
    return 0
}

# Wait for pods to be ready with a given label selector
# Usage: wait_for_pods_ready "app=hello-flask" 60
# Usage: wait_for_pods_ready "app=hello-flask"  (uses default 60s timeout)
wait_for_pods_ready() {
    local label="$1"
    local timeout="${2:-60}"
    
    log_info "Waiting for pods with label '$label' to be ready (timeout: ${timeout}s)..."
    
    if kubectl wait --for=condition=ready pod -l "$label" --timeout="${timeout}s" > /dev/null 2>&1; then
        log_success "All pods ready"
        return 0
    else
        log_warning "Some pods may not be ready yet (timeout reached or no pods found)"
        return 1
    fi
}

# ==================== Performance Helpers ====================

# Execute a command and log execution time
# Useful for tracking performance and identifying slow operations
# Usage: time_command "Building Docker image" docker build -t myapp .
# Usage: time_command "Running tests" make test
time_command() {
    local description="$1"
    shift
    
    log_info "Starting: $description"
    local start_time
    start_time=$(date +%s)
    
    # Run the command with all remaining arguments
    "$@"
    local exit_code=$?
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log_success "Completed in ${duration}s: $description"
    else
        log_error "Failed after ${duration}s: $description (exit code: $exit_code)"
    fi
    
    return $exit_code
}

