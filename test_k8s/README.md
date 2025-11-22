# Test Refactoring Documentation

## Overview

The `test_k8s` directory has been refactored to improve maintainability, debuggability, and organization of Kubernetes integration tests.

## Test Files Reference

This section explains what each test file does and when to run it.

### Core Infrastructure Tests

#### `test_deployment.py` - Pod Status Verification
**Purpose:** Verifies that Kubernetes Deployment creates and maintains healthy pods.

**What it tests:**
- ✅ Pods exist with the correct label (`app=hello-flask`)
- ✅ All pods are in `Running` state
- ✅ Expected number of replicas are running (default: 3)
- ✅ Pod status validation

**Markers:** None (runs automatically)

**When to run:** Always - this is a fundamental health check

**Example:**
```bash
pytest test_k8s/test_deployment.py -v
```

---

#### `test_configmap.py` - ConfigMap Configuration Validation
**Purpose:** Verifies that ConfigMap is properly configured and injected into pods.

**What it tests:**
- ✅ ConfigMap resource exists in cluster (`hello-config`)
- ✅ ConfigMap has correct keys (`APP_ENV`, `LOG_LEVEL`)
- ✅ ConfigMap values are correct (`APP_ENV=local`, `LOG_LEVEL=debug`)
- ✅ Deployment references ConfigMap correctly (via `envFrom`)
- ✅ Environment variables are accessible inside pods
- ✅ All ConfigMap values are injected into pods

**Markers:** None (runs automatically)

**When to run:** After deploying ConfigMap, to verify configuration injection

**Example:**
```bash
pytest test_k8s/test_configmap.py -v
```

---

#### `test_secret.py` - Secret Configuration Validation
**Purpose:** Verifies that Secret is properly configured, base64-encoded, and injected into pods.

**What it tests:**
- ✅ Secret resource exists in cluster (`hello-secrets`)
- ✅ Secret has correct keys (`API_KEY`, `DB_PASSWORD`)
- ✅ Secret values are properly base64-encoded
- ✅ Secret values decode to expected plaintext
- ✅ Deployment references Secret correctly (via `envFrom`)
- ✅ Environment variables from Secret are accessible inside pods (decoded)
- ✅ All Secret values are injected into pods with correct decoded values

**Markers:** None (runs automatically)

**When to run:** After deploying Secret, to verify secure configuration injection

**Example:**
```bash
pytest test_k8s/test_secret.py -v
```

---

#### `test_app_config.py` - Application Configuration Behavior
**Purpose:** Verifies that the application can access and use configuration from environment variables.

**What it tests:**
- ✅ Pods have all expected configuration environment variables available
- ✅ Variables from ConfigMap are accessible (`APP_ENV`, `LOG_LEVEL`)
- ✅ Variables from Secret are accessible (`API_KEY`, `DB_PASSWORD`)
- ✅ Variables from deployment env are accessible (`CUSTOM_MESSAGE`)
- ⚠️ App behavior changes based on config (skipped if app doesn't expose `/env` endpoint)

**Markers:** `@pytest.mark.ingress` (for HTTP endpoint tests)

**When to run:** To verify end-to-end configuration flow from K8s resources to application

**Example:**
```bash
pytest test_k8s/test_app_config.py -v
```

**Note:** One test is skipped if the app doesn't expose an `/env` endpoint for introspection.

---

### Service Access Tests

#### `test_service_nodeport.py` - NodePort Service Access
**Purpose:** Verifies NodePort service accessibility and configuration.

**What it tests:**
- ✅ Service type is `NodePort`
- ✅ Service has a NodePort assigned in valid range (30000-32767)
- ✅ Service is reachable via `minikube service` URL
- ✅ HTTP endpoint returns expected response
- ✅ Service points to correct pods

**Markers:** `@pytest.mark.nodeport`

**When to run:** When using NodePort service type (simpler local testing)

**Example:**
```bash
pytest test_k8s/test_service_nodeport.py -v
# Or run all NodePort tests
pytest test_k8s/ -v -m nodeport
```

**Note:** This test only runs when service type is `NodePort` (skips for ClusterIP)

---

#### `test_service_ingress.py` - Ingress Service Access
**Purpose:** Verifies Ingress-based service accessibility with proper routing.

**What it tests:**
- ✅ Service type is `ClusterIP` (used with Ingress)
- ✅ Ingress route is reachable via host header (`hello-flask.local`)
- ✅ HTTP endpoint returns expected response
- ✅ Ingress correctly routes to backend service
- ✅ Environment-aware testing (local vs CI/CD)

**Markers:** `@pytest.mark.ingress`

**When to run:** When using Ingress controller (production-like setup)

**Example:**
```bash
pytest test_k8s/test_service_ingress.py -v
# Or run all Ingress tests
pytest test_k8s/ -v -m ingress

# Simulate CI/CD environment (uses Minikube IP + Host header)
CI=true pytest test_k8s/test_service_ingress.py -v -s
```

**Environment detection:**
- **Local:** Uses `http://hello-flask.local` (requires `/etc/hosts` configured)
- **CI/CD:** Uses `http://<minikube-ip>` with `Host: hello-flask.local` header

**Tip:** Use `CI=true` to test the CI/CD behavior locally without modifying `/etc/hosts`

---

#### `test_ingress.py` - Ingress Resource Configuration
**Purpose:** Verifies Ingress resource is properly configured with correct rules.

**What it tests:**
- ✅ Ingress resource exists (`hello-flask-ingress`)
- ✅ Ingress has correct host configured (`hello-flask.local`)
- ✅ Ingress has correct path rules (`/` routes to `hello-flask` service)
- ✅ Ingress backend service is correct (port 5000)
- ✅ Ingress has an address assigned (load balancer IP)

**Markers:** `@pytest.mark.ingress`

**When to run:** When using Ingress controller, to verify routing configuration

**Example:**
```bash
pytest test_k8s/test_ingress.py -v
```

**Note:** This test skips if Ingress is not deployed

---

### Health & Self-Healing Tests

#### `test_liveness_probe.py` - Probe Configuration
**Purpose:** Verifies that liveness and readiness probes are correctly configured.

**What it tests:**
- ✅ Liveness probe is configured on containers
- ✅ Liveness probe uses correct endpoint (`/`)
- ✅ Liveness probe has correct port (5000)
- ✅ Readiness probe is configured on containers
- ✅ Readiness probe uses correct endpoint (`/`)
- ✅ Readiness probe has correct port (5000)

**Markers:** None (runs automatically)

**When to run:** Always - ensures self-healing configuration is correct

**Example:**
```bash
pytest test_k8s/test_liveness_probe.py -v
```

**Note:** This only tests probe **configuration**, not behavioral aspects (see manual tests below)

---

#### `test_crash_recovery_manual.py` - Self-Healing Behavior (Manual)
**Purpose:** Verifies Kubernetes self-healing mechanisms through destructive testing.

**What it tests:**
- 🧪 **Pod Deletion Test** (`test_self_healing_pod_deletion`)
  - Deletes a pod
  - Verifies ReplicaSet creates a replacement pod
  - Confirms desired replica count is restored
  - Validates new pod becomes Running and Ready

- 🧪 **Container Crash Test** (`test_container_restart_on_crash`)
  - Kills the main process (PID 1) inside a container
  - Verifies liveness probe detects the failure
  - Confirms container is automatically restarted
  - Validates restart count increments

**Markers:** `@pytest.mark.manual`, `@pytest.mark.slow`

**When to run:** Manually, for thorough validation (not in automated CI/CD)

**Why manual?**
- ⏱️ Tests involve wait times (60-90 seconds)
- 🎲 Timing-dependent (Kubernetes reconciliation loops)
- 💥 Destructive (deletes pods, kills processes)
- 🔍 Best verified with manual observation

**Examples:**
```bash
# Run all manual tests
pytest test_k8s/ -m manual -v -s

# Run only pod deletion test
pytest test_k8s/test_crash_recovery_manual.py::test_self_healing_pod_deletion -v -s -m ""

# Run only crash recovery test
pytest test_k8s/test_crash_recovery_manual.py::test_container_restart_on_crash -v -s -m ""
```

**Note:** Use `-s` flag to see real-time output during waits

---

### Educational Tests

#### Educational Ingress Tests (`test_service_ingress.py`)
**Purpose:** Demonstrate advanced Ingress concepts through hands-on testing.

These tests go beyond basic functionality to teach how Ingress works internally.

**What it teaches:**

- 📚 **Hostname-Based Routing** (`test_hostname_routing_rejects_wrong_host`)
  - Shows that Ingress routes based on HTTP Host header, not URL
  - Correct Host header (`hello-flask.local`) → 200 OK
  - Wrong Host header (`wrong-hostname.local`) → 404 Not Found
  - IP as Host header (Minikube IP) → 404 Not Found
  - **Learning:** Ingress is a Layer 7 (HTTP) router, not Layer 4 (TCP)

- 📚 **Response Consistency** (`test_response_consistency_ingress_vs_direct`)
  - Compares responses via Ingress vs direct service access (port-forward)
  - Validates that Ingress proxies without modifying responses
  - Both access methods return identical JSON responses
  - **Learning:** Ingress acts as a transparent proxy/router

- 📚 **Load Balancing** (`test_ingress_load_balancing`)
  - Makes multiple requests through Ingress to observe distribution
  - Checks pod logs to verify multiple pods receive traffic
  - Shows how Service load balances across pod replicas
  - **Learning:** Ingress → Service → Pods (load balancing happens at Service layer)

**Markers:** `@pytest.mark.ingress`, `@pytest.mark.educational`

**When to run:** For learning and demonstration purposes

**Examples:**
```bash
# Run all educational tests
pytest test_k8s/ -m educational -v -s

# Run specific educational test
pytest test_k8s/test_service_ingress.py::test_hostname_routing_rejects_wrong_host -v -s

# Run all Ingress tests (including educational)
pytest test_k8s/ -m ingress -v -s
```

**Why these tests are educational:**
- 🎓 They explain **WHY** things work, not just **IF** they work
- 🔍 They demonstrate underlying mechanisms (Host headers, proxying, load balancing)
- 💡 They include explanatory output messages during execution
- 📖 They're tagged separately so they can be run on-demand for learning

**Note:** These tests may take longer than basic validation tests (~30-60 seconds) because they:
- Use port-forward (2-3 second setup time)
- Make multiple HTTP requests (20+ for load balancing test)
- Check pod logs to observe traffic distribution

---

## Test Summary Table

| Test File | Purpose | Markers | Auto/Manual | Duration |
|-----------|---------|---------|-------------|----------|
| `test_deployment.py` | Pod status verification | - | Auto | Fast (~2s) |
| `test_configmap.py` | ConfigMap validation (5 tests) | - | Auto | Fast (~2s) |
| `test_secret.py` | Secret validation (6 tests) | - | Auto | Fast (~1s) |
| `test_app_config.py` | App config availability (2 tests) | `ingress` | Auto | Medium (~6s) |
| `test_service_nodeport.py` | NodePort service access | `nodeport` | Auto | Medium (~5s) |
| `test_service_ingress.py` | Ingress service access (3 basic) | `ingress` | Auto | Medium (~5s) |
| `test_service_ingress.py` | Educational Ingress tests (3 tests) | `ingress`, `educational` | On-demand | Slow (~30-60s) |
| `test_ingress.py` | Ingress resource config | `ingress` | Auto | Fast (~2s) |
| `test_liveness_probe.py` | Probe configuration | - | Auto | Fast (~2s) |
| `test_crash_recovery_manual.py` | Self-healing behavior | `manual`, `slow` | Manual | Slow (~60-90s) |

**Total automated test time:** ~20-25 seconds (excludes educational and manual tests)  
**Total educational test time:** ~30-60 seconds (run with `-m educational`)  
**Total manual test time:** ~60-90 seconds (run with `-m manual`)

**Marker Usage:**
```bash
# Run only automated tests (default)
pytest test_k8s/ -v

# Run only educational tests
pytest test_k8s/ -m educational -v -s

# Run only manual tests
pytest test_k8s/ -m manual -v -s

# Run Ingress tests (basic + educational)
pytest test_k8s/ -m ingress -v

# Run everything including manual and educational
pytest test_k8s/ -v -s -m ""
```

---

## Key Improvements

### 1. Shared Utilities Module (`utils.py`)

**Purpose**: Centralize common helper functions to eliminate code duplication.

**Key Functions**:

**kubectl Operations:**
- `run_kubectl()` - Execute kubectl commands with consistent error handling

**Pod Operations:**
- `get_pods()` - Retrieve pods by label selector
- `get_pod_by_name()` - Get specific pod by name
- `get_pod_restart_count()` - Get restart count for a pod
- `get_running_pods()` - Get only running and ready pods
- `wait_for_pods_ready()` - Wait for specific number of pods to be ready
- `exec_in_pod()` - Execute commands inside pods
- `delete_pod()` - Delete a pod

**Resource Operations:**
- `get_deployment()` - Retrieve deployment by name
- `get_service()` - Retrieve service by name
- `get_ingress()` - Retrieve ingress by name
- `get_configmap()` - Retrieve ConfigMap by name
- `get_secret()` - Retrieve Secret by name
- `deployment_references_resource()` - Check if deployment references ConfigMap/Secret via envFrom

**Environment & Debugging:**
- `is_ci_environment()` - Detect CI/CD environment
- `print_debug_info()` - Print comprehensive debugging information
- `get_minikube_ip()`, `get_service_url()` - Minikube utilities

**Benefits**:
- Single source of truth for kubectl operations
- Consistent error handling across all tests
- Better type hints and documentation
- Reusable deployment reference checking logic
- Easier to maintain and extend

### 2. Pytest Configuration (`conftest.py`)

**Purpose**: Provide reusable fixtures and test configuration.

**Key Fixtures**:

**Resource Name Fixtures:**
- `deployment_name` - Returns "hello-flask" deployment name
- `service_name` - Returns "hello-flask" service name  
- `ingress_name` - Returns "hello-flask-ingress" ingress name
- `configmap_name` - Returns "hello-config" ConfigMap name
- `secret_name` - Returns "hello-secrets" Secret name
- `label_selector` - Returns "app=hello-flask" label selector

**Resource Object Fixtures:**
- `deployment` - Auto-retrieve deployment object (skips if not found)
- `service` - Auto-retrieve service object (skips if not found)
- `ingress` - Auto-retrieve ingress object (skips if not found)
- `configmap` - Auto-retrieve ConfigMap object (skips if not found)
- `secret` - Auto-retrieve Secret object (skips if not found)

**Pod State Fixtures:**
- `pods` - Get current pod list matching label selector
- `running_pods` - Get only running and ready pods

**Environment & Helper Fixtures:**
- `ci_environment` - Detect CI/CD environment
- `k8s_timeouts` - Environment-appropriate timeouts
- `debug_on_failure` - Automatic debug output on test failure
- `wait_for_stable_state` - Helper for waiting for pod stability

**Custom Markers**:
- `@pytest.mark.manual` - Tests that should only be run manually
- `@pytest.mark.slow` - Tests that take longer than usual
- `@pytest.mark.ingress` - Tests requiring Ingress controller
- `@pytest.mark.nodeport` - Tests requiring NodePort service type

**Benefits**:
- Reduced boilerplate in test functions
- Automatic resource retrieval with skipping if not found
- Centralized resource names (single source of truth)
- Better timeout management for CI vs local environments
- Organized test categorization with markers

### 3. Test File Organization

#### Original Structure
```
test_k8s/
├── test_configmap.py
├── test_deployment.py
├── test_ingress.py
├── test_liveness_probe.py
├── test_crash_recovery_manual.py
└── test_service_access.py  (mixed concerns)
```

#### New Structure
```
test_k8s/
├── utils.py                      # NEW: Shared utilities
├── conftest.py                   # NEW: Pytest configuration
├── test_configmap.py             # REFACTORED: Uses utils
├── test_deployment.py            # REFACTORED: Uses utils
├── test_ingress.py               # REFACTORED: Uses utils & fixtures
├── test_liveness_probe.py        # REFACTORED: Uses utils & fixtures
├── test_crash_recovery_manual.py # REFACTORED: Uses utils & fixtures
├── test_service_nodeport.py      # NEW: Split from test_service_access
└── test_service_ingress.py       # NEW: Split from test_service_access
```

### 4. Specific Improvements by File

#### `test_liveness_probe.py`
- **Before**: Local functions for kubectl, duplicated code
- **After**: Uses shared utilities and deployment fixture
- **Benefits**: Cleaner, more focused test functions

#### `test_crash_recovery_manual.py`
- **Before**: Duplicate kubectl wrappers, hardcoded timeouts
- **After**: Uses shared utilities, `k8s_timeouts` fixture, better debugging
- **Benefits**: Adapts to CI/CD environment, better error messages

#### `test_service_access.py` → Split into Two Files
- **`test_service_nodeport.py`**: 
  - Tests specific to NodePort service type
  - Clearer focus on NodePort-specific functionality
  - Uses `@pytest.mark.nodeport` marker

- **`test_service_ingress.py`**:
  - Tests specific to Ingress-based access
  - Clearer focus on Ingress functionality
  - Uses `@pytest.mark.ingress` marker

- **Benefits**: 
  - Better separation of concerns
  - Easier to run subset of tests
  - Clearer test intent

#### `test_configmap.py`
- **Before**: Used shell subprocess with minikube kubectl
- **After**: Uses `exec_in_pod()` utility and `pods` fixture
- **Benefits**: More robust, better error handling

#### `test_deployment.py`
- **Before**: Subprocess calls with JSON parsing
- **After**: Uses `pods` fixture
- **Benefits**: Simplified, leverages fixture auto-skipping

#### `test_ingress.py`
- **Before**: Repeated subprocess calls, hardcoded timeouts
- **After**: Uses `ingress` fixture, `k8s_timeouts`, utilities
- **Benefits**: Environment-aware timeouts, cleaner code

## Usage Examples

### Running Tests with Markers

```bash
# Run all tests
pytest test_k8s/ -v

# Run only Ingress tests
pytest test_k8s/ -v -m ingress

# Run only NodePort tests
pytest test_k8s/ -v -m nodeport

# Skip manual tests (default in CI)
pytest test_k8s/ -v -m "not manual"

# Run manual tests explicitly
pytest test_k8s/ -v -m manual

# Run specific test file
pytest test_k8s/test_liveness_probe.py -v
```

### Using Utilities in New Tests

```python
from .utils import get_pods, wait_for_pods_ready, print_debug_info

def test_my_feature(pods, k8s_timeouts):
    """Example test using utilities and fixtures."""
    # pods fixture auto-retrieves pods
    initial_count = len(pods)
    
    # Make some changes...
    
    # Wait for stability with environment-appropriate timeout
    timeout = k8s_timeouts['pod_ready']
    success = wait_for_pods_ready(initial_count, timeout=timeout)
    
    if not success:
        # Print debug info on failure
        print_debug_info()
    
    assert success, "Pods did not become ready in time"
```

### Using Fixtures

```python
def test_deployment_replicas(deployment, running_pods):
    """Example using deployment and running_pods fixtures."""
    desired = deployment['spec']['replicas']
    actual = len(running_pods)
    
    assert actual == desired, \
        f"Expected {desired} running pods, got {actual}"
```

**Using ConfigMap and Secret fixtures:**
```python
def test_configmap_values(configmap):
    """Example using configmap fixture - auto-retrieved and skips if not found."""
    data = configmap.get("data", {})
    assert "APP_ENV" in data, "ConfigMap missing APP_ENV key"

def test_secret_base64(secret):
    """Example using secret fixture."""
    import base64
    data = secret.get("data", {})
    decoded = base64.b64decode(data["API_KEY"]).decode('utf-8')
    assert decoded == "somesecretkey"

def test_deployment_references(deployment, configmap_name, secret_name):
    """Example using deployment_references_resource utility."""
    from .utils import deployment_references_resource
    
    assert deployment_references_resource(deployment, "configmap", configmap_name)
    assert deployment_references_resource(deployment, "secret", secret_name)
```

## Migration Guide

If you're updating an existing test:

1. **Remove local helper functions** that duplicate `utils.py` functionality
2. **Add fixture parameters** to test functions (e.g., `deployment`, `pods`)
3. **Replace subprocess calls** with utility functions
4. **Use `k8s_timeouts`** instead of hardcoded timeout values
5. **Add appropriate markers** (`@pytest.mark.ingress`, etc.)
6. **Import from utils**: `from .utils import function_name`

## Debugging

### Enable Debug Output on Failure

Add `debug_on_failure` to your test:

```python
def test_something(debug_on_failure):
    # Test code...
    pass
```

Or enable for entire module:
```python
pytestmark = pytest.mark.usefixtures("debug_on_failure")
```

### Manual Debug Info

```python
from .utils import print_debug_info

# In your test:
print_debug_info()  # Prints pods, deployment, service status
```

### Check Specific Resources

```python
from .utils import get_pods, get_pod_logs

pods = get_pods("app=hello-flask")
for pod in pods:
    name = pod['metadata']['name']
    logs = get_pod_logs(name, tail=50)
    print(f"Pod {name} logs:\n{logs}")
```

## Benefits Summary

✅ **Reduced Code Duplication**: ~200 lines of duplicate code eliminated  
✅ **Better Error Handling**: Consistent error messages and exceptions  
✅ **Improved Debugging**: Automatic debug output, helper functions  
✅ **Environment Awareness**: Different timeouts for CI vs local  
✅ **Better Organization**: Clear separation of concerns  
✅ **Easier Maintenance**: Single source of truth for common operations  
✅ **More Testable**: Isolated, focused test functions  
✅ **Better Documentation**: Type hints, docstrings, examples  

## Future Enhancements

Potential improvements for the future:

1. Add more utility functions as patterns emerge
2. Create custom assertions (e.g., `assert_pod_ready()`)
3. Add performance benchmarking fixtures
4. Create test data factories for complex scenarios
5. Add integration with test reporting tools
6. Create visual test reports with pod state diagrams
