# Kubernetes Ingress Guide

**Purpose:** Comprehensive guide to understanding and troubleshooting Kubernetes Ingress host-based routing in local and CI/CD environments.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Understanding Ingress Host-Based Routing](#understanding-ingress-host-based-routing)
3. [Common Problem: 404 Errors Explained](#common-problem-404-errors-explained)
4. [Solutions by Environment](#solutions-by-environment)
5. [How the Test Suite Handles This](#how-the-test-suite-handles-this)
6. [Testing & Verification](#testing--verification)
7. [Debugging Guide](#debugging-guide)
8. [Common Issues & Solutions](#common-issues--solutions)
9. [Quick Reference](#quick-reference)

---

## Overview

This guide addresses the most common Ingress issue: **404 errors when accessing via IP address instead of hostname**.

### What You'll Learn

- ✅ Why Ingress returns 404 for IP-based access
- ✅ How Nginx Ingress uses HTTP Host headers for routing
- ✅ Solutions for local development vs CI/CD environments
- ✅ How to debug Ingress issues systematically
- ✅ How the test suite automatically handles different environments

### Quick Summary

🔑 **Key Insight:** Nginx Ingress routing is based on the `Host` HTTP header, not the IP address in the URL!

- `http://192.168.49.2` → Header: `Host: 192.168.49.2` → **404 (no match)**
- `http://hello-flask.local` → Header: `Host: hello-flask.local` → **200 ✓ (matches rule)**
- `http://192.168.49.2` + `Host: hello-flask.local` header → **200 ✓ (matches rule)**

---

## Understanding Ingress Host-Based Routing

### How Ingress Configuration Works

Our Ingress configuration specifies a hostname-based routing rule:

```yaml
# In k8s/ingress.yaml:
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-flask-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: hello-flask.local  # ← Nginx matches this against the Host HTTP header
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hello-flask
            port:
              number: 5000
```

### How Nginx Ingress Controller Routes Requests

The Nginx Ingress Controller inspects the **HTTP `Host` header** (not the URL) to determine routing:

1. Client sends HTTP request
2. Nginx examines `Host:` header in the HTTP request
3. Nginx compares header value against configured `host:` rules
4. If match found → route to backend service
5. If no match → return 404 Not Found

---

## Common Problem: 404 Errors Explained

### The Problem

When using Ingress with a hostname rule, you get a 404 when accessing via IP address directly.

### Visual Flow Diagrams

#### ❌ Request via IP (404 Not Found)

```
Client → http://192.168.49.2
         │
         ▼
    Nginx Ingress Controller
         │
         ├─ Checks: Host header = "192.168.49.2"
         ├─ Compares with rule: "hello-flask.local"
         ├─ Result: NO MATCH ✗
         │
         ▼
    Returns: 404 Not Found
```

**HTTP Request Sent:**
```http
GET / HTTP/1.1
Host: 192.168.49.2       ← Doesn't match "hello-flask.local"
```

**Why it fails:** The `Host` header is automatically set to the IP address from the URL, which doesn't match the configured routing rule.

---

#### ✅ Request via Hostname (200 OK)

```
Client → http://hello-flask.local
         │
         ▼
    Nginx Ingress Controller
         │
         ├─ Checks: Host header = "hello-flask.local"
         ├─ Compares with rule: "hello-flask.local"
         ├─ Result: MATCH! ✓
         │
         ▼
    Routes to: hello-flask Service
         │
         ▼
    Flask Application
         │
         ▼
    Returns: 200 OK (Flask app response)
```

**HTTP Request Sent:**
```http
GET / HTTP/1.1
Host: hello-flask.local  ← Matches rule!
```

**Why it works:** The `Host` header matches the configured routing rule.

---

#### ✅ Request via IP with Host Header (200 OK)

```
Client → http://192.168.49.2
         + Header: "Host: hello-flask.local"
         │
         ▼
    Nginx Ingress Controller
         │
         ├─ Checks: Host header = "hello-flask.local"  ← From explicit header, not URL!
         ├─ Compares with rule: "hello-flask.local"
         ├─ Result: MATCH! ✓
         │
         ▼
    Routes to: hello-flask Service
         │
         ▼
    Flask Application
         │
         ▼
    Returns: 200 OK (Flask app response)
```

**HTTP Request Sent:**
```http
GET / HTTP/1.1
Host: hello-flask.local  ← Manually set header matches rule!
```

**Why it works:** Even though the URL uses an IP, the explicitly set `Host` header matches the routing rule.

---

### Why This Matters in Different Environments

#### Local Development
- `/etc/hosts` file configured with: `192.168.49.2 hello-flask.local`
- Browser/curl resolves `hello-flask.local` to IP
- Host header automatically set correctly
- **Result:** Everything works seamlessly ✓

#### CI/CD Environments (GitHub Actions)
- No `/etc/hosts` configuration
- Can't resolve `hello-flask.local` hostname
- Must use IP address directly
- **Problem:** Default Host header doesn't match routing rule
- **Solution:** Explicitly set Host header (see Solutions section)

---

## Solutions by Environment

### Solution 1: Local Development (Use Hostname via /etc/hosts)

**Best for:** Local development, manual testing

**Setup:**
```bash
# Automated setup (recommended)
bash scripts/setup_ingress.sh

# Manual setup (if needed)
echo "$(minikube ip) hello-flask.local" | sudo tee -a /etc/hosts
```

**Usage:**
```bash
# Access via hostname
curl http://hello-flask.local

# Or in browser
open http://hello-flask.local
```

**Pros:**
- ✅ Natural and intuitive
- ✅ Works like production with real DNS
- ✅ No special headers needed

**Cons:**
- ⚠️ Requires /etc/hosts modification (sudo)
- ⚠️ Doesn't work in CI/CD without workflow changes

---

### Solution 2: CI/CD Environment (Use IP + Host Header)

**Best for:** CI/CD pipelines, automated testing

**Current Implementation (Recommended):**

The test suite automatically detects CI/CD environment and uses Minikube IP with the correct Host header.

**How it works:**

The `is_ci_environment()` utility function (in `test_k8s/utils.py`) detects GitHub Actions:

```python
def is_ci_environment() -> bool:
    """Detect if running in CI/CD environment."""
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
```

**Implementation in tests:**
```python
def get_ingress_url():
    """Get Ingress URL appropriate for current environment."""
    if is_ci_environment():
        # CI/CD: Use Minikube IP with Host header
        minikube_ip = get_minikube_ip()
        return f"http://{minikube_ip}", {"Host": "hello-flask.local"}
    else:
        # Local: Use hostname (via /etc/hosts)
        return "http://hello-flask.local", {}

# Usage in tests
url, headers = get_ingress_url()
response = requests.get(url, headers=headers)
```

**Manual usage:**
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Send correct Host header
curl -H "Host: hello-flask.local" http://$MINIKUBE_IP

# Expected output: {"message": "Hello from Flask on Kubernetes (Minikube)!"}
```

**Pros:**
- ✅ Works in any environment (no /etc/hosts needed)
- ✅ Tests actual Ingress routing logic
- ✅ Automatic environment detection

**Cons:**
- ⚠️ Requires explicit header management in code
- ⚠️ Less intuitive for manual testing

**Test files using this approach:**
- `test_k8s/test_service_ingress.py` - Ingress-based access tests
- `test_k8s/test_service_access.py` - Legacy file (backward compatibility)

---

### Solution 2b: Configure /etc/hosts in CI/CD Workflow (Alternative)

**Best for:** Making CI/CD tests identical to local tests

**Implementation:**

Add `/etc/hosts` entry in the GitHub Actions workflow before running tests:

```yaml
- name: Configure /etc/hosts for Ingress
  if: ${{ github.event_name != 'pull_request' }}
  run: |
    INGRESS_IP=$(kubectl get ingress hello-flask-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "127.0.0.1")
    echo "$INGRESS_IP hello-flask.local" | sudo tee -a /etc/hosts
    echo "Added to /etc/hosts: $INGRESS_IP hello-flask.local"
    cat /etc/hosts | grep hello-flask
```

**Pros:**
- ✅ Tests work exactly as in local development
- ✅ No code changes needed
- ✅ Natural hostname resolution

**Cons:**
- ⚠️ Requires workflow modification
- ⚠️ May need sudo permissions
- ⚠️ Workflow-specific (not portable)

---

### Solution 3: Bypass Ingress (Port Forward)

**Best for:** Debugging, direct service access

**Implementation:**

```bash
# Port-forward directly to service (bypasses Ingress)
kubectl port-forward svc/hello-flask 5000:5000 &

# Access service directly
curl http://localhost:5000

# Stop port-forward
kill %1
```

**In tests:**
```python
def get_service_url_via_port_forward():
    """Access service via port-forward (bypasses Ingress)."""
    # Start port-forward in background
    process = subprocess.Popen(
        ["kubectl", "port-forward", "svc/hello-flask", "5000:5000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for port-forward to be ready
    time.sleep(2)
    
    return "http://localhost:5000", process
```

**Pros:**
- ✅ Bypasses Ingress entirely (good for debugging)
- ✅ Works in any environment
- ✅ No DNS or routing configuration needed

**Cons:**
- ⚠️ Doesn't test Ingress configuration
- ⚠️ Adds process management complexity
- ⚠️ Not representative of production traffic flow

---

## How the Test Suite Handles This

### Automatic Environment Detection

The test suite automatically adapts to the environment:

**In CI/CD Environment:**
```
Detected CI environment - using Minikube IP with Host header
Using Minikube IP: 192.168.49.2
Setting Host header: hello-flask.local
Testing via Ingress: http://192.168.49.2
✓ Service is reachable
```

**In Local Development:**
```
Using Ingress hostname: hello-flask.local
Testing via Ingress: http://hello-flask.local
✓ Service is reachable
```

### Test Implementation Example

From `test_k8s/test_service_ingress.py`:

```python
def test_service_via_ingress(running_pods, service, ingress):
    """Test accessing the service through Ingress."""
    
    # Automatically detect environment and get appropriate URL
    if is_ci_environment():
        url = f"http://{get_minikube_ip()}"
        headers = {"Host": "hello-flask.local"}
    else:
        url = "http://hello-flask.local"
        headers = {}
    
    # Make request
    response = requests.get(url, headers=headers, timeout=10)
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Flask" in data["message"]
```

---

## Testing & Verification

### Run Tests Locally

```bash
# Run Ingress tests (uses hostname via /etc/hosts)
pytest test_k8s/test_service_ingress.py -v -s

# Expected: Uses http://hello-flask.local
```

### Simulate CI Environment Locally

```bash
# Force CI mode (uses IP + Host header)
export CI=true
pytest test_k8s/test_service_ingress.py -v -s

# Expected: Uses http://192.168.49.2 with Host header
```

### Test Locally with Same Sequence as CI

Run the exact same sequence locally to reproduce CI behavior:

```bash
# 1. Start Minikube
minikube start

# 2. Enable Ingress
minikube addons enable ingress

# 3. Wait for Ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

# 4. Deploy application
bash scripts/deploy_local.sh

# 5. Check /etc/hosts configuration
grep hello-flask.local /etc/hosts

# 6. Run tests
pytest test_k8s/test_service_ingress.py -v -s
```

### Manual Verification Commands

```bash
# Test 1: Direct IP (should fail with 404)
curl -v http://$(minikube ip)
# Expected: 404 Not Found

# Test 2: IP with Host header (should succeed)
curl -v -H "Host: hello-flask.local" http://$(minikube ip)
# Expected: 200 OK with Flask response

# Test 3: Hostname (should succeed if /etc/hosts configured)
curl -v http://hello-flask.local
# Expected: 200 OK with Flask response

# Test 4: Check Ingress routing configuration
kubectl get ingress hello-flask-ingress -o yaml | grep -A 5 "rules:"
# Expected: Shows host: hello-flask.local
```

---

## Debugging Guide

### Quick Debugging Checklist

Before diving into detailed debugging, verify these basics:

- [ ] Minikube is running: `minikube status`
- [ ] Ingress controller is enabled and ready
- [ ] Ingress resource has an IP address assigned
- [ ] Service is ClusterIP type (not NodePort when using Ingress)
- [ ] `/etc/hosts` is configured (local) or using IP with Host header (CI)
- [ ] Pods are running and ready
- [ ] Test can resolve/reach the URL

### Step-by-Step Debugging Process

#### Step 1: Check Ingress Controller Status

```bash
# Verify Ingress controller is running
kubectl get pods -n ingress-nginx

# Expected output:
# NAME                                        READY   STATUS    RESTARTS
# ingress-nginx-controller-xxxx               1/1     Running   0
```

**If controller is not running:**
```bash
# Enable Ingress addon
minikube addons enable ingress

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
```

---

#### Step 2: Verify Ingress Resource

```bash
# Check Ingress resource exists and has address
kubectl get ingress hello-flask-ingress

# Expected output:
# NAME                  CLASS   HOSTS                 ADDRESS         PORTS   AGE
# hello-flask-ingress   nginx   hello-flask.local     192.168.49.2    80      5m
```

**If ADDRESS is empty or pending:**
- Wait a few moments (can take 30-60 seconds)
- Check Ingress controller logs (see Step 6)

**Get detailed Ingress information:**
```bash
kubectl describe ingress hello-flask-ingress
```

Look for:
- `Rules:` section shows correct host (`hello-flask.local`)
- `Backend:` shows correct service (`hello-flask:5000`)
- `Events:` section for any errors or warnings

---

#### Step 3: Test Ingress Access Manually

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# Test 1: Direct IP (should fail with 404)
echo "Test 1: Direct IP access"
curl -v http://$MINIKUBE_IP
# Expected: 404 (proves Ingress is working, just not routing)

# Test 2: IP with Host header (should succeed)
echo "Test 2: IP with Host header"
curl -v -H "Host: hello-flask.local" http://$MINIKUBE_IP
# Expected: 200 with Flask response

# Test 3: Hostname (if /etc/hosts configured)
echo "Test 3: Hostname access"
curl -v http://hello-flask.local
# Expected: 200 with Flask response
```

---

#### Step 4: Check Backend Service and Pods

```bash
# Verify pods are running
kubectl get pods -l app=hello-flask

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# hello-flask-xxxxxxxxx-xxxxx    1/1     Running   0          5m
# hello-flask-xxxxxxxxx-xxxxx    1/1     Running   0          5m

# Check service configuration
kubectl get svc hello-flask

# Expected output (should be ClusterIP):
# NAME          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
# hello-flask   ClusterIP   10.96.123.45    <none>        5000/TCP   5m

# Describe service for details
kubectl describe svc hello-flask
```

**If pods are not ready:**
```bash
# Check pod logs
kubectl logs -l app=hello-flask --tail=50

# Check pod events
kubectl describe pod -l app=hello-flask
```

---

#### Step 5: Verify Service Type

**Important:** When using Ingress, the Service should be `ClusterIP`, not `NodePort`.

```bash
# Check service type
kubectl get svc hello-flask -o jsonpath='{.spec.type}'
# Expected: ClusterIP

# If it's NodePort, this can cause conflicts with Ingress
```

---

#### Step 6: Check Ingress Controller Logs

```bash
# View Ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=50

# Look for:
# - Routing decisions
# - Backend health checks
# - Error messages
# - SSL/TLS issues

# Follow logs in real-time while testing
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller -f
```

Then in another terminal, make a test request:
```bash
curl -H "Host: hello-flask.local" http://$(minikube ip)
```

Watch the logs for routing decisions.

---

#### Step 7: Verify /etc/hosts Configuration (Local Development)

```bash
# Check if /etc/hosts has Ingress entry
grep hello-flask.local /etc/hosts

# Expected output:
# 192.168.49.2 hello-flask.local

# If missing, add it:
echo "$(minikube ip) hello-flask.local" | sudo tee -a /etc/hosts

# Test DNS resolution
ping -c 1 hello-flask.local
# Should resolve to Minikube IP
```

---

### Add Debug Output to GitHub Actions

Add these commands before running tests in your workflow to get detailed state information:

```yaml
- name: Debug Kubernetes State
  run: |
    echo "=== Minikube Status ==="
    minikube status
    minikube ip
    
    echo "=== Ingress Controller Status ==="
    kubectl get pods -n ingress-nginx
    kubectl get svc -n ingress-nginx
    
    echo "=== Ingress Resource ==="
    kubectl get ingress -A
    kubectl describe ingress hello-flask-ingress
    
    echo "=== Service Configuration ==="
    kubectl get svc hello-flask -o yaml
    
    echo "=== Pod Status ==="
    kubectl get pods -l app=hello-flask -o wide
    kubectl describe pods -l app=hello-flask
    
    echo "=== Pod Logs ==="
    kubectl logs -l app=hello-flask --tail=20
    
    echo "=== Ingress Controller Logs ==="
    kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
    
    echo "=== /etc/hosts Content ==="
    cat /etc/hosts
    
    echo "=== Network Connectivity ==="
    curl -v -H "Host: hello-flask.local" http://$(minikube ip) || echo "Ingress access failed"
```

---

### Manual Service Test in CI (Debugging)

If you need to bypass Ingress for debugging in CI:

```yaml
- name: Debug - Direct Service Access
  run: |
    # Port-forward to service (bypasses Ingress)
    kubectl port-forward svc/hello-flask 5000:5000 &
    PF_PID=$!
    
    # Wait for port-forward to be ready
    sleep 3
    
    # Test direct service access
    echo "Testing direct service access via port-forward:"
    curl -v http://localhost:5000
    
    # Clean up
    kill $PF_PID
```

---

## Common Issues & Solutions

### Issue 1: 404 Not Found

**Symptom:**
```bash
$ curl http://192.168.49.2
404 page not found
```

**Root Cause:** Host header doesn't match Ingress routing rule

**Solution:**
```bash
# Use Host header
curl -H "Host: hello-flask.local" http://192.168.49.2

# Or configure /etc/hosts and use hostname
curl http://hello-flask.local
```

---

### Issue 2: Connection Refused

**Symptom:**
```bash
$ curl http://hello-flask.local
curl: (7) Failed to connect to hello-flask.local port 80: Connection refused
```

**Root Cause:** Minikube not running or Ingress controller not ready

**Solution:**
```bash
# Check Minikube status
minikube status

# Start if needed
minikube start

# Check Ingress controller
kubectl get pods -n ingress-nginx

# Enable if needed
minikube addons enable ingress
```

---

### Issue 3: Hostname Not Resolving

**Symptom:**
```bash
$ curl http://hello-flask.local
curl: (6) Could not resolve host: hello-flask.local
```

**Root Cause:** `/etc/hosts` not configured or incorrect IP

**Solution:**
```bash
# Option 1: Configure /etc/hosts (local development)
echo "$(minikube ip) hello-flask.local" | sudo tee -a /etc/hosts

# Verify
cat /etc/hosts | grep hello-flask

# Option 2: Use IP with Host header (CI/CD)
curl -H "Host: hello-flask.local" http://$(minikube ip)
```

---

### Issue 4: Ingress Has No IP Address

**Symptom:**
```bash
$ kubectl get ingress
NAME                  CLASS   HOSTS                 ADDRESS   PORTS
hello-flask-ingress   nginx   hello-flask.local               80
```

**Root Cause:** Ingress controller not running or not ready

**Solution:**
```bash
# Check Ingress controller status
kubectl get pods -n ingress-nginx

# If not running, enable addon
minikube addons enable ingress

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

# Check again (may take 30-60 seconds)
kubectl get ingress hello-flask-ingress
```

---

### Issue 5: Test Fails in CI but Works Locally

**Symptom:**
```
AssertionError: Failed to reach service at http://hello-flask.local
```

**Root Cause:** CI environment doesn't have /etc/hosts configured

**Solution:**

The test suite should automatically detect CI and use IP with Host header. If not working:

```python
# Verify is_ci_environment() is working
import os
print(f"CI env var: {os.getenv('CI')}")
print(f"GITHUB_ACTIONS: {os.getenv('GITHUB_ACTIONS')}")

# Should return True in GitHub Actions
```

Or manually set in workflow:
```yaml
- name: Run tests
  env:
    CI: true
  run: pytest test_k8s/test_service_ingress.py -v
```

---

### Issue 6: Service Type Conflicts

**Symptom:** Ingress and NodePort both configured, unpredictable behavior

**Root Cause:** Service type should be ClusterIP when using Ingress

**Solution:**
```bash
# Check service type
kubectl get svc hello-flask -o jsonpath='{.spec.type}'

# If it's NodePort, change to ClusterIP
# Edit k8s/service.yaml:
#   type: ClusterIP  # Not NodePort

# Reapply
kubectl apply -f k8s/service.yaml
```

---

## Quick Reference

### Common Commands Cheat Sheet

```bash
# === Minikube ===
minikube status                    # Check if running
minikube ip                        # Get cluster IP
minikube addons enable ingress     # Enable Ingress addon
minikube addons list              # List all addons

# === Ingress Controller ===
kubectl get pods -n ingress-nginx                        # Check controller status
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=50   # View logs

# === Ingress Resource ===
kubectl get ingress                                     # List all Ingress resources
kubectl get ingress hello-flask-ingress                # Get specific Ingress
kubectl describe ingress hello-flask-ingress           # Detailed Ingress info
kubectl get ingress hello-flask-ingress -o yaml        # Full YAML configuration

# === Service & Pods ===
kubectl get svc hello-flask                            # Check service
kubectl get pods -l app=hello-flask                    # Check application pods
kubectl describe svc hello-flask                       # Service details
kubectl logs -l app=hello-flask --tail=50              # Application logs

# === Testing Access ===
# Direct IP (should fail with 404)
curl http://$(minikube ip)

# IP with Host header (should succeed)
curl -H "Host: hello-flask.local" http://$(minikube ip)

# Hostname (if /etc/hosts configured)
curl http://hello-flask.local

# Port-forward (bypass Ingress)
kubectl port-forward svc/hello-flask 5000:5000
curl http://localhost:5000

# === /etc/hosts Management ===
# View current entries
cat /etc/hosts | grep hello-flask

# Add entry
echo "$(minikube ip) hello-flask.local" | sudo tee -a /etc/hosts

# Remove entry (macOS/Linux)
sudo sed -i '' '/hello-flask.local/d' /etc/hosts
```

### Decision Tree: Which Solution to Use?

```
Are you in a CI/CD pipeline?
│
├─ YES → Use Solution 2: IP + Host Header
│         • Automatic with is_ci_environment()
│         • curl -H "Host: hello-flask.local" http://$(minikube ip)
│
└─ NO → Are you doing local development?
        │
        ├─ YES → Use Solution 1: /etc/hosts + Hostname
        │         • bash scripts/setup_ingress.sh
        │         • curl http://hello-flask.local
        │
        └─ NO → Need to debug Ingress issues?
                │
                └─ YES → Use Solution 3: Port Forward
                          • kubectl port-forward svc/hello-flask 5000:5000
                          • curl http://localhost:5000
```

### Key Takeaways Summary

| Scenario | URL | Host Header | Result |
|----------|-----|-------------|--------|
| Direct IP | `http://192.168.49.2` | `192.168.49.2` (auto) | ❌ 404 |
| Hostname (with /etc/hosts) | `http://hello-flask.local` | `hello-flask.local` (auto) | ✅ 200 |
| IP + Manual Header | `http://192.168.49.2` | `hello-flask.local` (manual) | ✅ 200 |
| Port Forward | `http://localhost:5000` | N/A (bypasses Ingress) | ✅ 200 |

🔑 **Remember:** Nginx Ingress routing matches on the HTTP `Host` header, not the URL!

---

## Related Documentation

### Internal Documentation
- **[CI/CD Guide](../CI_CD_GUIDE.md)** - Complete CI/CD pipeline reference
- **[Probes Guide](../probes/PROBES_GUIDE.md)** - Kubernetes health probes configuration
- **[Test Architecture](../../testing/architecture/TEST_ARCHITECTURE.md)** - Test suite design
- **[Test Usage Guide](../../../test_k8s/README.md)** - How to run and write tests

### External Resources
- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Minikube Ingress DNS](https://minikube.sigs.k8s.io/docs/handbook/addons/ingress-dns/)
- [GitHub Actions Debugging](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

---

**Last Updated:** November 21, 2025  
**Maintained By:** Project Team  
**Feedback:** Open an issue or PR for improvements
