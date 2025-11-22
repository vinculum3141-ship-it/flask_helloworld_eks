# CI/CD Pipeline Guide

**Purpose**: Complete reference for the GitHub Actions CI/CD pipeline and development workflow automation.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Workflow Triggers](#workflow-triggers)
- [Pipeline Stages](#pipeline-stages)
- [Features Checklist](#features-checklist)
- [GitHub CLI Usage](#github-cli-usage)
- [Manual Testing](#manual-testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) automates the complete build, deploy, test, and security scanning workflow for the Flask application on Kubernetes.

**Pipeline Flow**:
```
Push/PR → Build → Deploy → Test → Scan → Report → Cleanup
```

**Key Features**:
- ✅ Automated testing at multiple levels (unit → integration → smoke)
- ✅ Security vulnerability scanning with Trivy
- ✅ Minikube deployment with Ingress support
- ✅ Guaranteed cleanup (runs even on failure)
- ✅ Detailed test result artifacts and GitHub annotations

---

## Workflow Triggers

The pipeline automatically triggers on:

### 1. **Branch Pushes**
Triggers on pushes to:
- `main` - Production branch (full pipeline)
- `develop` - Development branch (integration testing)
- `feature/**` - Feature branches (early feedback)
- `hotfix/**` - Hotfix branches (urgent fixes)

### 2. **Pull Requests**
Triggers on PRs targeting:
- `main` - PRs to production (thorough validation, deployment skipped)
- `develop` - PRs to development (integration validation)

### 3. **Manual Dispatch**
Allows on-demand execution with custom parameters:
- **Environment**: `test`, `staging`, or `production`
- **Run smoke tests**: Toggle smoke test execution
- **Debug mode**: Enable detailed debugging output across all scripts

---

## Pipeline Stages

### Stage 1: Setup
**Duration**: ~5 minutes

- ✅ Checkout repository
- ✅ Setup Python 3.11 with dependency caching
- ✅ Install dependencies in virtual environment
- ✅ Setup Docker with BuildKit
- ✅ Start Minikube cluster (K8s v1.28.0)
- ✅ Enable nginx Ingress controller

### Stage 2: Build Validation
**Duration**: ~1 minute

Early validation before expensive Docker build:

- ✅ **Step 4: Validate repository structure**
  - Script: `scripts/validate_repo_structure.sh`
  - Verifies all required directories and files exist
  - Fails fast if project structure is incorrect

- ✅ **Step 5: Validate workflow configuration**
  - Script: `scripts/validate_workflow.sh`
  - Checks GitHub Actions workflow syntax
  - Ensures CI/CD pipeline configuration is valid

### Stage 3: Build
**Duration**: ~10 minutes

- ✅ Build Docker image with layer caching
- ✅ Tag with both commit SHA and `latest`
- ✅ Use Minikube's Docker daemon (no registry needed)

**Image Tags**:
```
hello-flask:${GITHUB_SHA}
hello-flask:latest
```

### Stage 4: Deploy
**Duration**: ~5 minutes
**Note**: Skipped for Pull Requests

- ✅ Apply Kubernetes manifests (ConfigMap, Secret, Deployment, Service, Ingress)
- ✅ Wait for pods to be ready (5 min timeout)
- ✅ Wait for Ingress to get an address

**Deployment Script**: See [`scripts/deploy_local.sh`](../scripts/README.md#deploy_localsh)

### Stage 5: Test
**Duration**: ~10 minutes

Tests run in sequence with continue-on-error to collect all results:

1. **Unit Tests** - Flask application tests
   - Script: `scripts/unit_tests.sh`
   - Tests: `app/tests/test_app.py`

2. **Kubernetes Integration Tests** - Infrastructure validation
   - Script: `scripts/k8s_tests.sh`
   - Tests: `test_k8s/` (deployment, service, ConfigMap, etc.)
   - Auto-detects NodePort vs Ingress configuration

3. **Smoke Tests** - End-to-end validation
   - Script: `scripts/smoke_test.sh`
   - Validates application is accessible and responding correctly

**Test Reports**: Uploaded as GitHub artifacts (retained for 7 days)

### Stage 6: Security Scanning
**Duration**: ~5 minutes
**Runs in parallel** with deployment/testing

- ✅ Trivy vulnerability scan of Docker image
- ✅ SARIF report uploaded to GitHub Security tab
- ✅ Scan results available in pipeline logs

### Stage 7: Cleanup
**Duration**: ~2 minutes
**Guaranteed to run** even on failure

- ✅ Delete Kubernetes resources
- ✅ Stop Minikube
- ✅ Clean up Docker resources

---

## Features Checklist

Comprehensive overview of CI/CD capabilities:

### 1. Security & Permissions
| Feature | Status | Notes |
|---------|--------|-------|
| Minimal GITHUB_TOKEN permissions | ✅ | Read-only access, write only where needed |
| Environment variables centralized | ✅ | Defined in `env:` section |
| Security scanning (Trivy) | ✅ | Parallel execution |
| SARIF upload to Security tab | ✅ | Vulnerability tracking |

### 2. Performance & Caching
| Feature | Status | Notes |
|---------|--------|-------|
| Pip dependency caching | ✅ | Guarded for fork safety |
| Docker layer caching | ⚠️ | Prepared but limited by Minikube driver |
| Updated actions (v5/v6) | ✅ | Latest stable versions |
| Parallel jobs | ✅ | Security scan runs in parallel |

### 3. Reliability & Resilience
| Feature | Status | Notes |
|---------|--------|-------|
| Step timeouts | ✅ | Prevents hung steps |
| Job timeout (30 min) | ✅ | Prevents runaway jobs |
| Guaranteed cleanup | ✅ | `if: always()` ensures cleanup |
| Deployment readiness wait | ✅ | 5-minute timeout with proper checks |

### 4. Workflow Triggers
| Feature | Status | Notes |
|---------|--------|-------|
| Multi-branch support | ✅ | main, develop, feature/*, hotfix/* |
| Pull request validation | ✅ | Deployment skipped for PRs |
| Manual dispatch | ✅ | With environment and test toggles |
| Conditional deployment | ✅ | PRs skip deployment step |

### 5. Error Handling & Reporting
| Feature | Status | Notes |
|---------|--------|-------|
| Test result artifacts | ✅ | 7-day retention |
| Detailed status reporting | ✅ | Step-by-step logs |
| Continue-on-error for tests | ✅ | Collects all test results |
| GitHub annotations | ✅ | Test failures shown inline |

### 6. Production-Ready Features
| Feature | Status | Notes |
|---------|--------|-------|
| Environment-aware behavior | ✅ | Manual dispatch supports environments |
| Resource management | ✅ | Cleanup guaranteed |
| Comprehensive testing | ✅ | Unit → K8s → Smoke tests |
| Artifact retention | ✅ | Test results stored for 7 days |

---

## GitHub CLI Usage

The GitHub CLI (`gh`) enables command-line control of workflows and pipelines.

### Installation

**Ubuntu/Debian**:
```bash
sudo apt install gh -y
```

**macOS**:
```bash
brew install gh
```

### Authentication

First-time setup:
```bash
gh auth login
```

Follow the prompts to create a personal access token. See [GitHub CLI Manual](https://cli.github.com/manual/gh_auth_login) for detailed instructions.

### Common Commands

#### View Workflow Runs
```bash
# List recent workflow runs
gh run list

# Watch a specific run in real-time
gh run watch

# View details of a specific run
gh run view <run-id>
```

#### Trigger Workflows Manually
```bash
# Trigger the CI/CD pipeline on current branch
gh workflow run "Flask CI/CD Pipeline"

# Trigger with specific parameters
gh workflow run "Flask CI/CD Pipeline" \
  --ref main \
  --field environment=staging \
  --field run_smoke_tests=true

# Trigger with debug mode enabled
gh workflow run "Flask CI/CD Pipeline" \
  --ref main \
  --field debug_mode=true
```

#### Create Pull Requests
```bash
# Create PR from current branch
gh pr create --title "Feature: Add health endpoint" --body "Implements /health endpoint for better liveness probes"

# View PR checks
gh pr checks
```

### Testing in Feature Branches

**Recommended workflow** for testing CI/CD changes:

1. **Create an isolated test branch**:
   ```bash
   git checkout -b test-ci-pipeline
   ```

2. **Make changes to the workflow**:
   ```bash
   # Edit .github/workflows/ci-cd.yml
   vim .github/workflows/ci-cd.yml
   ```

3. **Commit and push**:
   ```bash
   git add .github/workflows/ci-cd.yml
   git commit -m "test: experiment with CI/CD pipeline"
   git push origin test-ci-pipeline
   ```

4. **Monitor the automated run**:
   ```bash
   # Push automatically triggers the workflow
   gh run watch
   ```

5. **Or trigger manually with custom parameters**:
   ```bash
   gh workflow run "Flask CI/CD Pipeline" \
     --ref test-ci-pipeline \
     --field run_smoke_tests=false  # Skip smoke tests for faster iteration
   ```

6. **View results**:
   - Web interface: GitHub → Actions tab
   - Terminal: `gh run list --branch test-ci-pipeline`

---

## Manual Testing

For local validation before pushing to the repository:

### Automated Pre-Push Validation

**Quick validation scripts** to run before every push:

```bash
# 1. Validate repository structure
bash scripts/validate_repo_structure.sh

# 2. Validate workflow configuration
bash scripts/validate_workflow.sh
```

These scripts check:
- ✅ All required files and directories exist
- ✅ Scripts are executable
- ✅ Workflow configuration is valid
- ✅ YAML syntax is correct
- ✅ Kubernetes manifests are valid

**See [Development Workflow Guide](DEVELOPMENT_WORKFLOW.md) for complete validation documentation.**

### Pre-Push Validation

**Prerequisites**:
```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r app/requirements.txt
pip install pytest requests yamllint
```

**Validation Steps**:

1. **Repository Structure Validation**:
   ```bash
   bash scripts/validate_repo_structure.sh
   ```

2. **Workflow Configuration Validation**:
   ```bash
   bash scripts/validate_workflow.sh
   ```

3. **Unit Tests**:
   ```bash
   bash scripts/unit_tests.sh
   ```

4. **Docker Build** (optional, requires Docker):
   ```bash
   bash scripts/build_image.sh
   ```

5. **Kubernetes Manifest Validation** (requires kubectl):
   ```bash
   kubectl apply --dry-run=client -f k8s/
   ```

### Full Local Pipeline Test

To test the complete pipeline locally:

```bash
# 1. Start Minikube
minikube start

# 2. Build and deploy
make full-deploy

# 3. Run all tests
make test-all

# 4. Run smoke tests
make smoke-test

# 5. Cleanup
make delete
```

See the [Makefile](../Makefile) for all available commands.

---

## Troubleshooting

### Enabling Debug Mode

For detailed debugging output across all pipeline scripts:

**Via GitHub UI**:
1. Navigate to **Actions** tab in your repository
2. Select **Flask CI/CD Pipeline** workflow
3. Click **Run workflow** button
4. Check the **Enable debug mode** checkbox
5. Click **Run workflow**

**Via GitHub CLI**:
```bash
gh workflow run "Flask CI/CD Pipeline" \
  --ref main \
  --field debug_mode=true
```

**What Debug Mode Does**:
- Sets `DEBUG=1` environment variable across all scripts
- Enables verbose output in all shell scripts
- Shows detailed timing information via `time_command()` wrapper
- Provides enhanced error messages and stack traces
- Useful for diagnosing pipeline issues

### Common Issues

#### 1. **Pipeline Fails on Fork/PR**

**Symptom**: Cache restoration fails on forks or external PRs

**Solution**: The pipeline already includes guards:
```yaml
if: ${{ github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository }}
```

This is expected behavior for security reasons.

#### 2. **Deployment Timeout**

**Symptom**: Pods don't become ready within 5 minutes

**Solution**: 
- Check pod logs: `kubectl logs -l app=hello-flask`
- Check events: `kubectl get events --sort-by='.lastTimestamp'`
- See [Ingress Guide](ingress/INGRESS_GUIDE.md)

#### 3. **Ingress Not Getting Address**

**Symptom**: Ingress waits indefinitely for an IP address

**Solution**:
- Verify Ingress controller is running: `kubectl get pods -n ingress-nginx`
- See [Ingress Guide](ingress/INGRESS_GUIDE.md)

#### 4. **Test Failures**

**Symptom**: Tests fail in CI but pass locally

**Solution**:
- Check test artifacts in GitHub Actions
- Verify Kubernetes resources are ready: `kubectl get all`
- Review test logs in the pipeline output

### Additional Resources

- **[Ingress Guide](ingress/INGRESS_GUIDE.md)** - Complete Ingress troubleshooting and CI/CD integration
- **[Scripts Documentation](../../scripts/README.md)** - Script usage and troubleshooting
- **[Test Architecture](../testing/architecture/TEST_ARCHITECTURE.md)** - Test suite details

---

## Reference

### Related Documentation
- **Main README**: [`../README.md`](../README.md)
- **Scripts Guide**: [`../scripts/README.md`](../scripts/README.md)
- **Test Suite**: [`../test_k8s/README.md`](../test_k8s/README.md)
- **Workflow File**: [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml)

### External Links
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubernetes CI/CD Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)

---

**Last Updated**: November 16, 2025
