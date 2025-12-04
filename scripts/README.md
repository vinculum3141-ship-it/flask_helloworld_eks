# Scripts Documentation

## Overview

The `scripts/` directory contains modular Bash scripts for automating common development and testing workflows. Each script has a targeted function, making it easy to run only what you need and integrate into CI/CD pipelines.

**Important:** All scripts run within the Minikube environment. Remember to:
- Start Minikube before running scripts: `minikube start`
- Stop Minikube when done: `minikube stop`

---

## Script Reference

### Build & Deployment Scripts

#### `build_image.sh`
**Purpose:** Build the Docker image for the Flask application.

**What it does:**
- Sets up Minikube Docker environment
- Builds Docker image with tag `hello-flask:latest`
- Verifies image was created successfully

**Usage:**
```bash
bash scripts/build_image.sh
```

**When to run:** After making changes to application code or Dockerfile

---

#### `deploy_local.sh`
**Purpose:** Deploy the application to local Kubernetes cluster with Ingress.

**What it does:**
- Sets up Ingress controller (if not already configured)
- Applies Kubernetes manifests (deployment, service, ingress, configmap, secret)
- Waits for pods to become ready
- Displays access information

**Usage:**
```bash
bash scripts/deploy_local.sh
```

**When to run:** After building the image, to deploy to Minikube

**Note:** This deploys with Ingress (ClusterIP service). For NodePort deployment, apply manifests manually.

---

#### `delete_local.sh`
**Purpose:** Clean up all Kubernetes resources.

**What it does:**
- Deletes all application resources (deployment, service, ingress, configmap, secret)
- Confirms cleanup was successful

**Usage:**
```bash
bash scripts/delete_local.sh
```

**When to run:** When you need to clean up resources or start fresh

---

### Testing Scripts

#### `unit_tests.sh`
**Purpose:** Run application-level unit tests.

**What it does:**
- Runs pytest on `app/tests/` directory
- Tests Flask application logic independently of Kubernetes

**Usage:**
```bash
bash scripts/unit_tests.sh
```

**Duration:** Fast (~1-2 seconds)

---

#### `coverage_test.sh`
**Purpose:** Run unit tests with coverage metrics.

**What it does:**
- Runs pytest with coverage tracking via pytest-cov
- Generates coverage reports in multiple formats
- Shows which code lines are tested and which are missing

**Usage:**
```bash
# Terminal report (default)
bash scripts/coverage_test.sh terminal

# HTML report (interactive, detailed)
bash scripts/coverage_test.sh html

# XML report (for CI/CD)
bash scripts/coverage_test.sh xml

# All formats
bash scripts/coverage_test.sh all
```

**Output:**
- Terminal: Coverage % and missing line numbers
- HTML: Interactive report in `htmlcov/index.html`
- XML: Machine-readable `coverage.xml`

**Duration:** ~2-3 seconds (slightly slower than plain unit tests)

**See also:** `docs/testing/COVERAGE_GUIDE.md` for detailed documentation

---

#### `k8s_tests.sh`
**Purpose:** Run Kubernetes integration tests (automated suite only).

**What it does:**
- Runs pytest on `test_k8s/` directory
- Excludes manual tests using `-m 'not manual'` marker
- Tests deployment, services, ingress, probes, configmaps

**Usage:**
```bash
bash scripts/k8s_tests.sh
```

**Duration:** ~15-20 seconds

**Note:** Excludes manual tests (pod deletion, crash recovery) for faster feedback

---

#### `liveness_test.sh`
**Purpose:** Run liveness probe and self-healing tests with multiple modes.

**What it does:**
- **Default mode:** Runs automated liveness probe configuration tests
- **Manual mode:** Runs behavioral tests (pod deletion, crash recovery)
- **Config mode:** Runs only configuration checks
- Tests `/health` endpoint and liveness probe behavior
- Verifies automatic container restart on failure

**Usage:**
```bash
# Automated configuration tests only (default)
bash scripts/liveness_test.sh

# Manual behavioral tests (pod deletion, crash recovery)
bash scripts/liveness_test.sh --manual

# Configuration check only
bash scripts/liveness_test.sh --config
```

**Duration:**
- Automated/Config: Fast (~2-3 seconds)
- Manual: Slow (~60-90 seconds)

**Note:** Manual tests involve wait times and are best run explicitly. Readiness probe tests are in `readiness_test.sh`.

---

#### `readiness_test.sh`
**Purpose:** Run readiness probe and traffic routing tests with multiple modes.

**What it does:**
- **Default mode:** Runs automated readiness probe configuration tests
- **Manual mode:** Runs behavioral tests (traffic routing, pod readiness)
- **Config mode:** Runs only configuration checks
- Tests `/ready` endpoint and readiness probe behavior
- Verifies ready replicas match desired count

**Usage:**
```bash
# Automated configuration tests only (default)
bash scripts/readiness_test.sh

# Manual behavioral tests (traffic routing validation)
bash scripts/readiness_test.sh --manual

# Configuration check only
bash scripts/readiness_test.sh --config
```

**Duration:**
- Automated/Config: Fast (~2-3 seconds)
- Manual: May involve timing (~10-30 seconds)

**Note:** Readiness probe determines when pods receive traffic. Separate from liveness probe which handles container restarts.

---

#### `health_endpoint_tests.sh`
**Purpose:** Run comprehensive /health endpoint tests in development.

**What it does:**
- Temporarily switches service from ClusterIP to NodePort
- Runs all health endpoint integration tests
- Automatically restores service to ClusterIP after testing
- Safe cleanup even if tests fail (uses trap)

**Usage:**
```bash
bash scripts/health_endpoint_tests.sh
# or
make health-tests
```

**Duration:** ~30-40 seconds

**When to run:**
- Development testing of /health endpoint behavior
- Validating health check performance and reliability
- Testing health endpoint during replica scaling

**Note:** 
- Requires active deployment
- Temporarily modifies service configuration (auto-restored)
- Not included in smoke tests (runs separately for development)

---

#### `smoke_test.sh`
**Purpose:** Quick validation of all critical functionality (automated tests only).

**What it does:**
- Runs all automated Kubernetes tests
- Excludes manual tests using `-m 'not manual'` marker
- Provides fast feedback on deployment health

**Usage:**
```bash
bash scripts/smoke_test.sh
```

**Duration:** ~15-20 seconds

**When to run:** After deployment to quickly verify everything works

---

### Utility Scripts

#### `port_forward.sh`
**Purpose:** Forward service port to localhost for local testing.

**What it does:**
- Sets up port forwarding from localhost:8080 to service port 5000
- Keeps running until interrupted (Ctrl+C)
- Displays access URL

**Usage:**
```bash
bash scripts/port_forward.sh
# Then access: http://localhost:8080
```

**When to run:** When you need to test the service directly without Ingress/NodePort

**Note:** Blocks terminal - use Ctrl+C to stop

---

#### `minikube_service_url.sh`
**Purpose:** Get service URL and access methods.

**What it does:**
- Auto-detects service type (NodePort or ClusterIP)
- Provides appropriate access instructions and tests connectivity
- For NodePort: Shows `minikube service` URL and tests the service
- For ClusterIP+Ingress: Shows multiple access methods (hostname, IP+Host header, port-forward)
- Tests connectivity intelligently (tries hostname first, falls back to IP if needed)

**Usage:**
```bash
bash scripts/minikube_service_url.sh
# or
make minikube-url
```

**Output examples:**

For ClusterIP with Ingress:
```
[INFO] Service type: ClusterIP
[INFO] Ingress hostname: hello-flask.local
Access via: http://hello-flask.local
  or: curl -H "Host: hello-flask.local" http://192.168.49.2
[SUCCESS] App is accessible
```

For NodePort:
```
[INFO] Service type: NodePort
[INFO] Access your app at: http://192.168.49.2:30123
```

**When to run:** When you need to know how to access the deployed service
```bash
bash scripts/minikube_service_url.sh
```

**When to run:** When you need to know how to access the deployed service

---

#### `setup_ingress.sh`
**Purpose:** Set up Ingress controller and configure host resolution.

**What it does:**
- Enables nginx ingress controller in Minikube
- Waits for ingress controller pods to be ready
- Adds `hello-flask.local` entry to `/etc/hosts`
- Verifies setup is complete

**Usage:**
```bash
bash scripts/setup_ingress.sh
```

**When to run:** Once per Minikube cluster, before deploying with Ingress

**Note:** Requires sudo for `/etc/hosts` modification

---

## Quick Reference Table

| Script | Purpose | Duration | Blocks Terminal |
|--------|---------|----------|-----------------|
| `build_image.sh` | Build Docker image | ~10-20s | No |
| `deploy_local.sh` | Deploy to Minikube | ~15-30s | No |
| `delete_local.sh` | Cleanup resources | ~5s | No |
| `unit_tests.sh` | App unit tests | ~2s | No |
| `k8s_tests.sh` | K8s integration tests | ~15-20s | No |
| `liveness_test.sh` | Liveness probe tests | ~2-90s* | No |
| `readiness_test.sh` | Readiness probe tests | ~2-30s** | No |
| `smoke_test.sh` | Quick validation | ~15-20s | No |
| `port_forward.sh` | Port forwarding | Continuous | Yes |
| `minikube_service_url.sh` | Get access URL | ~1s | No |
| `setup_ingress.sh` | Setup Ingress | ~30-60s | No |

\* *Liveness test duration depends on mode: config (~2s), automated (~3s), manual (~60-90s)*  
\*\* *Readiness test duration depends on mode: config (~2s), automated (~3s), manual (~10-30s)*

---

## Scripts Architecture

All bash scripts use a **shared utilities library** for consistent output and easier maintenance.

### Shared Library (`scripts/lib/common.sh`)

**Location:** `scripts/lib/common.sh`

**Features:**
- **Color definitions**: `GREEN`, `BLUE`, `YELLOW`, `RED`, `NC` (No Color)
- **Logging functions**: 
  - `log_info()` - Informational messages (blue)
  - `log_success()` - Success messages (green)
  - `log_warning()` - Warning messages (yellow)
  - `log_error()` - Error messages (red)
  - `log_note()` - Important notes (yellow)
- **Header formatting**: `print_header()` - Consistent script headers
- **Debug mode**: `enable_debug_mode()` - Enable verbose trace output (set -x) via DEBUG or VERBOSE env vars
- **Pytest helpers**: 
  - `run_pytest()` - Standardized test execution (improved in Phase 3)
  - `run_pytest_optional()` - Run tests that may not exist (handles exit code 5)
- **Kubernetes helpers**:
  - `kubectl_safe()` - Run kubectl with error context and logging
  - `wait_for_pods_ready()` - Wait for pods to be ready with timeout
- **Performance helpers**:
  - `time_command()` - Execute command with timing information (Phase 3)
- **Validation helpers**: 
  - `command_exists()` - Check if command is available
  - `check_git_repo()` - Verify we're in a git repository
- **Path helpers**: 
  - `get_scripts_dir()` - Get scripts directory path
  - `get_project_root()` - Get project root path

### Advanced Helper Functions

**`run_pytest(test_path, pytest_args, description)` (Phase 3 Improvement)**
- Improved argument handling - no longer uses `eval` for better security
- Properly handles complex pytest marker expressions
- Example:
  ```bash
  run_pytest "test_k8s/" "-v -m 'not manual and not nodeport'"
  run_pytest "app/tests/" "-v" "Testing Flask application"
  ```

**`run_pytest_optional(test_path, pytest_args, description, no_tests_message)`**
- Handles pytest exit code 5 (no tests collected) gracefully
- Useful for running optional or manual tests that may not exist yet
- Improved in Phase 3: Better argument handling without `eval`
- Example:
  ```bash
  run_pytest_optional \
      "test_k8s/" \
      "-v -m manual -k readiness" \
      "Running optional manual tests" \
      "No manual tests found yet (this is okay)"
  ```

**`kubectl_safe(description, kubectl_args...)`**
- Wrapper for kubectl commands with better error messages
- Logs what operation is being performed
- Provides context on failure
- Example:
  ```bash
  kubectl_safe "Applying deployment" apply -f k8s/deployment.yaml
  kubectl_safe "Waiting for rollout" rollout status deployment/hello-flask
  ```

**`wait_for_pods_ready(label, timeout)`**
- Wait for pods matching a label to be ready
- Default timeout is 60 seconds
- Example:
  ```bash
  wait_for_pods_ready "app=hello-flask" 60
  wait_for_pods_ready "app=hello-flask"  # Uses default 60s
  ```

**`time_command(description, command...)` (Phase 3 New)**
- Execute a command and log execution time
- Useful for performance tracking and identifying slow operations
- Logs success/failure with duration
- Example:
  ```bash
  time_command "Building Docker image" docker build -t myapp:latest .
  time_command "Running tests" make test
  time_command "Deploying to cluster" kubectl apply -f k8s/
  ```
  Output:
  ```
  [INFO] Starting: Building Docker image
  ...command output...
  ✅ Completed in 45s: Building Docker image
  ```

### Benefits

✅ **Single source of truth** - Colors and formatting defined once  
✅ **Consistent output** - All scripts use the same style  
✅ **Easier maintenance** - Update logging in one place, applies everywhere  
✅ **Better error handling** - Standardized error messages and strict error handling (`set -euo pipefail`)  
✅ **Code reuse** - Common patterns extracted into reusable functions  
✅ **Easy debugging** - Enable verbose trace mode with `DEBUG=1` or `VERBOSE=1` environment variable  
✅ **Robust operations** - kubectl_safe() and wait_for_pods_ready() improve reliability  
✅ **Secure argument handling** - Removed `eval` usage for safer command execution (Phase 3)  
✅ **Performance visibility** - time_command() helps identify slow operations (Phase 3)  

### Usage Pattern

All scripts follow this pattern:

```bash
#!/bin/bash

# Source the common library
source "$(dirname "$0")/lib/common.sh"

# Print script header
print_header "My Script Title"

# Use logging functions
log_info "Processing started..."

# Check prerequisites
if ! command_exists kubectl; then
    log_error "kubectl is not installed"
    exit 1
fi

# Run pytest with standard helper
run_pytest "test_k8s/" "-v"

# Success message
log_success "All done!"
```

### Example Output

When you run a script, you'll see consistent, color-coded output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  My Script Title
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ℹ Processing started...
✓ All done!
```

### Debug Mode

All scripts support verbose debugging mode for troubleshooting. When enabled, the shell will print each command before executing it (using `set -x`).

**Enable debug mode:**

```bash
# Using DEBUG environment variable
DEBUG=1 bash scripts/unit_tests.sh

# Using VERBOSE environment variable (alternative)
VERBOSE=1 bash scripts/smoke_test.sh

# Works with any script
DEBUG=1 bash scripts/build_image.sh
```

**Example debug output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Debug mode enabled (set -x)
+ SCRIPT_DIR=/home/user/flask_helloworld_miniproject/scripts
+ PROJECT_ROOT=/home/user/flask_helloworld_miniproject
+ cd /home/user/flask_helloworld_miniproject
+ pytest app/tests/ -v
...
```

**When to use:**
- 🐛 Debugging script failures
- 🔍 Understanding script execution flow
- 🛠️ Troubleshooting environment issues
- 📊 Investigating unexpected behavior

---

## Makefile Integration

All scripts can also be run via Makefile targets for convenience. The Makefile provides shortcuts that are easier to remember and type.

### Quick Help

To see all available Makefile targets at any time:
```bash
make help
```

### Build & Deployment Targets

```bash
make build           # Build Docker image (runs build_image.sh)
make deploy          # Deploy to local cluster (runs deploy_local.sh)
make delete          # Delete local deployment (runs delete_local.sh)
```

### Testing Targets

**Individual Test Targets:**
```bash
make unit-tests           # Run unit tests (runs unit_tests.sh)
make test-coverage        # Run unit tests with coverage (terminal report)
make test-coverage-html   # Run unit tests with HTML coverage report
make test-coverage-xml    # Run unit tests with XML coverage (for CI/CD)
make test-coverage-all    # Run unit tests with all coverage formats
make k8s-tests            # Run K8s integration tests (runs k8s_tests.sh)
make educational-tests    # Run educational Ingress tests only
make ingress-tests        # Run all Ingress tests (basic + educational)
make smoke-test           # Run smoke tests - quick validation (runs smoke_test.sh)
```

**Liveness Test Variations:**
```bash
make liveness-test         # Run automated liveness probe configuration tests
make liveness-test-manual  # Run manual behavioral tests (pod deletion, crash recovery)
make liveness-test-config  # Run only liveness probe configuration check
```

**Composite Test Targets:**
```bash
make test-all        # Run all automated tests (unit + k8s integration, excludes manual)
make test-full       # Run ALL tests including manual, educational, and nodeport (comprehensive)
```

### Utility Targets

```bash
make port-forward    # Forward service port to localhost (runs port_forward.sh)
make minikube-url    # Get service URL and access methods (runs minikube_service_url.sh)
```

### Validation Targets

**Pre-Push Validation:**
```bash
make validate-repo      # Validate repository structure (runs validate_repo_structure.sh)
make validate-workflow  # Validate GitHub Actions workflow (runs validate_workflow.sh)
make validate-all       # Run all validation checks (both scripts)
```

See [Development Workflow](../docs/DEVELOPMENT_WORKFLOW.md) for detailed validation documentation.

### Changelog Targets

```bash
make changelog                              # Generate changelog from all commits
make changelog-since TAG=v1.0.0             # Generate changelog since specific tag
make changelog-range FROM=v1.0.0 TO=v2.0.0  # Generate changelog between tags
make changelog-dev                          # Append auto-generated changelog to CHANGELOG.md
make changelog-dev-since TAG=v1.0.0         # Append changelog since tag to CHANGELOG.md
```

### Composite Workflow Targets

These targets run multiple steps in sequence:

```bash
make full-deploy     # Complete workflow: build → deploy → smoke test
make test-all        # Run automated tests (unit + k8s, excludes manual)
make test-full       # Run ALL tests including manual, educational, and nodeport
make release-prep    # Complete release preparation: validate structure/workflow → verify test requirements → test-full → build → deploy → smoke test
```

### Complete Makefile Reference

| Target | Script/Action | Description |
|--------|---------------|-------------|
| `build` | `build_image.sh` | Build Docker image |
| `deploy` | `deploy_local.sh` | Deploy to local cluster |
| `delete` | `delete_local.sh` | Delete local deployment |
| `unit-tests` | `unit_tests.sh` | Run unit tests |
| `k8s-tests` | `k8s_tests.sh` | Run K8s integration tests |
| `educational-tests` | `pytest -m educational` | Run educational Ingress tests |
| `ingress-tests` | `pytest -m ingress` | Run all Ingress tests |
| `health-tests` | `health_endpoint_tests.sh` | Run health endpoint tests (NodePort) |
| `liveness-test` | `liveness_test.sh` | Run automated liveness probe tests |
| `liveness-test-manual` | `liveness_test.sh --manual` | Run manual liveness behavioral tests |
| `liveness-test-config` | `liveness_test.sh --config` | Run liveness config check only |
| `readiness-test` | `readiness_test.sh` | Run automated readiness probe tests |
| `readiness-test-manual` | `readiness_test.sh --manual` | Run manual readiness behavioral tests |
| `readiness-test-config` | `readiness_test.sh --config` | Run readiness config check only |
| `smoke-test` | `smoke_test.sh` | Run smoke tests |
| `port-forward` | `port_forward.sh` | Forward service port |
| `minikube-url` | `minikube_service_url.sh` | Get service URL |
| `validate-repo` | `validate_repo_structure.sh` | Validate repository structure |
| `validate-workflow` | `validate_workflow.sh` | Validate GitHub Actions workflow |
| `validate-all` | Composite | Run all validation checks |
| `changelog` | `generate_changelog.sh` | Generate changelog |
| `test-all` | Composite | Run unit + k8s tests (automated) |
| `test-full` | Composite | Run ALL tests (includes manual, educational, nodeport) |
| `full-deploy` | Composite | Build + deploy + smoke test |
| `release-prep` | Composite | Complete release: validate structure/workflow + verify test requirements + test-full + build + deploy + smoke |
| `help` | Display help | Show all available targets |

### Benefits of Using Makefile

✅ **Shorter commands** - `make test-all` vs `bash scripts/unit_tests.sh && bash scripts/k8s_tests.sh`  
✅ **Easier to remember** - Standard make targets like `build`, `deploy`, `test`  
✅ **Composable** - Combine multiple steps with composite targets  
✅ **Auto-completion** - Many shells support make target auto-completion  
✅ **Self-documenting** - `make help` shows all available commands  

### Usage Examples

**Quick deployment:**
```bash
make full-deploy
# Equivalent to:
# bash scripts/build_image.sh
# bash scripts/deploy_local.sh
# bash scripts/smoke_test.sh
```

**Run automated tests (CI/CD friendly):**
```bash
make test-all
# Equivalent to:
# bash scripts/unit_tests.sh
# bash scripts/k8s_tests.sh
# Excludes manual/slow tests
```

**Run comprehensive tests (development):**
```bash
make test-full
# Runs ALL tests including:
# - Unit tests
# - K8s integration tests
# - Educational ingress tests
# - NodePort tests
# - Manual/slow tests (crash recovery)
```

**Prepare for release:**
```bash
make release-prep
# Complete release preparation workflow:
# 1. Repository validation
# 2. Full test suite (test-full)
# 3. Build Docker image
# 4. Deploy to local cluster
# 5. Final smoke test
# 6. Display release checklist
```

**Check available commands:**
```bash
make help
```

---

### Test Target Selection Guide

| Target | Duration | Use Case | When to Run |
|--------|----------|----------|-------------|
| `make unit-tests` | ~1-2 sec | Unit testing only | During development, after code changes |
| `make k8s-tests` | ~30-60 sec | K8s integration (automated) | After deployment changes, in CI/CD |
| `make health-tests` | ~30-40 sec | Health endpoint validation | Development, testing /health behavior |
| `make test-all` | ~1-2 min | Automated suite | Pre-commit, CI/CD pipelines |
| `make test-full` | ~5-10 min | Comprehensive testing | Pre-release, major changes |
| `make smoke-test` | ~5-10 sec | Quick validation | After deployment |

**Recommendation:**
- **During development:** `make unit-tests` or `make test-all`
- **Before commit/push:** `make test-all`
- **Before release:** `make release-prep`
- **In CI/CD:** `make test-all`

---

## Workflow Examples

### Complete Deployment Workflow

```bash
# 1. Start Minikube
minikube start

# 2. Setup Ingress (one time)
bash scripts/setup_ingress.sh

# 3. Build and deploy
bash scripts/build_image.sh
bash scripts/deploy_local.sh

# 4. Verify deployment
bash scripts/smoke_test.sh

# 5. Get access URL
bash scripts/minikube_service_url.sh

# 6. Cleanup when done
bash scripts/delete_local.sh
minikube stop
```

### Testing Workflow

```bash
# Run unit tests
bash scripts/unit_tests.sh

# Run all K8s tests (automated)
bash scripts/k8s_tests.sh

# Run manual tests if needed
bash scripts/liveness_test.sh --manual

# Quick smoke test
bash scripts/smoke_test.sh
```

### Release Preparation Workflow

**Option 1: Using Makefile (Recommended)**
```bash
# Complete automated release preparation
make release-prep

# After completion, follow the displayed checklist:
# 1. Review CHANGELOG.md
# 2. Update version numbers
# 3. Commit changes
# 4. Create and push git tag
# 5. Create GitHub release
```

**Option 2: Manual Step-by-Step**
```bash
# 1. Validate repository and workflow
make validate-all

# 2. Run comprehensive test suite
make test-full

# 3. Build final image
make build

# 4. Deploy to local cluster for final validation
make deploy

# 5. Final smoke test
make smoke-test

# 6. Generate changelog (replace v1.0.0 with your previous tag)
make changelog-since TAG=v1.0.0

# 7. Review output and update CHANGELOG.md
# 8. Commit, tag, and push
git add .
git commit -m "Release v1.1.0"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main
git push origin v1.1.0
```

**What `make release-prep` does:**
1. ✅ Validates repository structure and GitHub Actions workflow
2. ✅ Validates test requirement coverage (22/22 documented tests present)
3. ✅ Runs ALL tests (unit, k8s, educational, nodeport, manual)
4. ✅ Builds production Docker image
5. ✅ Deploys to local cluster
6. ✅ Runs final smoke tests
7. ✅ Displays comprehensive release checklist

### Development Workflow

```bash
# Make code changes...

# Rebuild and redeploy
bash scripts/build_image.sh
bash scripts/delete_local.sh
bash scripts/deploy_local.sh

# Test changes
bash scripts/smoke_test.sh
```

### Full Manual Testing Workflow

For comprehensive step-by-step manual verification of all components:

```bash
# 1. Environment Setup
minikube start
minikube status
kubectl cluster-info

# 2. Validate Repository
make validate-all

# 3. Run All Test Suites
make unit-tests              # Unit tests
make k8s-tests              # Kubernetes integration tests
make educational-tests      # Educational/demo tests
make health-tests           # Health endpoint tests (NodePort)

# 4. Build and Deploy
make build                  # Build Docker image
make deploy                 # Deploy to Kubernetes

# 5. Verify Deployment
kubectl get pods -l app=hello-flask
kubectl get service hello-flask
kubectl get ingress hello-flask-ingress
kubectl get configmap hello-flask-config
kubectl get secret hello-flask-secret

# 6. Check Pod Health
kubectl describe pods -l app=hello-flask
kubectl logs -l app=hello-flask --tail=50

# 7. Run Smoke Tests
make smoke-test

# 8. Manual Service Testing
# Test via Ingress
curl -H "Host: hello-flask.local" http://$(minikube ip)/
curl -H "Host: hello-flask.local" http://$(minikube ip)/health

# Test via NodePort (optional)
kubectl patch service hello-flask -p '{"spec":{"type":"NodePort"}}'
minikube service hello-flask --url
# Use the URL from above to test:
# curl <SERVICE_URL>/
# curl <SERVICE_URL>/health

# Restore to ClusterIP
kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}'

# 9. Test Liveness/Readiness Probes
kubectl describe deployment hello-flask | grep -A 10 "Liveness\|Readiness"

# 10. Test Pod Restart and Recovery
kubectl delete pod -l app=hello-flask --force --grace-period=0
kubectl get pods -l app=hello-flask -w  # Watch pods restart (Ctrl+C to exit)
make smoke-test  # Verify service recovered

# 11. Test Scaling
kubectl scale deployment hello-flask --replicas=3
kubectl get pods -l app=hello-flask -w  # Watch scaling (Ctrl+C when ready)
make smoke-test  # Verify with 3 replicas

# Scale back to 2
kubectl scale deployment hello-flask --replicas=2
kubectl get pods -l app=hello-flask -w  # Watch scale down (Ctrl+C when done)
make smoke-test

# 12. Test ConfigMap and Secret Values
kubectl get configmap hello-flask-config -o yaml
kubectl get secret hello-flask-secret -o yaml
# Verify values in pods:
POD=$(kubectl get pod -l app=hello-flask -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -- printenv | grep -E "ENVIRONMENT|APP_NAME|API_KEY|DB_PASSWORD"

# 13. Test Ingress Routing
# Test correct hostname
curl -H "Host: hello-flask.local" http://$(minikube ip)/
# Test wrong hostname (should get 404)
curl -H "Host: wrong-hostname.local" http://$(minikube ip)/

# 14. Load Balancing Test
for i in {1..10}; do 
  curl -s -H "Host: hello-flask.local" http://$(minikube ip)/ | grep -o "hello-flask-[a-z0-9-]*"
done
# Should see requests distributed across different pods

# 15. Final Comprehensive Test
make test-full

# 16. Cleanup (optional)
make delete
kubectl get all -l app=hello-flask  # Should show no resources
```

**Manual Testing Checklist:**

- [ ] Minikube is running and accessible
- [ ] Repository structure validated (`make validate-all`)
- [ ] Unit tests pass (`make unit-tests`)
- [ ] Kubernetes integration tests pass (`make k8s-tests`)
- [ ] Docker image builds successfully (`make build`)
- [ ] Deployment applied successfully (`make deploy`)
- [ ] All pods are Running (2/2 replicas)
- [ ] Service is type ClusterIP
- [ ] Ingress has IP address assigned
- [ ] ConfigMap exists with correct keys
- [ ] Secret exists with correct keys (base64 encoded)
- [ ] Environment variables injected into pods
- [ ] Application responds via Ingress
- [ ] Health endpoint returns 200 OK
- [ ] Liveness probe configured correctly
- [ ] Readiness probe configured correctly
- [ ] Pods can restart and recover
- [ ] Service scales up and down correctly
- [ ] Load balancing works across replicas
- [ ] Hostname routing works (correct host accepted, wrong host rejected)
- [ ] Health endpoint tests pass (`make health-tests`)
- [ ] Smoke tests pass (`make smoke-test`)
- [ ] Educational tests pass (`make educational-tests`)
- [ ] All comprehensive tests pass (`make test-full`)

---

## Troubleshooting

### Script Debugging

**Problem:** Script behaving unexpectedly or failing with unclear errors

**Solution:**
```bash
# Enable debug mode to see detailed execution trace
DEBUG=1 bash scripts/<script-name>.sh

# Example: Debug unit tests
DEBUG=1 bash scripts/unit_tests.sh

# Example: Debug build process
VERBOSE=1 bash scripts/build_image.sh
```

This shows:
- ✅ Every command executed by the script
- ✅ Variable values at each step
- ✅ Exact point of failure
- ✅ Environment and path information

### Script Fails with "command not found"

**Problem:** Script can't find `kubectl`, `minikube`, or other commands

**Solution:**
```bash
# Check prerequisites
kubectl version --client
minikube version
docker --version

# Install missing tools
# See main README.md for installation instructions
```

### Tests Fail - Pods Not Ready

**Problem:** Tests run before pods are ready

**Solution:**
```bash
# Wait for pods manually
kubectl wait --for=condition=ready pod -l app=hello-flask --timeout=60s

# Then run tests
bash scripts/k8s_tests.sh
```

### Port Forwarding Conflicts

**Problem:** Port 8080 already in use

**Solution:**
```bash
# Find and kill process using port 8080
lsof -ti:8080 | xargs kill -9

# Or use a different port
kubectl port-forward svc/hello-flask 8081:5000
```

### Ingress Not Working

**Problem:** Can't access via `hello-flask.local`

**Solution:**
```bash
# Re-run ingress setup
bash scripts/setup_ingress.sh

# Verify /etc/hosts entry
grep hello-flask /etc/hosts

# Check ingress controller
kubectl get pods -n ingress-nginx
```

---

## Contributing

When adding new scripts:

1. **Source the common library:**
   ```bash
   source "$(dirname "$0")/lib/common.sh"
   ```

2. **Use standard logging functions:**
   - `log_info()` for informational messages
   - `log_success()` for success
   - `log_error()` for errors
   - `log_warning()` for warnings

3. **Add to this README** with:
   - Purpose description
   - What it does
   - Usage example
   - When to run it
   - Special notes

4. **Add Makefile target** (optional but recommended)

5. **Test thoroughly** before committing

---

## Visual Exploration Tools

While this project uses `kubectl` commands for automation and production best practices, you can optionally use visual tools for learning and troubleshooting:

### Minikube Dashboard
```bash
minikube dashboard
```
Opens a web UI showing all cluster resources, logs, and metrics. Great for beginners to visualize Kubernetes objects.

### Alternative Tools
- **k9s** - Terminal UI for Kubernetes (recommended for power users)
- **Lens** - Desktop IDE for Kubernetes
- **kubectl plugins** - Extend kubectl with additional functionality

**Note:** All scripts in this project use `kubectl` for consistency and to teach production practices.

---

## Related Documentation

- **[Main README](../README.md)** - Project overview and quick start
- **[Test README](../test_k8s/README.md)** - Test suite documentation
- **[Script Updates](../docs/scripts/SCRIPT_UPDATES.md)** - Recent script changes
- **[Documentation Index](../docs/README.md)** - Complete documentation hub
