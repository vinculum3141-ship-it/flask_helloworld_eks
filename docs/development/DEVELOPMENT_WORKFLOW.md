# Development Workflow & Pre-Push Validation

**Purpose**: Guide for local development best practices, pre-push validation, and quality assurance before triggering CI/CD pipelines.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Pre-Push Validation Scripts](#pre-push-validation-scripts)
- [Quick Start](#quick-start)
- [Manual Validation Steps](#manual-validation-steps)
- [Recommended Workflow](#recommended-workflow)
- [Troubleshooting](#troubleshooting)

---

## Overview

Before pushing code to the repository and triggering the CI/CD pipeline, it's recommended to run local validation checks. This catches errors early, saves CI/CD time, and provides faster feedback during development.

**Benefits**:
- ✅ Catch errors before CI/CD runs
- ✅ Faster feedback loop (seconds vs minutes)
- ✅ Reduce failed pipeline runs
- ✅ Validate changes locally without cluster overhead

---

## Pre-Push Validation Scripts

The repository includes automated validation scripts that check your local environment and configuration:

### **1. Repository Structure Validation**

**Script**: `scripts/validate_repo_structure.sh`

**What it checks**:
- ✅ Core application files (`app/app.py`, `Dockerfile`, `requirements.txt`)
- ✅ Kubernetes manifests (all YAML files in `k8s/`)
- ✅ Automation scripts (all scripts in `scripts/`)
- ✅ Test suite (`test_k8s/`, `app/tests/`)
- ✅ CI/CD configuration (`.github/workflows/`)
- ✅ Documentation (`docs/`, `README.md`)
- ✅ Script permissions (executable flags)

**Usage**:
```bash
bash scripts/validate_repo_structure.sh
# OR using Make
make validate-repo
```

**Output**:
```
🧪 Repository Structure Validation
====================================

✅ All required files and directories are present!
⚠️  Found 1 warning(s) (optional items missing)

🚀 Repository structure is valid and ready for deployment!
```

---

### **2. Workflow Configuration Validation**

**Script**: `scripts/validate_workflow.sh`

**What it checks**:
- ✅ GitHub Actions workflow file exists
- ✅ YAML syntax validation (if `yamllint` installed)
- ✅ Workflow structure (name, triggers, jobs)
- ✅ Best practices (timeouts, cleanup, permissions)
- ✅ Referenced scripts exist and are executable
- ✅ Kubernetes manifests are valid (if `kubectl` available)
- ✅ GitHub Actions versions
- ✅ GitHub CLI status (optional)

**Usage**:
```bash
bash scripts/validate_workflow.sh
# OR using Make
make validate-workflow
```

**Output**:
```
🔍 GitHub Actions Workflow Validation
======================================

✅ Workflow configuration is valid!
⚠️  Found 2 warning(s)

🚀 READY TO PROCEED
------------------

✅ All critical checks passed!
```

---

## Quick Start

### Prerequisites

**Required**:
- Python 3.11+
- Git
- Bash shell

**Optional** (for enhanced validation):
- `yamllint` - YAML syntax validation
- `kubectl` - Kubernetes manifest validation
- `gh` - GitHub CLI for workflow management

**Install optional tools**:
```bash
# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install validation tools
pip install yamllint

# Install GitHub CLI (Ubuntu/Debian)
sudo apt install gh -y

# Authenticate GitHub CLI
gh auth login
```

### Run All Validations

**Quick validation** (recommended before every commit):
```bash
# Using scripts directly
bash scripts/validate_repo_structure.sh && bash scripts/validate_workflow.sh

# OR using Make (easier)
make validate-all
```

**With test execution**:
```bash
# 1. Validate structure
make validate-repo

# 2. Validate workflow
make validate-workflow

# 3. Run unit tests
make unit-tests

# 4. (Optional) Build Docker image locally
make build
```

---

## Manual Validation Steps

If you prefer manual validation or the scripts aren't available:

### 1. YAML Syntax Validation

**Check all YAML files** for syntax errors:

```bash
# Using yamllint
yamllint k8s/*.yaml .github/workflows/*.yml

# Or using Python
python3 -c "import yaml; yaml.safe_load(open('k8s/deployment.yaml'))"
```

### 2. Python Syntax Check

**Validate Python code**:

```bash
# Syntax check
python3 -m py_compile app/app.py

# Run unit tests
pytest app/tests/test_app.py -v
```

### 3. Kubernetes Manifest Validation

**Dry-run validation** (requires `kubectl`):

```bash
# Validate manifests without applying
kubectl apply --dry-run=client -f k8s/

# Validate specific manifest
kubectl apply --dry-run=client -f k8s/deployment.yaml
```

### 4. Script Permissions

**Ensure scripts are executable**:

```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Verify permissions
ls -la scripts/*.sh | grep -E "^-rwxr"
```

### 5. GitHub Actions Workflow Check

**Validate workflow syntax**:

```bash
# Using yamllint
yamllint .github/workflows/ci-cd.yml

# Check workflow with GitHub CLI (if authenticated)
gh workflow list
gh workflow view "Flask CI/CD Pipeline"
```

---

## Recommended Workflow

### Daily Development Cycle

```bash
# 1. Start your work session
git checkout -b feature/my-feature
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt pytest requests

# 2. Make changes to code
# ... edit files ...

# 3. Test locally
pytest app/tests/ -v                    # Unit tests
bash scripts/validate_repo_structure.sh # Structure check
bash scripts/validate_workflow.sh       # Workflow check

# 4. If tests pass, commit
git add .
git commit -m "feat: add new feature"

# 5. Run full validation before push
bash scripts/unit_tests.sh              # Full unit tests
bash scripts/validate_repo_structure.sh # Final structure check
bash scripts/validate_workflow.sh       # Final workflow check

# 6. Push and trigger CI/CD
git push origin feature/my-feature
```

### Before Pull Request

**Complete validation checklist**:

```bash
# 1. Repository structure
bash scripts/validate_repo_structure.sh

# 2. Workflow configuration
bash scripts/validate_workflow.sh

# 3. Unit tests
bash scripts/unit_tests.sh

# 4. (Optional) Full integration tests with Minikube
minikube start
bash scripts/build_image.sh
bash scripts/deploy_local.sh
bash scripts/k8s_tests.sh
bash scripts/smoke_test.sh
minikube stop

# 5. Create PR
gh pr create --title "Feature: My Feature" --body "Description..."
```

---

## Troubleshooting

### Common Issues

#### 1. **Script Debugging**

**Symptom**:
```
Script fails with unclear error or unexpected behavior
```

**Solution**:
```bash
# Enable debug mode to see detailed execution trace
DEBUG=1 bash scripts/validate_repo_structure.sh
DEBUG=1 bash scripts/validate_workflow.sh

# Or use VERBOSE as alternative
VERBOSE=1 bash scripts/validate_repo_structure.sh
```

**What you'll see:**
- Every command executed by the script
- Variable values at each step
- Exact point of failure
- Full execution trace with `set -x`

**When to use:**
- 🐛 Script fails with unclear error
- 🔍 Need to understand script behavior
- 🛠️ Investigating environment issues
- 📊 Debugging validation failures

#### 2. **Script Permission Denied**

**Symptom**:
```
bash: scripts/validate_repo_structure.sh: Permission denied
```

**Solution**:
```bash
chmod +x scripts/validate_repo_structure.sh
# Or make all scripts executable
chmod +x scripts/*.sh
```

#### 3. **yamllint Not Found**

**Symptom**:
```
⚠️  yamllint not found - install with: pip install yamllint
```

**Solution**:
```bash
pip install yamllint
```

#### 4. **kubectl Not Available**

**Symptom**:
```
⚠️  kubectl not found - skipping manifest validation
```

**Solution**:
```bash
# Install kubectl (Ubuntu/Debian)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Or use Minikube's kubectl
minikube kubectl -- version
```

#### 5. **Minikube Cluster Not Running**

**Symptom**:
```
⚠️  Minikube cluster not running - skipping kubectl validation
```

**Solution**:
```bash
minikube start
# Then run validation again
bash scripts/validate_workflow.sh
```

#### 6. **GitHub CLI Not Authenticated**

**Symptom**:
```
⚠️  GitHub CLI: Available but not authenticated
```

**Solution**:
```bash
gh auth login
# Follow the prompts to authenticate
```

---

## Validation Tools Reference

### Installed Tools

| Tool | Purpose | Install Command |
|------|---------|----------------|
| `yamllint` | YAML syntax validation | `pip install yamllint` |
| `kubectl` | Kubernetes manifest validation | See [kubectl docs](https://kubernetes.io/docs/tasks/tools/) |
| `gh` | GitHub CLI for workflows | `sudo apt install gh` |
| `pytest` | Python test runner | `pip install pytest` |
| `docker` | Container build testing | See [Docker docs](https://docs.docker.com/get-docker/) |

### Script Exit Codes

Both validation scripts follow standard exit code conventions:

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | ✅ All checks passed | Safe to proceed |
| `1` | ❌ Critical errors found | Fix errors before pushing |

**Warnings** don't cause script failure but should be reviewed.

---

## Integration with CI/CD

The local validation scripts check the same things that the CI/CD pipeline validates:

| Local Check | CI/CD Equivalent |
|-------------|------------------|
| Repository structure | Build step (Docker context) |
| Workflow configuration | GitHub Actions validation |
| YAML syntax | Kubernetes apply |
| Script existence | Pipeline execution |
| Manifest validation | Deployment step |

**Running local validation saves CI/CD time** by catching errors before triggering the pipeline.

---

## Related Documentation

- **[CI/CD Guide](CI_CD_GUIDE.md)** - Complete pipeline reference
- **[Scripts Guide](../scripts/README.md)** - All automation scripts
- **[Test Architecture](../testing/architecture/TEST_ARCHITECTURE.md)** - Test suite design
- **[Main README](../README.md)** - Project overview

---

**Last Updated**: November 16, 2025
