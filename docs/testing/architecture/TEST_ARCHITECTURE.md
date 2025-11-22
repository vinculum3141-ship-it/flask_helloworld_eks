# Test Suite Architecture

## Overview

The `test_k8s` directory uses a modular architecture with shared utilities, pytest fixtures, and custom markers for organized, maintainable testing.

---

## Current Architecture

```
test_k8s/
│
├── __init__.py                    ← Package marker
├── README.md                      ← Documentation
│
├── utils.py ─────────────────────┐
│   │                              │
│   ├── run_kubectl()              │
│   ├── get_pods()                 │
│   ├── get_running_pods()         │  Shared
│   ├── get_pod_restart_count()    │  Utilities
│   ├── wait_for_pods_ready()      │  (20+ functions)
│   ├── get_deployment()           │
│   ├── get_service()              │
│   ├── get_ingress()              │
│   ├── exec_in_pod()              │
│   ├── delete_pod()               │
│   ├── print_debug_info()         │
│   └── ... more utilities         │
│                                  │
├── conftest.py ──────────────────┐│
│   │                             ││
│   ├── Fixtures:                 ││  Pytest
│   │   ├── deployment            ││  Config
│   │   ├── service               ││  & Fixtures
│   │   ├── ingress               ││
│   │   ├── pods                  ││
│   │   ├── running_pods          ││
│   │   ├── k8s_timeouts          ││
│   │   └── debug_on_failure      ││
│   │                             ││
│   └── Markers:                  ││
│       ├── @pytest.mark.manual   ││
│       ├── @pytest.mark.slow     ││
│       ├── @pytest.mark.ingress  ││
│       └── @pytest.mark.nodeport ││
│                                 ││
├── test_configmap.py ────────────┼┤
│   └── Uses: utils, fixtures     ││
│                                 ││
├── test_deployment.py ───────────┼┤
│   └── Uses: utils, fixtures     ││
│                                 ││
├── test_ingress.py ──────────────┼┤
│   └── Uses: utils, fixtures     ││
│                                 ││
├── test_liveness_probe.py ───────┼┤
│   └── Uses: utils, fixtures     ││
│       (liveness probe only)     ││
│                                 ││  All Tests
├── test_readiness_probe.py ──────┼┤  Import From
│   └── Uses: utils, fixtures     ││  Shared Modules
│       (readiness probe only)    ││
│                                 ││
├── test_crash_recovery_manual.py ┼┤
│   └── Uses: utils, fixtures     ││
│                                 ││
├── test_service_nodeport.py ─────┼┤
│   ├── @pytest.mark.nodeport     ││
│   └── Uses: utils, fixtures     ││
│       (focused on NodePort)     ││
│                                 ││
├── test_service_ingress.py ──────┼┤
│   ├── @pytest.mark.ingress      ││
│   └── Uses: utils, fixtures     ││
│       (focused on Ingress)      ││
│                                 ││
└── test_service_access.py ───────┼┤  (Legacy - kept for
    └── Uses: utils, fixtures     ││   backward compatibility)
                                  ││
        ┌─────────────────────────┘│
        │  ┌───────────────────────┘
        ▼  ▼
    Shared Dependencies
```

**Key Features:**
- ✅ Zero duplicate code (shared utilities)
- ✅ 20+ reusable utility functions
- ✅ 10+ pytest fixtures for automated setup
- ✅ Consistent error handling
- ✅ Clear separation of concerns (liveness vs readiness)
- ✅ Environment-aware timeouts
- ✅ Comprehensive debugging tools
- ✅ Custom pytest markers for test categorization

---

## Architecture Evolution

The test suite was refactored from individual test files with duplicated helper functions to a modular architecture with shared utilities and pytest fixtures.

**Previous Issues (now resolved):**
- Duplicate code (~200 lines across files)
- No shared utilities
- Inconsistent error handling  
- Mixed concerns (NodePort + Ingress in one file)
- Hardcoded timeouts

**Current Benefits:**
- Single source of truth for Kubernetes operations
- DRY principle applied throughout
- Reusable fixtures reduce boilerplate
- Focused test files with clear purposes
- Environment-aware configuration

---

## Data Flow Example

### Test Execution with Fixtures and Utilities

```
Test Function
    ↓
conftest.py provides fixtures (deployment, service, etc.)
    ↓
utils.get_deployment() / utils.get_service()
    ↓
Centralized error handling with KubectlError
    ↓
Type-hinted return values (Dict[str, Any])
    ↓
Auto-skip if resource not found (using pytest.skip)
    ↓
Environment-aware timeouts (k8s_timeouts fixture)
```

**Example Flow:**
1. Test requests `deployment` fixture
2. Fixture calls `utils.get_deployment("hello-flask")`
3. Utility runs kubectl, parses JSON, handles errors
4. Returns deployment resource or skips test
5. Test uses resource with confidence (type-safe, validated)

---

## Test Execution Flow

### CI/CD Environment
```
pytest test_k8s/ -v -m "not manual"
    ↓
conftest.py detects CI environment
    ↓
k8s_timeouts fixture sets longer timeouts
    ↓
Tests run with appropriate waits
    ↓
Auto-skip @pytest.mark.manual tests
```

### Local Development
```
pytest test_k8s/ -v
    ↓
conftest.py detects local environment
    ↓
k8s_timeouts fixture sets shorter timeouts
    ↓
Tests run faster
    ↓
Can optionally run manual tests
```

---

## Dependency Graph

```
┌─────────────────────────────────────────┐
│         Python Standard Library         │
│  (subprocess, json, time, typing, os)   │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│            External: pytest              │
│         (pytest, requests)               │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│          test_k8s/utils.py               │
│    (Kubernetes operation wrappers)       │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│        test_k8s/conftest.py              │
│    (Pytest fixtures using utils)         │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
┌──────────────┐  ┌──────────────┐
│  Unit Tests  │  │ Integration  │
│              │  │    Tests     │
│ • configmap  │  │ • ingress    │
│ • deployment │  │ • nodeport   │
│ • liveness   │  │ • manual     │
└──────────────┘  └──────────────┘
```

---

## Marker Usage

```
@pytest.mark.manual
    ↓
    Used for: test_crash_recovery_manual.py
    Purpose: Skip in CI, run manually
    
@pytest.mark.slow
    ↓
    Used for: Tests with long waits
    Purpose: Skip in quick test runs
    
@pytest.mark.ingress
    ↓
    Used for: test_service_ingress.py, test_ingress.py
    Purpose: Only run when Ingress is configured
    
@pytest.mark.nodeport
    ↓
    Used for: test_service_nodeport.py
    Purpose: Only run when NodePort is configured
```

Filter tests:
```bash
# Ingress tests only
pytest -m ingress

# Everything except manual
pytest -m "not manual"

# Specific combinations
pytest -m "ingress and not slow"
```

---

## Benefits Summary

The modular architecture provides significant improvements:

| Area | Improvement | Impact |
|------|-------------|--------|
| **Code Reuse** | Eliminated ~200 lines of duplication | DRY principle applied |
| **Maintainability** | Single source of truth for operations | Easy to update/fix |
| **Debugging** | Fixtures + debug utilities | Faster troubleshooting |
| **Organization** | Clear separation of concerns | Easier to navigate |
| **Testability** | Markers enable selective execution | Flexible test runs |
| **Reliability** | Consistent error handling | Fewer edge cases |

**Key Metrics:**
- **20+ shared utility functions** - Kubernetes operations centralized
- **10+ pytest fixtures** - Automated test setup and teardown
- **4 custom markers** - Test categorization and filtering
- **0 code duplication** - DRY principle throughout
- **Environment-aware** - Different behavior for CI vs local

---

## Related Documentation

- **[Test Refactoring](TEST_REFACTORING.md)** - Detailed refactoring history and changes
- **[Script Integration](SCRIPT_INTEGRATION.md)** - How scripts use pytest markers
- **[Test Usage Guide](../../test_k8s/README.md)** - Complete test documentation and examples
- **[Conftest.py](../../test_k8s/conftest.py)** - Fixture and marker definitions
- **[Utils.py](../../test_k8s/utils.py)** - Shared utility functions
