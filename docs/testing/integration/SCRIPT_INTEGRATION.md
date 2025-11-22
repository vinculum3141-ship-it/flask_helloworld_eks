# Script Integration with Pytest Markers

## Overview

This document describes how the bash scripts in `scripts/` integrate with pytest markers to control test execution. The scripts support selective test execution based on test categorization.

---

## Script Test Execution Behavior

### 1. **scripts/k8s_tests.sh** - Automated CI Tests

**Pytest Arguments:** `-v -m 'not manual'`

**What it runs:**
- All Kubernetes integration tests except those marked `@pytest.mark.manual`
- Includes: deployment, configmap, service, ingress configuration tests
- Excludes: Timing-dependent behavioral tests (pod deletion, crash recovery)

**Usage:**
```bash
make k8s-tests
```

**Purpose:** Fast, reliable automated testing suitable for CI/CD pipelines.

---

### 2. **scripts/smoke_test.sh** - Quick Validation

**Pytest Arguments:** `-v -m 'not manual'`

**What it runs:**
- Same as `k8s_tests.sh` - fast configuration validation
- Quick smoke test to verify deployment health
- Excludes slow manual tests

**Usage:**
```bash
make smoke-test
```

**Purpose:** Rapid deployment validation during development.

---

### 3. **scripts/liveness_test.sh** - Liveness Probe Testing

**Pytest Arguments (default):** `test_k8s/test_liveness_probe.py -v -s`
**Pytest Arguments (with --manual):** `-v -s -m manual`

**What it runs:**
- **Without flag:** Configuration tests for liveness probe setup (/health endpoint)
- **With --manual flag:** Behavioral tests (pod deletion, auto-recovery)

**Usage:**
```bash
make liveness-test         # Config only (fast)
make liveness-test-manual  # Behavioral tests (slow)
```

---

### 4. **scripts/readiness_test.sh** - Readiness Probe Testing

**Pytest Arguments (default):** `test_k8s/test_readiness_probe.py -v -s`
**Pytest Arguments (with --manual):** `-v -s -m manual -k readiness`

**What it runs:**
- **Without flag:** Configuration tests for readiness probe setup (/ready endpoint)
- **With --manual flag:** Behavioral tests (traffic routing validation)

**Usage:**
```bash
make readiness-test         # Config only (fast)
make readiness-test-manual  # Behavioral tests
```

**Purpose:** Targeted liveness probe testing with optional behavioral validation.

---

### 4. **scripts/port_forward.sh** - Manual Helper (Not a Test)

**Type:** Manual utility script

**CI Coverage Note:**
```bash
# Service reachability is validated in pytest via:
#   test_k8s/test_service_nodeport.py (NodePort service type)
#   test_k8s/test_service_ingress.py (ClusterIP with Ingress)
```

**Usage:**
```bash
bash scripts/port_forward.sh
```

**Purpose:** Quick local manual testing via port forwarding.

---

### 5. **scripts/minikube_service_url.sh** - Manual Helper (Not a Test)

**Type:** Manual utility script

**CI Coverage Note:**
```bash
# In CI, this functionality is tested via pytest:
#   - test_k8s/test_service_nodeport.py (NodePort tests)
#   - test_k8s/test_service_ingress.py (Ingress tests)
```

**Usage:**
```bash
bash scripts/minikube_service_url.sh
```

**Purpose:** Get service URL for local development testing.


---

## Pytest Marker Reference

### Available Markers

Defined in `test_k8s/conftest.py`:

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.manual` | Timing-dependent behavioral tests | Excluded from automated CI |
| `@pytest.mark.slow` | Tests that take longer to execute | May be filtered in CI |
| `@pytest.mark.ingress` | Requires Ingress controller setup | Auto-skipped if Ingress unavailable |
| `@pytest.mark.nodeport` | Requires NodePort service type | For NodePort-specific tests |

### Marker Usage in Scripts

| Script | Marker Filter | Tests Included |
|--------|--------------|----------------|
| `k8s_tests.sh` | `-m 'not manual'` | All except manual |
| `smoke_test.sh` | `-m 'not manual'` | All except manual |
| `liveness_test.sh` (default) | None (specific file) | Config tests only |
| `liveness_test.sh --manual` | `-m manual` | Only manual tests |

---

## Running Tests Manually

### Run All Tests (Including Manual)
```bash
pytest test_k8s/ -v
```

### Run Only Manual Tests
```bash
pytest test_k8s/ -v -m manual
```

### Run Specific Test Categories
```bash
pytest test_k8s/ -v -m ingress      # Only Ingress tests
pytest test_k8s/ -v -m nodeport     # Only NodePort tests
pytest test_k8s/ -v -m slow         # Only slow tests
```

### Run Tests Excluding Multiple Categories
```bash
pytest test_k8s/ -v -m 'not manual and not slow'
```

---

## Related Documentation

- **Test Architecture:** `docs/testing/TEST_ARCHITECTURE.md` - Overall test structure
- **Test Refactoring:** `docs/testing/TEST_REFACTORING.md` - Python test refactoring details
- **Test Usage Guide:** `test_k8s/README.md` - Comprehensive test documentation
- **Pytest Configuration:** `test_k8s/conftest.py` - Fixtures and marker definitions
- **Scripts README:** `scripts/README.md` - All available scripts documentation
