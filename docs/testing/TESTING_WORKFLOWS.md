# Testing Workflows Guide

Complete reference for all testing workflows and sequences in this project.

## Quick Navigation

- [Standard Development Workflow](#standard-development-workflow)
- [Test Sequences](#test-sequences)
- [Full Manual Testing](#full-manual-testing)
- [Make Targets Reference](#make-targets-reference)
- [Test Organization](#test-organization)

---

## Standard Development Workflow

### Daily Development Sequence

```bash
# 1. Start Minikube (if not running)
minikube start

# 2. Build, Deploy, Test
make build          # Build Docker image in Minikube's Docker daemon
make deploy         # Apply Kubernetes manifests
make smoke-test     # Quick validation (29 tests, ~7 seconds)
```

### Full Development Testing

```bash
# Complete testing workflow (before commits)
make validate-all   # Validate repository structure
make test-all       # Unit → K8s → Smoke tests
make build          # Build image
make deploy         # Deploy to cluster
make smoke-test     # Final validation
```

### Release Preparation

```bash
# Single command that does everything
make release-prep

# What it runs internally:
# 1. make validate-all      - Repository structure validation
# 2. make test-full         - All 6 test categories
# 3. make build             - Build Docker image
# 4. make deploy            - Deploy to Kubernetes
# 5. make smoke-test        - Final smoke tests
# 6. Print release checklist
```

---

## Test Sequences

### Fast Automated Tests (Pre-Commit)

```bash
make test-all       # Runs: unit-tests → k8s-tests → smoke-test
                    # Excludes: manual, nodeport, educational
                    # Duration: ~2 minutes
```

### Comprehensive Tests (Pre-Release)

```bash
make test-full      # Runs all 5 test categories:
                    # 1. unit-tests
                    # 2. k8s-tests
                    # 3. educational-tests
                    # 4. health-tests (with NodePort switching)
                    # 5. manual-tests
                    # Duration: ~5-10 minutes
```

### Health Endpoint Testing

```bash
make health-tests   # Specialized NodePort testing:
                    # - Backs up service config
                    # - Switches to NodePort
                    # - Runs 7 health endpoint tests
                    # - Restores to ClusterIP
                    # Duration: ~30 seconds
```

### Educational Ingress Tests

```bash
make educational-tests  # Educational/demo Ingress tests:
                        # - Hostname routing demonstration
                        # - Ingress vs direct access consistency
                        # - Load balancing across replicas
                        # - Probe frequency analysis
                        # Duration: ~5 seconds
```

### All Ingress Tests

```bash
make ingress-tests  # All Ingress-marked tests:
                    # - Basic ingress configuration tests
                    # - Educational ingress tests
                    # - Health endpoint via ingress
                    # Duration: ~5-10 seconds
```

### Liveness Probe Tests

```bash
make liveness-test         # Automated liveness probe configuration tests:
                           # - Verify liveness probe configured
                           # - Check /health endpoint
                           # - Validate probe settings
                           # Duration: ~2-3 seconds

make liveness-test-config  # Configuration check only:
                           # - Quick validation of liveness probe config
                           # Duration: ~2 seconds

make liveness-test-manual  # Manual behavioral tests:
                           # - Pod deletion and recovery
                           # - Crash recovery simulation
                           # - Self-healing validation
                           # Duration: ~60-90 seconds
```

### Readiness Probe Tests

```bash
make readiness-test         # Automated readiness probe configuration tests:
                            # - Verify readiness probe configured
                            # - Check /ready endpoint
                            # - Validate ready replicas
                            # Duration: ~2-3 seconds

make readiness-test-config  # Configuration check only:
                            # - Quick validation of readiness probe config
                            # Duration: ~2 seconds

make readiness-test-manual  # Manual readiness behavioral tests:
                            # - Traffic routing validation
                            # - Pod readiness checks
                            # Duration: ~10-30 seconds
```

---

## Full Manual Testing

For comprehensive step-by-step manual verification:

### Environment Setup

```bash
# 1. Start and verify environment
minikube start
minikube status
kubectl cluster-info

# 2. Validate repository structure
make validate-all
```

### Run Test Suites

```bash
# 3. Run all test categories
make unit-tests              # Application unit tests
make k8s-tests              # Kubernetes integration tests (25 tests)
make educational-tests      # Educational demos (4 tests)
make health-tests           # Health endpoint tests (7 tests, NodePort)
```

### Build and Deploy

```bash
# 4. Build Docker image
make build

# 5. Deploy to Kubernetes
make deploy

# 6. Verify deployment
kubectl get pods -l app=hello-flask
kubectl get service hello-flask
kubectl get ingress hello-flask-ingress
kubectl get configmap hello-flask-config
kubectl get secret hello-flask-secret
```

### Verify Application Health

```bash
# 7. Check pod health and logs
kubectl describe pods -l app=hello-flask
kubectl logs -l app=hello-flask --tail=50

# 8. Run smoke tests
make smoke-test
```

### Manual Service Testing

```bash
# 9. Test via Ingress (default ClusterIP)
curl -H "Host: hello-flask.local" http://$(minikube ip)/
curl -H "Host: hello-flask.local" http://$(minikube ip)/health

# 10. Test via NodePort (optional)
kubectl patch service hello-flask -p '{"spec":{"type":"NodePort"}}'
minikube service hello-flask --url
# Use the URL to test:
# curl <SERVICE_URL>/
# curl <SERVICE_URL>/health

# Restore to ClusterIP
kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}'
```

### Test Kubernetes Features

```bash
# 11. Verify probe configuration
kubectl describe deployment hello-flask | grep -A 10 "Liveness\|Readiness"

# 12. Test pod restart and self-healing
kubectl delete pod -l app=hello-flask --force --grace-period=0
kubectl get pods -l app=hello-flask -w  # Watch restart (Ctrl+C when done)
make smoke-test  # Verify recovery

# 13. Test scaling
kubectl scale deployment hello-flask --replicas=3
kubectl get pods -l app=hello-flask -w  # Watch scaling (Ctrl+C when ready)
make smoke-test  # Verify with 3 replicas

# Scale back to 2
kubectl scale deployment hello-flask --replicas=2
kubectl get pods -l app=hello-flask -w  # Watch scale down (Ctrl+C when done)
make smoke-test
```

### Test ConfigMap and Secrets

```bash
# 14. Verify ConfigMap and Secret
kubectl get configmap hello-flask-config -o yaml
kubectl get secret hello-flask-secret -o yaml

# 15. Verify values in pods
POD=$(kubectl get pod -l app=hello-flask -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -- printenv | grep -E "ENVIRONMENT|APP_NAME|API_KEY|DB_PASSWORD"
```

### Test Ingress Routing

```bash
# 16. Test hostname-based routing
# Correct hostname (should succeed)
curl -H "Host: hello-flask.local" http://$(minikube ip)/

# Wrong hostname (should get 404)
curl -H "Host: wrong-hostname.local" http://$(minikube ip)/

# 17. Test load balancing
for i in {1..10}; do 
  curl -s -H "Host: hello-flask.local" http://$(minikube ip)/ | grep -o "hello-flask-[a-z0-9-]*"
done
# Should see requests distributed across different pods
```

### Final Validation

```bash
# 18. Run comprehensive tests
make test-full

# 19. Cleanup (optional)
make delete
kubectl get all -l app=hello-flask  # Should show no resources
```

---

## Manual Testing Checklist

Use this for thorough verification:

**Environment:**
- [ ] Minikube is running and accessible
- [ ] Repository structure validated (`make validate-all`)

**Testing:**
- [ ] Unit tests pass (`make unit-tests`)
- [ ] Kubernetes integration tests pass (`make k8s-tests`)
- [ ] Educational tests pass (`make educational-tests`)
- [ ] Health endpoint tests pass (`make health-tests`)

**Deployment:**
- [ ] Docker image builds successfully (`make build`)
- [ ] Deployment applied successfully (`make deploy`)
- [ ] All pods are Running (2/2 replicas)
- [ ] Service is type ClusterIP
- [ ] Ingress has IP address assigned

**Configuration:**
- [ ] ConfigMap exists with correct keys
- [ ] Secret exists with correct keys (base64 encoded)
- [ ] Environment variables injected into pods

**Functionality:**
- [ ] Application responds via Ingress
- [ ] Health endpoint returns 200 OK
- [ ] Liveness probe configured correctly
- [ ] Readiness probe configured correctly

**Resilience:**
- [ ] Pods can restart and recover
- [ ] Service scales up and down correctly
- [ ] Load balancing works across replicas

**Routing:**
- [ ] Hostname routing works (correct host accepted)
- [ ] Wrong hostname rejected (404)

**Final:**
- [ ] Smoke tests pass (`make smoke-test`)
- [ ] All comprehensive tests pass (`make test-full`)

---

## Make Targets Reference

### Build & Deployment

| Command | Duration | Purpose |
|---------|----------|---------|
| `make build` | ~30s | Build Docker image in Minikube |
| `make deploy` | ~5s | Apply Kubernetes manifests |
| `make delete` | ~5s | Delete deployment from cluster |

### Testing Targets

| Command | Tests | Duration | Use Case |
|---------|-------|----------|----------|
| `make smoke-test` | 29 | ~7s | Quick validation after deploy |
| `make k8s-tests` | 25 | ~5s | Integration tests (no NodePort) |
| `make health-tests` | 7 | ~30s | Health endpoint validation (NodePort) |
| `make educational-tests` | 4 | ~5s | Educational Ingress demos |
| `make ingress-tests` | varies | ~5-10s | All Ingress-marked tests |
| `make liveness-test` | 2 | ~2-3s | Liveness probe configuration tests |
| `make liveness-test-config` | 1 | ~2s | Liveness config check only |
| `make liveness-test-manual` | varies | ~60-90s | Manual liveness behavioral tests |
| `make readiness-test` | 3 | ~2-3s | Readiness probe configuration tests |
| `make readiness-test-config` | 1 | ~2s | Readiness config check only |
| `make readiness-test-manual` | varies | ~10-30s | Manual readiness behavioral tests |
| `make unit-tests` | 22 | ~2s | Application unit tests |
| `make test-all` | all automated | ~2min | Pre-commit validation |
| `make test-full` | ALL | ~5-10min | Comprehensive testing |

### Validation & Workflows

| Command | Purpose |
|---------|---------|
| `make validate-all` | Validate repository structure |
| `make release-prep` | Complete release workflow |

---

## Test Organization

### Test Markers

Tests use pytest markers for selective execution:

```bash
# Run specific test types
pytest test_k8s/ -v -m nodeport      # NodePort tests only
pytest test_k8s/ -v -m ingress       # Ingress tests only
pytest test_k8s/ -v -m educational   # Educational tests only
pytest test_k8s/ -v -m manual        # Manual tests only
pytest test_k8s/ -v -m slow          # Slow tests only
```

### Marker Exclusions

Different test targets exclude different markers:

```bash
# smoke-test and k8s-tests exclude:
-m 'not manual and not nodeport and not educational'

# health-tests runs only:
-m 'nodeport'

# educational-tests runs only:
-m 'educational'
```

### Test Count Summary

- **smoke-test**: 29 passed, 1 skipped, 12 deselected
- **k8s-tests**: 25 passed, 1 skipped, 16 deselected
- **health-tests**: 7 passed, 2 deselected (NodePort only)
- **educational-tests**: 4 passed, 38 deselected
- **test-full**: All categories combined

---

## Common Scenarios

### After Modifying Application Code

```bash
make build
make deploy
make smoke-test
```

### After Modifying /health Endpoint

```bash
make build
make deploy
make health-tests
```

### Before Git Commit

```bash
make test-all
```

### Before Opening PR

```bash
make release-prep
```

### After Modifying K8s Manifests

```bash
make validate-all
make deploy
make k8s-tests
```

### Learning Kubernetes Concepts

```bash
make educational-tests
```

---

## Service Type Considerations

- **Default**: ClusterIP + Ingress (production-like)
- **Health tests**: Automatically switches to NodePort, then restores
- **Manual switching** (if needed):

```bash
# Switch to NodePort
kubectl patch service hello-flask -p '{"spec":{"type":"NodePort"}}'

# Switch back to ClusterIP
kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}'
```

---

## Related Documentation

- **[Scripts Guide](../../scripts/README.md)** - Automation scripts and workflows
- **[Health Endpoint Testing](HEALTH_ENDPOINT_TESTING.md)** - Health endpoint test details
- **[Test Architecture](architecture/TEST_ARCHITECTURE.md)** - Test design overview
- **[Unit Test Reference](UNIT_TEST_REFERENCE.md)** - Unit testing guide
- **[Main README](../../README.md)** - Project overview and quick start
