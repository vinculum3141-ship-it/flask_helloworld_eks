# Kubernetes Probes Guide

**Purpose:** Comprehensive guide to understanding and configuring Kubernetes liveness and readiness probes for application health monitoring and self-healing.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Probe Types](#probe-types)
- [Liveness Probe](#liveness-probe)
- [Readiness Probe](#readiness-probe)
- [Probes Working Together](#probes-working-together)
- [Configuration Reference](#configuration-reference)
- [Testing & Verification](#testing--verification)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

Kubernetes probes are **health checks** that determine the state of your application containers. They enable:

- ✅ **Automatic crash recovery** (liveness probe)
- ✅ **Intelligent traffic routing** (readiness probe)
- ✅ **Self-healing applications** (both probes)
- ✅ **Zero-downtime deployments** (readiness probe)

### The Three Questions Probes Answer

| Probe | Question | Action on Failure |
|-------|----------|-------------------|
| **Startup** | "Has the app finished starting?" | Delays liveness/readiness checks |
| **Liveness** | "Is the app still alive?" | **Restart container** 🔄 |
| **Readiness** | "Is the app ready for traffic?" | Remove from Service (no restart) |

**This repository uses:** Liveness + Readiness probes (no startup probe needed for this simple app)

---

## Probe Types

### Probe Check Methods

Kubernetes supports three ways to check health:

#### 1. **HTTP GET** (Used in this repo)
```yaml
httpGet:
  path: /
  port: 5000
```
- Sends HTTP GET request
- Success: HTTP 200-399
- Failure: Any other response or timeout

#### 2. **TCP Socket**
```yaml
tcpSocket:
  port: 5000
```
- Attempts TCP connection
- Success: Connection established
- Failure: Connection refused or timeout

#### 3. **Exec Command**
```yaml
exec:
  command:
  - cat
  - /tmp/healthy
```
- Runs command in container
- Success: Exit code 0
- Failure: Non-zero exit code

**Why HTTP GET?** Best for REST APIs - tests actual app functionality, not just container/port availability.

---

## Liveness Probe

### Purpose: Detect Crashed or Deadlocked Containers

**Question:** "Is my application still alive, or is it stuck/crashed?"

**Action on Failure:** Restart the container (destructive but healing)

### Current Configuration

From `k8s/deployment.yaml`:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### How It Works

**Timeline:**

```
Container Start
    │
    ├─ t=0s:   Container starts
    ├─ t=0-10s: Initial delay (no checks)
    │
    ├─ t=10s:  First liveness check → GET http://pod-ip:5000/health
    │          ✅ Success (200 OK) → Container healthy
    │
    ├─ t=20s:  Second check → GET http://pod-ip:5000/health
    │          ✅ Success → Container healthy
    │
    ├─ t=30s:  Third check → GET http://pod-ip:5000/health
    │          ✅ Success → Container healthy
    │
    └─ Checks continue every 10 seconds...
```

### Failure Scenario

**App crashes or deadlocks:**

```
t=30s:  Liveness check → GET http://pod-ip:5000/health
        ❌ FAILED (timeout after 5s or non-200 response)
        Failure count: 1/3
        
t=40s:  Liveness check → GET http://pod-ip:5000/health
        ❌ FAILED (still not responding)
        Failure count: 2/3
        
t=50s:  Liveness check → GET http://pod-ip:5000/health
        ❌ FAILED (3rd consecutive failure)
        Failure count: 3/3
        
        🔄 ACTION: RESTART CONTAINER
        
t=50s:  Container restarted
        RESTARTS count incremented (visible in kubectl get pods)
        
t=60s:  First liveness check after restart
        ✅ Success → Container healthy again
```

**Time to restart:** 30 seconds from first failure (10s period × 3 failures)

### What Triggers Liveness Failures

**Common scenarios:**

1. **Application Crash**
   ```
   Flask process exits → Container alive but app not responding
   → Liveness probe fails → Container restarted
   ```

2. **Deadlock/Hang**
   ```
   App stuck in infinite loop → Can't process HTTP requests
   → Liveness probe timeouts → Container restarted
   ```

3. **Out of Memory**
   ```
   Memory leak → OOM → App can't respond
   → Liveness probe fails → Container restarted
   ```

4. **Database Connection Loss** (if not handled)
   ```
   DB disconnects → App can't serve requests
   → Liveness probe fails → Container restarted → Reconnects
   ```

### Self-Healing Example

**Scenario: Flask process crashes**

```bash
# Initial state - pod running normally
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
hello-flask-5d856bb855-abc12   1/1     Running   0          5m

# Simulate crash - kill main process
$ kubectl exec hello-flask-5d856bb855-abc12 -- bash -c "kill -9 1"

# Immediately after - container still running but app dead
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
hello-flask-5d856bb855-abc12   0/1     Running   0          5m

# After ~30s of failed liveness checks
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
hello-flask-5d856bb855-abc12   0/1     Running   1          5m
#                                               ↑ Restart count increased

# Shortly after restart - app recovered
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
hello-flask-5d856bb855-abc12   1/1     Running   1          5m
#                              ↑ Ready again!
```

### Configuration Parameters Explained

| Parameter | Value | Why This Value? |
|-----------|-------|-----------------|
| `initialDelaySeconds` | 10 | Flask app starts in ~2-3s, 10s provides safety margin |
| `periodSeconds` | 10 | Check every 10s = balanced between responsiveness and overhead |
| `timeoutSeconds` | 5 | App normally responds in <100ms, 5s is very generous |
| `failureThreshold` | 3 | Tolerate transient issues, requires 30s of problems before restart |
| `successThreshold` | 1 (implicit) | Must be 1 for liveness probes (cannot be changed) |

---

## Readiness Probe

### Purpose: Control Traffic Routing

**Question:** "Is my application ready to receive traffic?"

**Action on Failure:** Remove pod from Service endpoints (no restart)

### Current Configuration

From `k8s/deployment.yaml`:

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 5000
  initialDelaySeconds: 2
  periodSeconds: 5
  # timeoutSeconds: 1 (default)
  # failureThreshold: 3 (default)
  # successThreshold: 1 (default)
```

### How It Works

**Timeline:**

```
Container Start
    │
    ├─ t=0s:   Container starts
    ├─ t=0-2s: Initial delay (no checks)
    │
    ├─ t=2s:   First readiness check → GET http://pod-ip:5000/
    │          ✅ Success (200 OK) → Pod marked READY
    │          Pod added to Service endpoints (receives traffic)
    │
    ├─ t=7s:   Second check → GET http://pod-ip:5000/
    │          ✅ Success → Pod still READY
    │
    ├─ t=12s:  Third check → GET http://pod-ip:5000/
    │          ✅ Success → Pod still READY
    │
    └─ Checks continue every 5 seconds...
```

### Failure Scenario

**App becomes temporarily overloaded:**

```
t=12s:  Readiness check → GET http://pod-ip:5000/
        ❌ FAILED (timeout or slow response)
        Failure count: 1/3
        Pod: STILL READY (need 3 failures)
        
t=17s:  Readiness check → GET http://pod-ip:5000/
        ❌ FAILED
        Failure count: 2/3
        Pod: STILL READY (need 1 more failure)
        
t=22s:  Readiness check → GET http://pod-ip:5000/
        ❌ FAILED (3rd consecutive failure)
        Failure count: 3/3
        
        🚫 ACTION: REMOVE FROM SERVICE
        Pod marked NOT READY
        Removed from load balancer endpoints
        No traffic routed to this pod
        
t=27s:  Readiness check → GET http://pod-ip:5000/
        ✅ SUCCESS (app recovered)
        Success count: 1/1
        
        ✅ ACTION: ADD BACK TO SERVICE
        Pod marked READY
        Added to load balancer endpoints
        Traffic resumes to this pod
```

**Time to remove from service:** 15 seconds from first failure (5s period × 3 failures)

**Time to add back:** 5 seconds (immediately after 1 success)

### Traffic Routing Impact

**When Pod is READY:**
```
                    ┌─────────────┐
                    │   Service   │
                    └──────┬──────┘
                           │
                ┳──────────┴──────────┳
                │                     │
         ┌──────▼──────┐       ┌─────▼──────┐
         │   Pod 1     │       │   Pod 2    │
         │   READY ✅  │       │   READY ✅ │
         └─────────────┘       └────────────┘
         Receives 50%          Receives 50%
         of traffic            of traffic
```

**When Pod 1 becomes NOT READY:**
```
                    ┌─────────────┐
                    │   Service   │
                    └──────┬──────┘
                           │
                ┳──────────┴──────────┳
                │                     │
         ┌──────▼──────┐       ┌─────▼──────┐
         │   Pod 1     │       │   Pod 2    │
         │ NOT READY ❌│       │   READY ✅ │
         └─────────────┘       └────────────┘
         Receives 0%           Receives 100%
         of traffic            of traffic
```

### What Triggers Readiness Failures

**Common scenarios:**

1. **Temporary Overload**
   ```
   Traffic spike → Slow responses → Readiness probe timeouts
   → Removed from service → Load decreases → Recovers → Added back
   ```

2. **Startup Dependencies**
   ```
   App starting → Database not connected yet → Returns 503
   → Not added to service → Connection ready → Returns 200 → Added to service
   ```

3. **Graceful Shutdown**
   ```
   SIGTERM received → App stops accepting new requests → Returns 503
   → Removed from service → Existing requests complete → Container stops
   ```

4. **External Dependency Failure**
   ```
   Redis/DB temporarily down → App can't serve requests
   → Removed from service → Dependency recovers → Added back
   ```

### Configuration Parameters Explained

| Parameter | Value | Why This Value? |
|-----------|-------|-----------------|
| `initialDelaySeconds` | 2 | App starts quickly, checks can begin almost immediately |
| `periodSeconds` | 5 | More frequent than liveness (detect issues faster for traffic routing) |
| `timeoutSeconds` | 1 (default) | Quick responses expected, 1s is sufficient |
| `failureThreshold` | 3 (default) | Tolerates brief slow responses, 15s total before removal |
| `successThreshold` | 1 (default) | Single success → immediate traffic restoration |

---

## Probes Working Together

Both probes work simultaneously to provide **graceful traffic management** (readiness) and **automatic crash recovery** (liveness).

### Complete Timeline Example

**Scenario: App experiences temporary overload, then crashes**

```
t=0s:   Container starts
        Readiness: Waiting 2s
        Liveness:  Waiting 10s

t=2s:   Readiness: ✅ Success → Pod READY (receives traffic)
t=7s:   Readiness: ✅ Success → Pod READY
t=10s:  Liveness:  ✅ Success → Container healthy
t=12s:  Readiness: ✅ Success → Pod READY
t=17s:  Readiness: ✅ Success → Pod READY
t=20s:  Liveness:  ✅ Success → Container healthy

--- App becomes temporarily overloaded ---

t=22s:  Readiness: ❌ Failed (1/3) → Pod STILL READY
t=27s:  Readiness: ❌ Failed (2/3) → Pod STILL READY
t=30s:  Liveness:  ✅ Success → Container healthy (no restart needed)
t=32s:  Readiness: ❌ Failed (3/3) → Pod NOT READY (no traffic)
t=37s:  Readiness: ✅ Success → Pod READY (traffic resumes)
t=40s:  Liveness:  ✅ Success → Container healthy

--- App completely deadlocks (e.g., infinite loop) ---

t=42s:  Readiness: ❌ Failed (1/3) → Pod STILL READY
t=47s:  Readiness: ❌ Failed (2/3) → Pod STILL READY
t=50s:  Liveness:  ❌ Failed (1/3) → Container still running
t=52s:  Readiness: ❌ Failed (3/3) → Pod NOT READY (no traffic)
t=57s:  Readiness: ❌ Failed → Pod NOT READY
t=60s:  Liveness:  ❌ Failed (2/3) → Container still running
t=62s:  Readiness: ❌ Failed → Pod NOT READY
t=67s:  Readiness: ❌ Failed → Pod NOT READY
t=70s:  Liveness:  ❌ Failed (3/3) → 🔄 RESTART CONTAINER

t=70s:  Container restarted, RESTARTS count: 1
t=72s:  Readiness: ✅ Success → Pod READY (traffic resumes)
t=77s:  Readiness: ✅ Success → Pod READY
t=80s:  Liveness:  ✅ Success → Container healthy (recovered!)
```

### Key Insights

**1. Readiness Fails First (Faster Detection)**
- Checks every 5s vs liveness every 10s
- Removes traffic before container restart

**2. Liveness Only Restarts When Necessary**
- Temporary issues handled by readiness (no restart)
- Only severe, persistent failures trigger restart

**3. Non-Destructive → Destructive Progression**
- Readiness: "Stop sending traffic" (gentle)
- Liveness: "Restart container" (aggressive)

**4. Self-Healing Without Downtime**
- Other pods continue serving traffic
- Failed pod recovers automatically
- Users experience no downtime (with 2+ replicas)

---

## Configuration Reference

### All Probe Parameters

```yaml
livenessProbe:
  # Check method (choose one)
  httpGet:
    path: /health          # HTTP endpoint to check
    port: 5000             # Port to connect to
    httpHeaders:           # Optional custom headers
    - name: Custom-Header
      value: Header-Value
  # OR
  tcpSocket:
    port: 5000             # Just check if port is open
  # OR
  exec:
    command:               # Run command in container
    - cat
    - /tmp/healthy
  
  # Timing configuration
  initialDelaySeconds: 10  # Wait before first check (default: 0)
  periodSeconds: 10        # How often to check (default: 10)
  timeoutSeconds: 5        # Max time to wait for response (default: 1)
  successThreshold: 1      # Consecutive successes to be healthy (must be 1 for liveness)
  failureThreshold: 3      # Consecutive failures before action (default: 3)
```

### Parameter Decision Guide

#### `initialDelaySeconds`

**Liveness:**
```
Low value:  Risk restarting healthy container during startup
High value: Delay detecting actual crashes
Sweet spot: App startup time + 5-10s buffer
```

**Readiness:**
```
Low value:  Detect readiness quickly, faster traffic routing
High value: Ensure app is fully initialized before traffic
Sweet spot: Minimum time for app to be ready
```

**This repo:**
- Liveness: 10s (Flask starts in ~2-3s, +7s safety)
- Readiness: 2s (app ready almost immediately)

#### `periodSeconds`

**Trade-off:**
```
Low value:  Fast detection, higher CPU/network overhead
High value: Slower detection, lower overhead
Sweet spot: Balance based on app criticality
```

**Best practices:**
- Readiness: 5-10s (fast traffic decisions)
- Liveness: 10-30s (less frequent, less overhead)
- Readiness < Liveness (detect traffic issues before restart)

**This repo:**
- Liveness: 10s (balanced)
- Readiness: 5s (faster traffic control)

#### `timeoutSeconds`

**Calculation:**
```
Expected response time + network latency + buffer
```

**Examples:**
- REST API (fast): 1-5s
- Database query: 5-10s
- ML inference: 10-30s

**This repo:**
- Liveness: 5s (very generous for simple app)
- Readiness: 1s (default, appropriate for fast endpoint)

#### `failureThreshold`

**Trade-off:**
```
Low value:  Fast failure detection, risk of false positives
High value: Tolerates transient issues, slower detection
Sweet spot: 2-5 failures for most apps
```

**Time to action:**
```
Time = periodSeconds × failureThreshold

failureThreshold: 1 → 10s (very aggressive)
failureThreshold: 3 → 30s (balanced)
failureThreshold: 5 → 50s (conservative)
```

**This repo:**
- Liveness: 3 (30s to restart)
- Readiness: 3 (15s to remove from service)

#### `successThreshold`

**For Readiness:**
```
1: Immediate traffic restoration (default)
2-3: Conservative, ensure consistent health
```

**Use higher values when:**
- App has flaky health checks
- Want to prevent traffic to unstable pods
- Need to verify sustained health

**For Liveness:**
- Must be 1 (cannot change)

**This repo:**
- Both probes: 1 (default, appropriate)

---

## Testing & Verification

### Quick Verification Commands

**Check probe configuration:**
```bash
# View probe settings in running pod
kubectl describe pod <pod-name> | grep -A 10 "Liveness:"
kubectl describe pod <pod-name> | grep -A 10 "Readiness:"

# Expected output:
# Liveness:   http-get http://:5000/health delay=10s timeout=5s period=10s #success=1 #failure=3
# Readiness:  http-get http://:5000/ delay=2s timeout=1s period=5s #success=1 #failure=3
```

**Check current pod status:**
```bash
# See if pods are ready
kubectl get pods -l app=hello-flask

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# hello-flask-5d856bb855-abc12   1/1     Running   0          5m
#                                ↑       ↑         ↑
#                             Ready   Status   Restart count
```

**Watch pod status in real-time:**
```bash
kubectl get pods -l app=hello-flask -w
# Press Ctrl+C to stop
```

### Manual Testing

#### Test 1: Liveness Probe (Self-Healing via Container Restart)

**Simulate app crash:**
```bash
# Get pod name
POD=$(kubectl get pods -l app=hello-flask -o jsonpath="{.items[0].metadata.name}")
echo "Testing pod: $POD"

# Watch for changes (in another terminal)
kubectl get pod $POD -w

# Kill the main process (PID 1) to crash the app
kubectl exec $POD -- bash -c "kill -9 1"

# Alternative: Kill Python specifically
kubectl exec $POD -- bash -c "pkill -9 python"
```

**What to observe:**
```
1. READY changes from 1/1 to 0/1 (almost immediately)
2. After ~30s: RESTARTS increments from 0 to 1
3. STATUS remains "Running" (container restart, not pod recreation)
4. After restart: READY returns to 1/1
5. Pod is healthy again!
```

**Check pod events:**
```bash
kubectl describe pod $POD | tail -20

# Look for events like:
# Unhealthy    Liveness probe failed: Get "http://...": dial tcp ...
# Killing      Container hello-flask failed liveness probe, will be restarted
# Pulled       Container image "hello-flask:latest" already present on machine
# Created      Created container hello-flask
# Started      Started container hello-flask
```

#### Test 2: Readiness Probe (Traffic Control via Pod Deletion)

**Delete a pod to watch ReplicaSet recreate it:**
```bash
# Watch pods (in another terminal)
kubectl get pods -l app=hello-flask -w

# Delete one pod
kubectl delete pod <pod-name>
```

**What to observe:**
```
1. Deleted pod enters "Terminating" state
2. Readiness probe marks it NOT READY → removed from service
3. Kubernetes immediately creates new pod (maintain replica count)
4. New pod: ContainerCreating → Running
5. New pod: Readiness checks pass → marked READY → receives traffic
6. Total time: ~5-10 seconds
```

#### Test 3: Service Endpoints (Verify Readiness Impact)

**Check Service endpoints:**
```bash
# See which pods are receiving traffic
kubectl get endpoints hello-flask

# Expected output (2 ready pods):
# NAME          ENDPOINTS                         AGE
# hello-flask   10.244.0.5:5000,10.244.0.6:5000   10m
#               ↑                ↑
#            Pod 1 IP         Pod 2 IP

# If a pod becomes NOT READY, it disappears from endpoints
```

### Automated Tests

**Liveness Probe Configuration Tests (Fast):**
```bash
# Test liveness probe configuration
make liveness-test
# OR: pytest test_k8s/test_liveness_probe.py -v

# What it checks:
# - Liveness probe configured correctly (/health endpoint)
# - Proper timing parameters
# - Container restart tracking
```

**Readiness Probe Configuration Tests (Fast):**
```bash
# Test readiness probe configuration
make readiness-test
# OR: pytest test_k8s/test_readiness_probe.py -v

# What it checks:
# - Readiness probe configured correctly (/ready endpoint)
# - Ready replicas match desired count
# - All running pods pass readiness checks
```

**Behavioral Tests (Slow, Manual):**
```bash
# Test actual self-healing behavior
pytest test_k8s/test_crash_recovery_manual.py -v -s

# What it tests:
# - Pod deletion and ReplicaSet recreation
# - Container crash and liveness restart
# - Restart count increments
# - Pod recovers to healthy state

# Note: Marked as @pytest.mark.manual (not run in CI/CD)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Pod Stuck in CrashLoopBackOff

**Symptoms:**
```bash
kubectl get pods
# NAME                     READY   STATUS             RESTARTS   AGE
# hello-flask-xxx          0/1     CrashLoopBackOff   5          10m
```

**Cause:** Liveness probe fails immediately after container starts

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod <pod-name> | tail -30

# Common messages:
# "Liveness probe failed: Get http://...: dial tcp: connect: connection refused"
# "Back-off restarting failed container"
```

**Solutions:**

1. **Increase `initialDelaySeconds`** if app needs more startup time:
   ```yaml
   livenessProbe:
     initialDelaySeconds: 30  # Give app more time
   ```

2. **Check app actually starts** on port 5000:
   ```bash
   # Check logs
   kubectl logs <pod-name>
   
   # Should see: "Running on http://0.0.0.0:5000"
   ```

3. **Verify endpoint returns 200**:
   ```bash
   kubectl port-forward <pod-name> 8080:5000
   curl http://localhost:8080/
   # Should return: {"message": "Hello from Flask..."}
   ```

#### Issue 2: Pod Always Shows 0/1 Ready

**Symptoms:**
```bash
kubectl get pods
# NAME                     READY   STATUS    RESTARTS   AGE
# hello-flask-xxx          0/1     Running   0          5m
#                          ↑ Never becomes 1/1
```

**Cause:** Readiness probe failing continuously

**Diagnosis:**
```bash
# Check readiness probe failures
kubectl describe pod <pod-name> | grep -A 5 "Readiness"

# Look for:
# "Readiness probe failed: Get http://...: dial tcp: connection refused"
# "Readiness probe failed: HTTP probe failed with statuscode: 503"
```

**Solutions:**

1. **Check app is listening on correct port**:
   ```bash
   kubectl exec <pod-name> -- netstat -tlnp | grep 5000
   # Should show: tcp 0.0.0.0:5000 ... LISTEN
   ```

2. **Test endpoint directly**:
   ```bash
   kubectl exec <pod-name> -- curl http://localhost:5000/
   # Should return JSON response
   ```

3. **Check probe configuration**:
   ```yaml
   readinessProbe:
     httpGet:
       path: /        # Correct path?
       port: 5000     # Correct port?
   ```

#### Issue 3: Pods Restarting Too Frequently

**Symptoms:**
```bash
kubectl get pods
# NAME                     READY   STATUS    RESTARTS   AGE
# hello-flask-xxx          1/1     Running   47         10m
#                                            ↑ High restart count
```

**Cause:** Liveness probe too aggressive or app legitimately failing

**Diagnosis:**
```bash
# Check why it's restarting
kubectl describe pod <pod-name> | grep -A 10 "Events:"

# Look for:
# "Liveness probe failed"
# "Killing container"
# Error patterns
```

**Solutions:**

1. **Increase timeout** if app is slow:
   ```yaml
   livenessProbe:
     timeoutSeconds: 10  # More time for response
   ```

2. **Increase failure threshold** for transient issues:
   ```yaml
   livenessProbe:
     failureThreshold: 5  # Tolerate more failures
   ```

3. **Check app logs** for actual errors:
   ```bash
   kubectl logs <pod-name> --previous  # Logs from before restart
   ```

#### Issue 4: Traffic Not Evenly Distributed

**Symptoms:** One pod receives all traffic, others receive none

**Diagnosis:**
```bash
# Check which pods are endpoints
kubectl get endpoints hello-flask

# Check pod readiness
kubectl get pods -l app=hello-flask -o wide

# Check pod logs for request counts
kubectl logs <pod-1> | grep -c "GET / HTTP"
kubectl logs <pod-2> | grep -c "GET / HTTP"
```

**Cause:** Some pods not passing readiness probe

**Solutions:**

1. **Check readiness probe status**:
   ```bash
   kubectl describe pod <pod-name> | grep -A 5 "Readiness"
   ```

2. **Verify all pods are READY**:
   ```bash
   kubectl get pods -l app=hello-flask
   # All should show 1/1 in READY column
   ```

### Debug Commands Reference

```bash
# View all probe configurations
kubectl get pod <pod-name> -o yaml | grep -A 15 "livenessProbe"
kubectl get pod <pod-name> -o yaml | grep -A 15 "readinessProbe"

# Watch pod status changes
kubectl get pods -l app=hello-flask -w

# Stream pod events
kubectl get events -w --field-selector involvedObject.name=<pod-name>

# Check pod conditions
kubectl get pod <pod-name> -o jsonpath='{.status.conditions[*].type}{"\n"}{.status.conditions[*].status}'

# View container status
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].state}'

# Check recent restarts
kubectl get pods -l app=hello-flask -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'
```

---

## Best Practices

### 1. Always Use Both Probes

✅ **Do:**
```yaml
livenessProbe:   # Restart crashed containers
  ...
readinessProbe:  # Control traffic routing
  ...
```

❌ **Don't:**
```yaml
livenessProbe:   # Only liveness - no traffic control
  ...
# Missing readiness probe!
```

**Why:** Liveness alone can't prevent traffic to slow/starting pods.

### 2. Readiness Should Be Less Than Liveness Delay

✅ **Do:**
```yaml
readinessProbe:
  initialDelaySeconds: 2   # Fast traffic control
  periodSeconds: 5
livenessProbe:
  initialDelaySeconds: 10  # Slower, more conservative
  periodSeconds: 10
```

❌ **Don't:**
```yaml
readinessProbe:
  initialDelaySeconds: 15  # Slower than liveness!
livenessProbe:
  initialDelaySeconds: 5
```

**Why:** Want to detect traffic issues before considering restart.

### 3. Use Dedicated Health Endpoints

✅ **Do:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready  # Checks dependencies
readinessProbe:
  httpGet:
    path: /health/live   # Checks app is alive
```

**Example implementation:**
```python
@app.route('/health/live')
def liveness():
    # Simple check - is app running?
    return {"status": "alive"}, 200

@app.route('/health/ready')
def readiness():
    # Complex check - can we serve traffic?
    db_ok = check_database()
    cache_ok = check_redis()
    if db_ok and cache_ok:
        return {"status": "ready"}, 200
    else:
        return {"status": "not ready"}, 503
```

**Current repo:** Uses `/health` for liveness (dedicated health check) and `/` for readiness (main endpoint).

### 4. Tune Based on Application Characteristics

**Fast startup apps:**
```yaml
livenessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Slow startup apps (databases, ML models):**
```yaml
livenessProbe:
  initialDelaySeconds: 60
  periodSeconds: 30
```

**Critical apps (need fast failure detection):**
```yaml
readinessProbe:
  periodSeconds: 2
  failureThreshold: 2  # Fast removal (4s)
```

**Apps with transient issues:**
```yaml
livenessProbe:
  failureThreshold: 5  # Tolerate more failures (50s)
```

### 5. Monitor Restart Counts

**Set up alerts:**
```bash
# Check for pods with high restart counts
kubectl get pods -l app=hello-flask -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'

# Alert if restarts > 5 in last hour
```

**Investigate patterns:**
- Regular restarts at specific times → Resource issue, cron job impact
- Gradually increasing restarts → Memory leak
- Immediate restart loop → Probe misconfiguration

### 6. Different Probes for Different Environments

**Development:**
```yaml
livenessProbe:
  initialDelaySeconds: 60  # More time for debugging
  failureThreshold: 10     # Very tolerant
```

**Production:**
```yaml
livenessProbe:
  initialDelaySeconds: 10  # Fast detection
  failureThreshold: 3      # Balanced
```

### 7. Test Probe Behavior

**Include in CI/CD:**
```yaml
# .github/workflows/ci-cd.yml
- name: Test Probe Configuration
  run: |
    make liveness-test    # Test liveness probe config
    make readiness-test   # Test readiness probe config
```

**Manual testing:**
```bash
# Regularly test self-healing
make liveness-test-manual
```

---

## Summary

### Quick Reference

| Aspect | Liveness Probe | Readiness Probe |
|--------|---------------|-----------------|
| **Purpose** | Detect crashed/deadlocked containers | Control traffic routing |
| **Action** | Restart container | Remove/add to Service |
| **Initial Delay** | 10s (app startup time + buffer) | 2s (fast traffic detection) |
| **Period** | 10s (balanced) | 5s (faster than liveness) |
| **Timeout** | 5s (generous) | 1s (default, fast) |
| **Failures** | 3 (30s to restart) | 3 (15s to remove) |
| **Severity** | High (destructive) | Low (non-destructive) |

### Key Takeaways

1. ✅ **Use both probes** - Complementary, not redundant
2. ✅ **Readiness < Liveness timing** - Detect traffic issues first
3. ✅ **Tune for your app** - No one-size-fits-all
4. ✅ **Monitor restarts** - High count indicates problems
5. ✅ **Test regularly** - Ensure self-healing works
6. ✅ **Different endpoints** - Liveness vs readiness checks can differ
7. ✅ **Progressive timeouts** - Fast detection → slower restart

### This Repository's Configuration

**Liveness:** `/health` endpoint, 10s delay, 10s period, 5s timeout, 3 failures → Restart after 30s  
**Readiness:** `/` endpoint, 2s delay, 5s period, 1s timeout, 3 failures → Remove after 15s

**Result:** Self-healing application with intelligent traffic routing! 🎉

---

## Further Reading

- **Kubernetes Documentation:** [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- **Repository Documentation:**
  - `README.md` - Quick testing examples
  - `test_k8s/README.md` - Test suite architecture
  - `test_k8s/test_liveness_probe.py` - Liveness probe configuration tests
  - `test_k8s/test_readiness_probe.py` - Readiness probe configuration tests
  - `test_k8s/test_crash_recovery_manual.py` - Behavioral tests
  - `docs/testing/TESTING_WORKFLOWS.md` - Complete testing workflows
- **Related Guides:**
  - `docs/CI_CD_GUIDE.md` - How probes work in CI/CD
  - `docs/DEVELOPMENT_WORKFLOW.md` - Pre-push validation

---

**Last Updated:** November 21, 2025  
**Kubernetes Version:** 1.28.0  
**Tested With:** Minikube, Flask 3.x
