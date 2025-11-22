# Educational Ingress Tests - Complete Guide

**Purpose:** Comprehensive guide to educational tests that demonstrate how Kubernetes Ingress works internally.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What Educational Tests Teach](#what-educational-tests-teach)
3. [The Three Educational Tests](#the-three-educational-tests)
4. [How to Run Tests](#how-to-run-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Expected Output Examples](#expected-output-examples)
7. [Why These Tests Matter](#why-these-tests-matter)
8. [Integration with Documentation](#integration-with-documentation)
9. [Extending Educational Tests](#extending-educational-tests)
10. [Quick Reference](#quick-reference)

---

## Overview

### Purpose

**Standard tests answer:** "Does it work?"  
**Educational tests answer:** "How and why does it work?"

These tests are designed for:
- 📚 Learning Ingress concepts
- 🎓 Training team members
- 🔍 Demonstrating best practices
- 💡 Understanding troubleshooting techniques

### What Was Added

We've enhanced the repository with **3 new educational tests** that demonstrate advanced Ingress concepts. These tests go beyond basic validation to teach how Kubernetes Ingress works internally.

**Files Modified:**
- `/test_k8s/test_service_ingress.py` - Added 3 educational tests
- `/pytest.ini` - Added `educational` marker
- `/test_k8s/README.md` - Added educational tests section
- `/docs/README.md` - Updated documentation index

**Tests Added:** 3  
**Documentation Pages:** Multiple comprehensive guides  
**Learning Value:** 📈 Significantly Enhanced

---

## What Educational Tests Teach

### Philosophy: Tests as Teaching Tools

```
Standard Test:
  assert response.status_code == 200
  # Pass/Fail

Educational Test:
  # Test multiple scenarios
  correct_host → 200 OK
  wrong_host → 404 Not Found
  ip_as_host → 404 Not Found
  
  # Explain why
  print("📚 Learning: Ingress routes based on Host header!")
  
  # Show the pattern
  print(f"  - Host: {ingress_host} → 200 OK")
  print(f"  - Host: wrong → 404")
```

### Test Coverage Comparison

#### Before (Basic Validation):
- ✅ Ingress exists
- ✅ Ingress is reachable
- ✅ Returns 200 OK

**Answers:** "Does it work?"

#### After (Educational + Validation):
- ✅ All of the above, PLUS:
- 📚 Why Host header matters (hostname routing)
- 📚 How Ingress proxies without modification (consistency)
- 📚 Where load balancing happens (Service layer)

**Answers:** "Does it work? How does it work? Why does it work?"

---

## The Three Educational Tests

### 1. Hostname-Based Routing Test

**Test:** `test_hostname_routing_rejects_wrong_host`  
**File:** `test_k8s/test_service_ingress.py`  
**Duration:** ~5 seconds

#### What it teaches:
Ingress controllers route based on the HTTP `Host` header, not the URL path alone.

#### Demonstration:
```python
# ✅ Correct Host header → 200 OK
curl -H "Host: hello-flask.local" http://192.168.49.2
# Response: {"message": "Hello from Flask..."}

# ❌ Wrong Host header → 404 Not Found  
curl -H "Host: wrong-hostname.local" http://192.168.49.2
# Response: 404 page not found

# ❌ IP as Host → 404 Not Found
curl http://192.168.49.2
# Response: 404 page not found (Host header is the IP)
```

#### Key Learning:
- Ingress is a **Layer 7 (HTTP)** router, not Layer 4 (TCP)
- The routing decision is based on HTTP headers, specifically the `Host` header
- This is why `/etc/hosts` configuration matters for local development
- This is why CI/CD tests need to explicitly set the Host header

#### Real-world application:
- Understanding why different domains can route to different services
- Troubleshooting 404 errors when accessing via IP instead of hostname
- Setting up multi-tenant applications with hostname-based routing

---

### 2. Response Consistency Test

**Test:** `test_response_consistency_ingress_vs_direct`  
**File:** `test_k8s/test_service_ingress.py`  
**Duration:** ~10 seconds

#### What it teaches:
Ingress acts as a transparent proxy that doesn't modify application responses.

#### Demonstration:
```python
# Access via Ingress
response_ingress = requests.get("http://hello-flask.local")
# {"message": "Hello from Flask on Kubernetes (Minikube)!"}

# Access directly via port-forward (bypassing Ingress)
response_direct = requests.get("http://localhost:8080")
# {"message": "Hello from Flask on Kubernetes (Minikube)!"}

# Assertion: Both responses are identical
assert response_ingress.json() == response_direct.json()
```

#### Key Learning:
- Ingress is a **proxy/router**, not a modifier
- The application response is the same regardless of access method
- Ingress adds routing capabilities without changing application behavior
- Any differences in responses indicate misconfiguration or middleware issues

#### Real-world application:
- Debugging response inconsistencies
- Validating that Ingress annotations don't break application logic
- Understanding the separation between routing (Ingress) and application (Pods)
- Troubleshooting CORS, authentication, or header issues

---

### 3. Load Balancing Test

**Test:** `test_ingress_load_balancing`  
**File:** `test_k8s/test_service_ingress.py`  
**Duration:** ~30 seconds

#### What it teaches:
Load balancing happens at the Service layer, not the Ingress layer. Ingress routes to Services, and Services distribute to Pods.

#### Demonstration:
```
Request Flow:
Client → Ingress → Service → Pod (Round-robin across replicas)

Multiple Requests:
Request 1 → Ingress → Service → Pod 1
Request 2 → Ingress → Service → Pod 2  
Request 3 → Ingress → Service → Pod 1
...
```

#### The test:
1. Makes 20 HTTP requests through Ingress
2. Checks logs from each pod
3. Verifies multiple pods received traffic
4. Demonstrates distribution across replicas

#### Key Learning:
- **Ingress** routes to a **Service** (based on hostname/path)
- **Service** load balances to **Pods** (based on labels)
- Load balancing is automatic when you have multiple pod replicas
- This is how Kubernetes achieves high availability

#### Real-world application:
- Understanding traffic distribution in production
- Debugging why some pods get more traffic than others
- Planning for horizontal scaling (adding more replicas)
- Troubleshooting sticky session requirements

---

## How to Run Tests

### Run All Educational Tests

```bash
# All educational tests with output
pytest test_k8s/ -m educational -v -s

# Via Makefile
make educational-tests
```

### Run Specific Educational Test

```bash
# Hostname routing test
pytest test_k8s/test_service_ingress.py::test_hostname_routing_rejects_wrong_host -v -s

# Response consistency test
pytest test_k8s/test_service_ingress.py::test_response_consistency_ingress_vs_direct -v -s

# Load balancing test
pytest test_k8s/test_service_ingress.py::test_ingress_load_balancing -v -s
```

### Run All Ingress Tests (Basic + Educational)

```bash
# All Ingress tests
pytest test_k8s/ -m ingress -v -s

# Via Makefile
make ingress-tests
```

### Exclude Educational Tests

```bash
# Run only basic validation (exclude educational)
pytest test_k8s/ -m "ingress and not educational" -v
```

**Note:** Use `-s` flag to see the explanatory print statements during test execution.

---

## CI/CD Integration

### Current Behavior

#### ✅ Educational Tests **ARE INCLUDED** in CI/CD by Default

The educational tests run automatically in:
- `make k8s-tests`
- `make smoke-test`
- `make test-all`
- GitHub Actions CI/CD pipeline

### Why This Configuration?

**Rationale:**
1. **Comprehensive Validation** - Tests validate real Ingress behavior (routing, consistency, load balancing)
2. **Reasonable Overhead** - Only ~45 seconds extra on a 15-30 minute pipeline
3. **Ensures Tests Stay Working** - Educational tests won't break silently
4. **Demonstrates Full Capabilities** - Shows the repo's complete testing suite

### Test Execution Breakdown

#### Automated CI/CD Tests (Default)
```bash
pytest test_k8s/ -m "not manual"
```

**Includes:**
- ✅ Basic deployment tests
- ✅ ConfigMap/Secret tests
- ✅ Service tests (NodePort + Ingress)
- ✅ Basic Ingress tests
- ✅ **Educational Ingress tests** (hostname routing, consistency, load balancing)
- ✅ Liveness probe configuration tests

**Excludes:**
- ❌ Manual tests (pod deletion, crash recovery)

**Duration:** ~60-90 seconds

---

#### Manual Tests Only
```bash
pytest test_k8s/ -m manual
```

**Includes:**
- 🧪 Pod deletion test (~30s)
- 🧪 Container crash recovery test (~60s)

**Duration:** ~90 seconds

---

#### Educational Tests Only
```bash
pytest test_k8s/ -m educational
# OR
make educational-tests
```

**Includes:**
- 📚 Hostname-based routing test (~5s)
- 📚 Response consistency test (~10s)
- 📚 Load balancing test (~30s)

**Duration:** ~45 seconds

---

### Makefile Targets

#### New Targets Added:

```bash
# Run only educational tests
make educational-tests

# Run all Ingress tests (basic + educational)
make ingress-tests
```

#### Existing Targets (Unchanged):

```bash
# Run k8s tests (includes educational, excludes manual)
make k8s-tests

# Run smoke tests (includes educational, excludes manual)
make smoke-test

# Run all automated tests
make test-all
```

---

### Configuration Files

#### `pytest.ini`
```ini
[pytest]
addopts = -v -m "not manual"
markers =
    manual: marks tests as manual-only (not run in automated suite)
    educational: marks tests that demonstrate educational concepts
```

**Key Point:** Educational marker is defined but **NOT excluded** by default.

#### Scripts
- `scripts/k8s_tests.sh` - Uses `-m "not manual"` (includes educational)
- `scripts/smoke_test.sh` - Uses `-m "not manual"` (includes educational)

#### CI/CD Workflow
- `.github/workflows/ci-cd.yml` - Calls `scripts/k8s_tests.sh` (includes educational)

---

### How to Exclude Educational Tests (If Needed)

If you want to exclude educational tests from CI/CD in the future:

#### Option 1: Update `pytest.ini` (Global)
```ini
addopts = -v -m "not manual and not educational"
```

#### Option 2: Update Scripts (Per-script)
```bash
# In scripts/k8s_tests.sh and scripts/smoke_test.sh
run_pytest "test_k8s/" "-v -m 'not manual and not educational'"
```

#### Option 3: Update CI/CD Workflow (CI-only)
```yaml
- name: Run Kubernetes tests
  run: pytest test_k8s/ -v -m "not manual and not educational"
```

#### Option 4: Run Educational Tests Separately
```yaml
# Add a separate CI job for educational tests
- name: Run educational tests
  if: github.event_name == 'push'  # Only on push, not PR
  run: pytest test_k8s/ -m educational -v -s
```

---

### Recommendations

#### ✅ **Current Setup is Recommended**

**Keep educational tests in CI/CD because:**

1. **Low Cost** - 45 seconds on a 15-30 minute pipeline is negligible
2. **High Value** - Validates actual Ingress behavior, not just configuration
3. **Prevents Breakage** - Educational tests stay working and up-to-date
4. **Demonstrates Quality** - Shows comprehensive testing practices

#### 🎯 **When to Exclude Educational Tests**

Consider excluding if:
- CI/CD pipeline becomes too slow (>30 minutes)
- Running on resource-constrained CI runners
- Tests become flaky in CI environment
- Team prefers to run them manually during development

---

### Test Timing Summary

| Test Suite | Duration | Runs in CI/CD? |
|------------|----------|----------------|
| Unit tests | ~2s | ✅ Yes |
| Basic k8s tests | ~20s | ✅ Yes |
| **Educational tests** | **~45s** | **✅ Yes (current)** |
| Manual tests | ~90s | ❌ No |
| **Total automated** | **~70s** | |
| **Total with manual** | **~160s** | |

---

## Expected Output Examples

### Hostname Routing Test Output:
```
Testing hostname-based routing:
  Configured hostname: hello-flask.local
  Minikube IP: 192.168.49.2
  ✓ Request with correct Host header 'hello-flask.local': 200
  ✓ Request with wrong Host header 'wrong-hostname.local': 404
  ✓ Request with IP as Host header '192.168.49.2': 404

  📚 Learning: Ingress routes based on Host header, not URL!
     - Host: hello-flask.local → 200 OK
     - Host: wrong-hostname.local → 404 Not Found
     - Host: 192.168.49.2 → 404 Not Found
```

### Response Consistency Test Output:
```
  Response via Ingress: {'message': 'Hello from Flask on Kubernetes (Minikube)!'}
  Starting port-forward to hello-flask:5000...
  Response via port-forward: {'message': 'Hello from Flask on Kubernetes (Minikube)!'}

  ✓ Responses are identical via Ingress and direct access
  📚 Learning: Ingress proxies requests without modifying responses
```

### Load Balancing Test Output:
```
  Testing load balancing across 2 pods:
    - hello-flask-5d856bb855-abc123
    - hello-flask-5d856bb855-xyz789

  Making 20 requests to observe load distribution...
  ✓ Successfully completed 20/20 requests
    ✓ Pod hello-flask-5d856bb855-abc123 received requests
    ✓ Pod hello-flask-5d856bb855-xyz789 received requests

  📚 Learning: 2/2 pods received traffic
  ✓ Load balancing is working - multiple pods handled requests
```

---

## Why These Tests Matter

### For Learning:
- 🎓 Teaches **why** things work, not just **if** they work
- 📚 Demonstrates core Kubernetes concepts
- 💡 Provides hands-on troubleshooting experience

### For the Repository:
- Transforms a simple demo into a comprehensive learning platform
- Complements existing documentation (INGRESS_GUIDE.md, etc.)
- Provides concrete examples of abstract concepts

### For Teams:
- Onboarding tool for new team members
- Training resource for Kubernetes concepts
- Troubleshooting reference

### Why Not Run by Default (Historical Note):

These tests were initially considered optional because:
1. **Slower execution** - They involve port-forwarding, multiple requests, and log checking (~30-60 seconds)
2. **Educational focus** - They demonstrate concepts rather than validate deployment health
3. **Not critical for basic CI/CD** - Basic Ingress tests already validate core functionality
4. **Optional learning** - Teams can choose when to run them for training purposes

**Current Decision:** Include by default for comprehensive validation and continuous education.

### When to Run Them:
- 🎓 Onboarding new team members to Kubernetes
- 📚 Teaching Ingress concepts in training sessions
- 🔍 Troubleshooting complex routing issues
- 💡 Understanding why certain configurations work or fail
- 🛠️ Demonstrating best practices to stakeholders
- ✅ **Automatically in CI/CD** (current configuration)

---

## Integration with Documentation

These tests complement the existing documentation:

| Existing Doc | Educational Test |
|--------------|------------------|
| `INGRESS_GUIDE.md` | `test_hostname_routing_rejects_wrong_host` demonstrates Host header behavior |
| `INGRESS_GUIDE.md` | All tests show environment detection (CI vs local) |
| `README.md` deployment steps | Tests validate the steps actually work |

### Cross-References

**From Test Suite:**
- Tests validate concepts explained in [Ingress Guide](../../../operations/ingress/INGRESS_GUIDE.md)
- Demonstrates environment detection discussed in CI/CD sections
- Practical examples of troubleshooting steps

**To Test Suite:**
- Documentation references test examples
- Troubleshooting guides mention running educational tests
- Quick reference guides link to test commands

---

## Extending Educational Tests

Want to add more educational tests? Follow this pattern:

### Template for New Educational Tests

```python
@pytest.mark.ingress
@pytest.mark.educational
def test_your_concept(service, ingress, k8s_timeouts):
    """
    Educational: Explain what concept this demonstrates.
    
    This demonstrates [concept] by [method].
    """
    # 1. Setup and explain what you're testing
    print(f"\nTesting [concept]:")
    
    # 2. Perform the test with multiple scenarios
    # Show both what works and what doesn't
    
    # 3. Provide learning output
    print(f"\n  📚 Learning: [key takeaway]")
    print(f"     - [specific example]")
    
    # 4. Assert expected behavior
    assert expected_behavior
```

### Ideas for Additional Educational Tests:

- **Path-based routing** - Different paths to different services
- **TLS certificate validation** - HTTPS with certificates
- **Request/response header manipulation** - Custom headers through Ingress
- **Custom error pages** - 404, 503 error handling
- **Rate limiting and throttling** - Traffic control
- **Websocket support** - Websockets through Ingress
- **Canary deployments** - Weighted routing for gradual rollouts
- **Session affinity** - Sticky sessions with cookies
- **CORS configuration** - Cross-origin resource sharing
- **Authentication** - OAuth/JWT validation at Ingress level

### Best Practices for Educational Tests:

1. **Clear Documentation** - Explain what concept is being demonstrated
2. **Multiple Scenarios** - Show both success and failure cases
3. **Learning Output** - Print educational messages during execution
4. **Real-world Context** - Explain when/why this matters in production
5. **Self-contained** - Test should be understandable on its own
6. **Markers** - Use `@pytest.mark.educational` for easy discovery
7. **Reasonable Duration** - Keep tests under 1 minute each when possible

---

## Quick Reference

### Common Commands

```bash
# Run all educational tests
pytest test_k8s/ -m educational -v -s
make educational-tests

# Run specific test
pytest test_k8s/test_service_ingress.py::test_hostname_routing_rejects_wrong_host -v -s

# Run all Ingress tests (basic + educational)
pytest test_k8s/ -m ingress -v -s
make ingress-tests

# Exclude educational tests
pytest test_k8s/ -m "ingress and not educational" -v
```

### When to Use Each Test

| Scenario | Command |
|----------|---------|
| **Learning Ingress** | `pytest -m educational -v -s` |
| **Onboarding new team member** | `pytest -m educational -v -s` |
| **Quick validation (CI/CD)** | `pytest test_k8s/ -v` (default, includes educational) |
| **Full test suite** | `pytest test_k8s/ -v -m ""` |
| **Troubleshooting routing** | Run Test 1 (hostname routing) |
| **Debugging responses** | Run Test 2 (consistency) |
| **Understanding traffic flow** | Run Test 3 (load balancing) |

### Test Execution Time

| Test | Duration |
|------|----------|
| Hostname Routing | ~5 seconds |
| Response Consistency | ~10 seconds |
| Load Balancing | ~30 seconds |
| **Total** | **~45 seconds** |

### Key Learnings Summary

#### Test 1: Hostname Routing
```
✅ Host: hello-flask.local → 200 OK
❌ Host: wrong-hostname.local → 404 Not Found
❌ Host: 192.168.49.2 (IP) → 404 Not Found
```
**Takeaway:** Ingress is Layer 7 (HTTP), routes on Host header

#### Test 2: Response Consistency
```
Ingress response == Direct response
```
**Takeaway:** Ingress doesn't modify application responses

#### Test 3: Load Balancing
```
Request flow: Client → Ingress → Service → Pods (round-robin)
```
**Takeaway:** Service distributes traffic, not Ingress

---

## Summary

**Educational tests transform this repository from a simple demo into a comprehensive learning platform.**

### What Makes These Tests Special:

✅ **Well-documented** - Comprehensive guide (this document)  
✅ **Well-integrated** - Linked from test README and docs index  
✅ **Well-marked** - Use `@pytest.mark.educational` for easy discovery  
✅ **Well-explained** - Include learning output during execution  
✅ **Practical** - Demonstrate real troubleshooting scenarios  
✅ **Included in CI/CD** - Run automatically to ensure quality

### Questions They Answer:

- ❓ Why does Ingress need `/etc/hosts` configuration?
- ❓ Why do CI/CD tests use Host headers?
- ❓ How does traffic flow from client to pod?
- ❓ What's the difference between Ingress and Service?
- ❓ Where does load balancing actually happen?

### Metrics:

**Files Modified:** 4  
**Files Created:** 4 (documentation)  
**Tests Added:** 3  
**Documentation Pages:** Multiple comprehensive guides  
**Lines of Code:** ~250  
**Learning Value:** 📈 Significantly Enhanced  
**CI/CD Overhead:** ~45 seconds (minimal impact)  

**Result:** Anyone using this repository learns not just *how* to deploy Ingress, but *why* it works the way it does! 🎯

---

## Related Documentation

### Internal Documentation
- **[EDUCATIONAL_TESTS_QUICKREF.md](EDUCATIONAL_TESTS_QUICKREF.md)** - Quick command reference
- **[Ingress Guide](../../../operations/ingress/INGRESS_GUIDE.md)** - Complete Ingress troubleshooting
- **[Test Architecture](../../architecture/TEST_ARCHITECTURE.md)** - Test suite design
- **[Test Usage Guide](../../../../test_k8s/README.md)** - How to run and write tests

### External Resources
- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest Markers](https://docs.pytest.org/en/stable/how-to/mark.html)

---

**Last Updated:** November 21, 2025  
**Maintained By:** Project Team  
**Feedback:** Open an issue or PR for improvements
