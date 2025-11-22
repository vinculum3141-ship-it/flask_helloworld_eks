#!/bin/bash
set -euo pipefail

# Repository Structure Validation Script
# Validates that all required files and directories exist for the Flask Kubernetes project

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Track validation status
ERRORS=0
WARNINGS=0

# Navigate to repository root
check_git_repo || exit 1
PROJECT_ROOT=$(get_project_root)
cd "$PROJECT_ROOT"

print_header "Repository Structure Validation"
echo ""
log_info "Repository root: $PROJECT_ROOT"
echo ""

# Helper function for checks
check_file() {
    local file=$1
    local description=$2
    if [[ -f "$file" ]]; then
        echo -e "  ${GREEN}✅${NC} $description"
        return 0
    else
        echo -e "  ${RED}❌${NC} $description ${RED}(missing: $file)${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_dir() {
    local dir=$1
    local description=$2
    if [[ -d "$dir" ]]; then
        echo -e "  ${GREEN}✅${NC} $description"
        return 0
    else
        echo -e "  ${RED}❌${NC} $description ${RED}(missing: $dir)${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

warn_if_missing() {
    local file=$1
    local description=$2
    if [[ ! -e "$file" ]]; then
        echo -e "  ${YELLOW}⚠️${NC}  $description ${YELLOW}(optional: $file)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# 1. Core Application Files
echo -e "${BLUE}📦 Core Application Files${NC}"
echo "-------------------------"
check_file "app/app.py" "Flask application"
check_file "app/Dockerfile" "Docker build configuration"
check_file "app/requirements.txt" "Python dependencies"
# Note: __pycache__ is created automatically by Python, not required for validation
if [[ -d "app/__pycache__" ]]; then
    echo -e "  ${GREEN}✅${NC} Python cache directory"
else
    echo -e "  ${YELLOW}ℹ️${NC}  Python cache (created on first run)"
fi
echo ""

# 2. Kubernetes Manifests
echo -e "${BLUE}☸️  Kubernetes Manifests${NC}"
echo "-----------------------"
check_dir "k8s" "Kubernetes manifests directory"
if [[ -d "k8s" ]]; then
    check_file "k8s/deployment.yaml" "Deployment configuration"
    check_file "k8s/service.yaml" "Service configuration"
    check_file "k8s/ingress.yaml" "Ingress configuration"
    check_file "k8s/configmap.yaml" "ConfigMap configuration"
    check_file "k8s/secret.yaml" "Secret configuration"
    
    # List all manifests
    echo ""
    echo -e "  ${BLUE}📋 All Kubernetes manifests:${NC}"
    ls k8s/*.yaml 2>/dev/null | sed 's/^/    /' || echo "    No YAML files found"
fi
echo ""

# 3. Scripts
echo -e "${BLUE}📜 Automation Scripts${NC}"
echo "--------------------"
check_dir "scripts" "Scripts directory"
if [[ -d "scripts" ]]; then
    # Check for essential scripts
    check_file "scripts/build_image.sh" "Docker build script"
    check_file "scripts/deploy_local.sh" "Deployment script"
    check_file "scripts/delete_local.sh" "Cleanup script"
    check_file "scripts/unit_tests.sh" "Unit test runner"
    check_file "scripts/k8s_tests.sh" "Kubernetes test runner"
    check_file "scripts/smoke_test.sh" "Smoke test script"
    check_file "scripts/liveness_test.sh" "Liveness probe test script"
    
    # Check for optional scripts
    warn_if_missing "scripts/port_forward.sh" "Port forwarding helper"
    warn_if_missing "scripts/setup_ingress.sh" "Ingress setup script"
    warn_if_missing "scripts/minikube_service_url.sh" "Service URL helper"
    
    # Check script permissions
    echo ""
    echo -e "  ${BLUE}🔐 Script Permissions:${NC}"
    for script in scripts/*.sh; do
        if [[ -f "$script" ]]; then
            if [[ -x "$script" ]]; then
                echo -e "    ${GREEN}✅${NC} $(basename "$script") is executable"
            else
                echo -e "    ${YELLOW}⚠️${NC}  $(basename "$script") not executable (run: chmod +x $script)"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    done
fi
echo ""

# 4. Test Suite
echo -e "${BLUE}🧪 Test Suite${NC}"
echo "-------------"
check_dir "test_k8s" "Kubernetes integration tests"
if [[ -d "test_k8s" ]]; then
    check_file "test_k8s/conftest.py" "Pytest configuration"
    check_file "test_k8s/utils.py" "Test utilities"
    check_file "test_k8s/__init__.py" "Test package init"
    
    # Count test files
    test_count=$(find test_k8s -name "test_*.py" -type f | wc -l)
    echo -e "  ${GREEN}✅${NC} Found $test_count test files"
fi

check_dir "app/tests" "Application unit tests"
if [[ -d "app/tests" ]]; then
    check_file "app/tests/test_app.py" "Flask unit tests"
fi

check_file "pytest.ini" "Pytest configuration"
echo ""

# 5. CI/CD Configuration
echo -e "${BLUE}🚀 CI/CD Configuration${NC}"
echo "---------------------"
check_dir ".github" "GitHub configuration"
check_dir ".github/workflows" "GitHub Actions workflows"
if [[ -d ".github/workflows" ]]; then
    check_file ".github/workflows/ci-cd.yml" "CI/CD pipeline"
    
    # List all workflows
    workflow_count=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    echo -e "  ${GREEN}✅${NC} Found $workflow_count workflow file(s)"
fi
echo ""

# 6. Documentation
echo -e "${BLUE}📚 Documentation${NC}"
echo "----------------"
check_file "README.md" "Main documentation"
check_dir "docs" "Documentation directory"
if [[ -d "docs" ]]; then
    check_file "docs/README.md" "Documentation index"
    check_file "docs/operations/CI_CD_GUIDE.md" "CI/CD guide"
    
    # Check for optional docs
    warn_if_missing "docs/DEBUGGING_CI_CD.md" "CI/CD debugging guide"
    warn_if_missing "docs/testing/architecture/TEST_ARCHITECTURE.md" "Test architecture documentation"
    
    # Count documentation files
    doc_count=$(find docs -name "*.md" -type f | wc -l)
    echo -e "  ${GREEN}✅${NC} Found $doc_count documentation files"
fi
echo ""

# 7. Project Configuration
echo -e "${BLUE}⚙️  Project Configuration${NC}"
echo "------------------------"
check_file "Makefile" "Make automation"
check_file ".gitignore" "Git ignore rules"

# Check for Python virtual environment
if [[ -d ".venv" ]]; then
    echo -e "  ${GREEN}✅${NC} Python virtual environment (.venv)"
else
    echo -e "  ${YELLOW}ℹ️${NC}  No .venv found (create with: python3 -m venv .venv)"
fi

# Check for common Python files
warn_if_missing "requirements.txt" "Root requirements file (app/requirements.txt is sufficient)"
echo ""

# 8. Validation Summary
echo -e "${BLUE}📊 VALIDATION SUMMARY${NC}"
echo "===================="
echo ""

if [[ $WARNINGS -gt 0 ]]; then
    log_warning "Found $WARNINGS warning(s) (optional items missing)"
fi

if [[ $ERRORS -eq 0 ]]; then
    log_success "All required files and directories are present!"
else
    log_error "Found $ERRORS critical error(s)"
fi

echo ""
log_note "Repository Status:"
echo "  Root: $PROJECT_ROOT"
echo "  Structure: ✅ Flask app + Kubernetes + Tests + CI/CD"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    log_success "Repository structure is valid and ready for deployment!"
    exit 0
else
    log_error "Fix errors above before proceeding"
    exit 1
fi
