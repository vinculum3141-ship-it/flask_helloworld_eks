#!/bin/bash
set -euo pipefail

# GitHub Actions Workflow Validation Script
# Validates CI/CD workflow configuration and dependencies

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

WORKFLOW_FILE=".github/workflows/ci-cd.yml"

# Track validation status
ERRORS=0
WARNINGS=0

# Navigate to repository root
check_git_repo || exit 1
PROJECT_ROOT=$(get_project_root)
cd "$PROJECT_ROOT"

print_header "GitHub Actions Workflow Validation"
echo ""
log_info "Repository: $(basename "$PROJECT_ROOT")"
log_info "Location: $PROJECT_ROOT"
echo ""

# Check GitHub CLI status (optional)
echo -e "${BLUE}🔧 GitHub CLI Status${NC}"
echo "--------------------"
if command_exists gh; then
    if gh auth status &> /dev/null 2>&1; then
        log_success "GitHub CLI: Available & Authenticated"
        REPO_INFO=$(gh repo view --json nameWithOwner,defaultBranch 2>/dev/null || echo "")
        if [[ -n "$REPO_INFO" ]]; then
            REPO_NAME=$(echo "$REPO_INFO" | jq -r '.nameWithOwner' 2>/dev/null || echo "Unknown")
            DEFAULT_BRANCH=$(echo "$REPO_INFO" | jq -r '.defaultBranch' 2>/dev/null || echo "Unknown")
            log_note "  Repository: $REPO_NAME"
            log_note "  Default branch: $DEFAULT_BRANCH"
        fi
        GH_AVAILABLE=true
    else
        log_warning "GitHub CLI: Available but not authenticated"
        log_note "  💡 Optional: Run 'gh auth login' for enhanced features"
        GH_AVAILABLE=false
    fi
else
    log_note "ℹ️  GitHub CLI: Not installed (optional tool)"
    log_note "  💡 Optional: Install with 'sudo apt install gh'"
    GH_AVAILABLE=false
fi
echo ""

# 1. Check workflow file exists
echo -e "${BLUE}📁 Workflow File Check${NC}"
echo "---------------------"
if [[ ! -f "$WORKFLOW_FILE" ]]; then
    log_error "Workflow file not found: $WORKFLOW_FILE"
    ERRORS=$((ERRORS + 1))
    exit 1
else
    log_success "Found workflow file: $WORKFLOW_FILE"
fi
echo ""

# 2. YAML Syntax Validation
echo -e "${BLUE}🔍 YAML Syntax Validation${NC}"
echo "-------------------------"
if command_exists yamllint; then
    echo "Running yamllint..."
    if yamllint "$WORKFLOW_FILE" \
        --config-data '{extends: default, rules: {line-length: {max: 120}, trailing-spaces: disable, comments: {min-spaces-from-content: 1}}}' 2>&1; then
        log_success "YAML syntax is valid"
    else
        log_warning "YAML has formatting issues but may still work"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    log_warning "yamllint not found - install with: pip install yamllint"
    log_note "  Skipping syntax check"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 3. Workflow Structure Analysis
echo -e "${BLUE}📋 Workflow Structure Analysis${NC}"
echo "------------------------------"

# Check for required top-level fields
echo "Checking required workflow fields..."

if grep -q "^name:" "$WORKFLOW_FILE"; then
    WORKFLOW_NAME=$(grep "^name:" "$WORKFLOW_FILE" | cut -d':' -f2- | xargs)
    log_success "Workflow name: $WORKFLOW_NAME"
else
    log_error "Missing workflow name"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "^on:" "$WORKFLOW_FILE"; then
    log_success "Trigger events defined"
    
    # Check specific triggers
    if grep -q "push:" "$WORKFLOW_FILE"; then
        echo -e "  ${GREEN}✅${NC} Push trigger configured"
    fi
    if grep -q "pull_request:" "$WORKFLOW_FILE"; then
        echo -e "  ${GREEN}✅${NC} Pull request trigger configured"
    fi
    if grep -q "workflow_dispatch:" "$WORKFLOW_FILE"; then
        echo -e "  ${GREEN}✅${NC} Manual dispatch configured"
    fi
else
    log_error "Missing trigger events"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "^jobs:" "$WORKFLOW_FILE"; then
    log_success "Jobs section defined"
    
    # Count jobs
    JOB_COUNT=$(grep -E "^  [a-zA-Z0-9_-]+:" "$WORKFLOW_FILE" | wc -l)
    log_note "  Found $JOB_COUNT job(s)"
else
    log_error "Missing jobs section"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# 4. Best Practices Check
print_header "Best Practices Check"

# Check for versioned actions
if grep -qE "uses: .+@v[0-9]+" "$WORKFLOW_FILE"; then
    log_success "Using versioned actions"
else
    log_warning "Consider using versioned actions (e.g., actions/checkout@v4)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for timeouts
if grep -q "timeout-minutes:" "$WORKFLOW_FILE"; then
    log_success "Timeouts configured"
else
    log_warning "Consider adding timeouts to prevent stuck jobs"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for cleanup steps
if grep -q "if: always()" "$WORKFLOW_FILE"; then
    log_success "Cleanup steps configured (if: always())"
else
    log_warning "Consider adding cleanup steps with 'if: always()'"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for environment variables
if grep -q "^env:" "$WORKFLOW_FILE"; then
    log_success "Environment variables defined"
else
    log_note "No global environment variables"
fi

# Check for permissions
if grep -q "permissions:" "$WORKFLOW_FILE"; then
    log_success "Permissions explicitly defined (security best practice)"
else
    log_warning "Consider explicitly defining permissions for security"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# 5. Project Structure Validation
print_header "Project Structure Validation"

# Check app directory
if [[ -f "app/requirements.txt" ]]; then
    log_success "app/requirements.txt exists"
else
    log_error "app/requirements.txt missing"
    ERRORS=$((ERRORS + 1))
fi

if [[ -f "app/Dockerfile" ]]; then
    log_success "app/Dockerfile exists"
else
    log_error "app/Dockerfile missing"
    ERRORS=$((ERRORS + 1))
fi

# Check scripts directory
if [[ -d "scripts" ]]; then
    log_success "scripts/ directory exists"
else
    log_error "scripts/ directory missing"
    ERRORS=$((ERRORS + 1))
fi

# Check k8s manifests
if [[ -d "k8s" ]]; then
    log_success "k8s/ directory exists"
    
    # Count manifests
    MANIFEST_COUNT=$(find k8s -name "*.yaml" -o -name "*.yml" | wc -l)
    log_note "  Found $MANIFEST_COUNT Kubernetes manifest(s)"
else
    log_error "k8s/ directory missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# 6. Referenced Scripts Validation
print_header "Referenced Scripts Validation"
echo "Checking if referenced scripts exist..."

# Extract script references from workflow
SCRIPTS=($(grep -oE "scripts/[a-zA-Z0-9_-]+\.sh" "$WORKFLOW_FILE" 2>/dev/null | sort -u || true))

if [[ ${#SCRIPTS[@]} -eq 0 ]]; then
    log_note "No script references found in workflow"
else
    for script_path in "${SCRIPTS[@]}"; do
        if [[ -f "$script_path" ]]; then
            log_success "$script_path exists"
            if [[ -x "$script_path" ]]; then
                echo -e "  ${GREEN}└─ ✅ Executable${NC}"
            else
                echo -e "  ${YELLOW}└─ ⚠️  Not executable (run: chmod +x $script_path)${NC}"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            log_error "$script_path missing"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

echo ""

# 7. Kubernetes Manifests Validation
print_header "Kubernetes Manifests Validation"

if command_exists kubectl; then
    echo "Running kubectl dry-run validation..."
    
    # Try dry-run validation - this works without a cluster
    if kubectl apply --dry-run=client -f k8s/ 2>&1 | grep -q "error:.*does not exist"; then
        echo -e "${YELLOW}⚠️  Minikube cluster not running - skipping kubectl validation${NC}"
        log_note "  Start Minikube to enable full validation: minikube start"
        WARNINGS=$((WARNINGS + 1))
    elif kubectl apply --dry-run=client -f k8s/ &>/dev/null; then
        log_success "All Kubernetes manifests are valid"
    else
        log_warning "Kubernetes manifest validation had issues"
        echo "Run this command for details:"
        echo "  kubectl apply --dry-run=client -f k8s/"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    log_warning "kubectl not found - skipping manifest validation"
    echo -e "  Install kubectl to validate manifests"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# 8. Action Versions Check
print_header "GitHub Actions Version Check"
echo "Actions used in workflow:"

grep -n "uses:" "$WORKFLOW_FILE" | while IFS=: read -r line_num content; do
    action=$(echo "$content" | sed 's/.*uses: *//')
    echo -e "  ${BLUE}Line $line_num:${NC} $action"
done

echo ""

# 9. GitHub CLI Integration (if available)
if [[ "$GH_AVAILABLE" == "true" ]]; then
    print_header "GitHub CLI Integration"
    
    # List existing workflows
    echo "Available workflows:"
    if gh workflow list 2>/dev/null | grep -q .; then
        gh workflow list 2>/dev/null | sed 's/^/  /'
    else
        log_note "  No workflows found (workflow will appear after first push)"
    fi
    
    echo ""
    echo "Recent workflow runs:"
    if gh run list --limit 5 2>/dev/null | grep -q .; then
        gh run list --limit 5 2>/dev/null | sed 's/^/  /'
    else
        log_note "  No workflow runs yet"
    fi
    
    echo ""
fi

# 10. Validation Summary
print_header "VALIDATION SUMMARY"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    log_success "Workflow configuration is valid!"
else
    echo -e "${RED}❌ Found $ERRORS critical error(s)${NC}"
fi

if [[ $WARNINGS -gt 0 ]]; then
    log_warning "Found $WARNINGS warning(s)"
fi

echo ""
log_info "Validation Results:"
echo "  Workflow: $WORKFLOW_FILE"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

# 11. Next Steps
if [[ $ERRORS -eq 0 ]]; then
    print_header "READY TO PROCEED"
    echo ""
    log_success "All critical checks passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Commit your changes:"
    echo "     git add ."
    echo "     git commit -m 'feat: update workflow'"
    echo ""
    echo "  2. Push to trigger workflow:"
    echo "     git push origin <branch-name>"
    echo ""
    
    if [[ "$GH_AVAILABLE" == "true" ]]; then
        echo "  3. Monitor with GitHub CLI:"
        echo "     gh run watch"
        echo ""
        echo "  Or manually trigger:"
        echo "     gh workflow run \"$WORKFLOW_NAME\""
    else
        echo "  3. Monitor via GitHub web interface:"
        echo "     → Go to repository"
        echo "     → Click 'Actions' tab"
        echo "     → Watch workflow execution"
    fi
    echo ""
    exit 0
else
    print_header "FIX ERRORS BEFORE PROCEEDING"
    echo ""
    log_error "Fix the errors above, then run this script again."
    echo ""
    exit 1
fi
