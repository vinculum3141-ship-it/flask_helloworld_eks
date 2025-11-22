# Health Endpoint Testing Guide

## Overview

This guide explains how to test the `/health` endpoint in different deployment configurations. Tests are organized by service type requirements using pytest markers.

## Background

The Flask application exposes a `/health` endpoint used by Kubernetes liveness probes. Testing this endpoint requires different service access methods:

- **ClusterIP** (default): Service only accessible within cluster or via Ingress
- **NodePort**: Service accessible externally via node IP:port

## Test Organization by Service Type

Health endpoint tests in `test_k8s/test_health_endpoint.py` are marked based on their service type requirements:

### NodePort Tests (`@pytest.mark.nodeport`)
Tests that require direct pod access via NodePort:
- `test_health_endpoint_via_nodeport` - Direct service access
- `test_health_endpoint_performance_in_cluster` - Performance measurements
- `test_health_consistency_across_replicas` - Multi-replica validation
- `test_health_endpoint_during_pod_restart` - Restart behavior
- `test_health_vs_root_response_time_comparison` - Endpoint comparison
- `test_health_endpoint_without_readiness` - Probe independence
- `test_liveness_probe_configuration_matches_health_endpoint` - Config validation

### Ingress Tests (`@pytest.mark.ingress`)
Tests that validate external access via Ingress with ClusterIP:
- `test_health_endpoint_via_ingress` - External monitoring access pattern

### Educational Tests (`@pytest.mark.educational`)
Demonstration tests that may have environmental dependencies:
- `test_demonstrate_probe_frequency` - Probe frequency analysis

## Running Tests

### Health Endpoint Tests (NodePort)
**Command:** `make health-tests`
- Runs only NodePort-marked tests
- Temporarily switches service to NodePort
- Automatically restores to ClusterIP after completion
- Duration: ~30 seconds

```bash
make health-tests
```

### Integration Tests (Ingress)
**Command:** `make k8s-tests`
- Runs with default ClusterIP + Ingress
- Includes ingress-marked health test
- Excludes NodePort and educational tests
- Duration: ~5 seconds

```bash
make k8s-tests
```

### Full Test Suite
**Command:** `make test-full`
- Runs ALL tests including NodePort, Ingress, and educational
- Automatically handles service switching
- Duration: ~5-10 minutes

```bash
make test-full
```

## Solution: Conditional Testing

The `make health-tests` command provides automated service switching:
1. ✅ Backs up current service configuration
2. ✅ Switches to NodePort temporarily
3. ✅ Runs NodePort-marked tests only (`-m nodeport`)
4. ✅ Restores original ClusterIP configuration
5. ✅ Cleans up even if tests fail

## Test Markers

Tests use pytest markers to indicate service type requirements:

```python
# NodePort test example
@pytest.mark.nodeport
def test_health_endpoint_via_nodeport(self):
    service_url = get_service_url("hello-flask")
    # ... test code

# Ingress test example
@pytest.mark.ingress
def test_health_endpoint_via_ingress(self):
    minikube_ip = get_minikube_ip()
    headers = {"Host": "hello-flask.local"}
    # ... test code
```

Selective execution:

```bash
# Run only NodePort tests
pytest test_k8s/test_health_endpoint.py -m nodeport -v

# Run only Ingress tests
pytest test_k8s/test_health_endpoint.py -m ingress -v

# Exclude NodePort tests (used in k8s-tests)
pytest test_k8s/ -m 'not nodeport and not educational' -v
```

## Manual Testing

### Option 1: Use the Script (Recommended)
```bash
make health-tests
```

### Option 2: Manual Service Switching
```bash
# Switch to NodePort
kubectl patch service hello-flask -p '{"spec":{"type":"NodePort"}}'

# Get service URL
minikube service hello-flask --url

# Run tests
pytest test_k8s/test_health_endpoint.py -v

# Restore to ClusterIP
kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}'
```

### Option 3: Run Individual Tests
```bash
# After switching to NodePort
pytest test_k8s/test_health_endpoint.py::TestHealthEndpointDeployed::test_health_endpoint_via_nodeport -v
```

## What Gets Tested

The health endpoint tests verify:

### Performance
- Response time < liveness probe timeout (5s)
- Average latency < 1s
- Consistent performance across multiple requests

### Reliability
- 200 OK status code
- Correct JSON response: `{"status": "healthy"}`
- Consistent responses across all replicas

### Behavior
- Service availability during rolling updates
- Health check independence from readiness probe
- Configuration alignment with deployment manifest

### Educational Tests
- Liveness probe configuration validation
- Probe frequency analysis
- Comparison with readiness checks

## Best Practices

### During Development
1. Use `make health-tests` for comprehensive health endpoint validation
2. Run after changes to `/health` endpoint code
3. Run before modifying liveness probe configuration

### Pre-Commit
1. Use `make test-all` for fast automated tests
2. Health tests are optional but recommended for health-related changes

### Pre-Release
1. Use `make test-full` for complete validation
2. Includes health endpoint tests automatically

### CI/CD Pipeline
1. Use `make test-all` (excludes NodePort tests)
2. Health tests can be added as optional job for comprehensive validation

## Troubleshooting

### Health Tests Fail with "no node port" Error
**Cause:** Service is ClusterIP, not NodePort  
**Solution:** Use `make health-tests` (auto-switches) or manually switch service type

### Service Not Restored After Test Failure
**Cause:** Script interrupted before cleanup  
**Solution:** Manually restore:
```bash
kubectl patch service hello-flask -p '{"spec":{"type":"ClusterIP"}}'
```

### Tests Timeout
**Cause:** Service not ready or networking issue  
**Solution:** 
1. Check deployment: `kubectl get pods`
2. Verify service: `kubectl get service hello-flask`
3. Check Minikube: `minikube status`

## Architecture Decision

### Why Separate NodePort and Ingress Tests?

**Reasons for marker-based separation:**
1. **Service Type Requirements**: NodePort tests need direct pod access, Ingress tests validate external routing
2. **Deployment Realism**: ClusterIP + Ingress matches production patterns
3. **Test Efficiency**: Run appropriate tests for each service configuration
4. **Clear Intent**: Markers document what each test requires

**Test Distribution:**
- **7 NodePort tests**: Direct pod access for performance, consistency, behavior validation
- **1 Ingress test**: External monitoring access pattern
- **1 Educational test**: Demonstration with specific environment assumptions

### Solution Benefits

✅ **Consolidated but Organized**: All health tests in one file, separated by markers  
✅ **Service-Specific Testing**: Each test runs in appropriate service configuration  
✅ **No Conflicts**: NodePort tests excluded from k8s-tests, Ingress tests excluded from health-tests  
✅ **Automatic Switching**: `make health-tests` handles NodePort switching  
✅ **Flexible**: Run tests based on what you're validating  
✅ **Documented**: Clear markers indicate requirements

## Related Documentation

- [Test Architecture](architecture/TEST_ARCHITECTURE.md) - Overall test design
- [Unit Test Reference](UNIT_TEST_REFERENCE.md) - Unit testing guide
- [Probes Guide](../operations/probes/PROBES_GUIDE.md) - Liveness/readiness probes
- [Scripts README](../../scripts/README.md) - All automation scripts

## Quick Reference

```bash
# Quick validation (ClusterIP + Ingress)
make smoke-test

# Health endpoint testing (temporary NodePort)
make health-tests

# Full comprehensive testing (includes health tests)
make test-full

# Manual NodePort tests
pytest test_k8s/ -m nodeport -v

# Exclude NodePort tests
pytest test_k8s/ -m 'not nodeport' -v
```
