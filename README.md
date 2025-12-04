# Flask Hello World - Minikube Deployment

Demonstrate deploying a Flask application to a local Kubernetes cluster using Minikube, with comprehensive testing and CI/CD automation.

## Key Takeaways

This project demonstrates production-grade DevOps practices for containerized applications:

| Area | Why It Matters |
|------|----------------|
| **Separation of concerns** | App code, infrastructure manifests, and tests live independently, making the codebase modular and maintainable. |
| **Automated testing** | Tests run at multiple levels (unit tests for Flask, integration tests for Kubernetes) ensuring reliability. |
| **Reproducibility** | Scripts and Makefile create consistent environments across local development, CI/CD, and cloud deployments. |
| **CI/CD integration** | GitHub Actions pipeline automates build, deploy, and validation - see [CI/CD Guide](docs/CI_CD_GUIDE.md) for details. |
| **Cloud-readiness** | The same Kubernetes manifests work for both local Minikube and cloud platforms (EKS, GKE, AKS). |

---

## Quick Start

Note: Use a Python virtual environment for development and testing.
```bash
python3 -m venv .venv
source .venv/bin/activate
```

# Step-by-step commands (run in a terminal)

## Pre-requisites

Make sure you have installed:

| Tool | Command to check |
|------|-----------------|
| Python 3.11+ | `python --version` |
| pip | `pip --version` |
| Docker | `docker --version` |
| Minikube | `minikube version` |
| kubectl | `kubectl version --client` |

Also, ensure Python packages for testing are installed:

```bash
# Install Flask app dependencies (production)
pip install -r app/requirements.txt

# Install all development and testing dependencies
# (includes pytest, pytest-cov, requests, yamllint, flake8)
pip install -r app/requirements-dev.txt
```

**Required packages:**
- `pytest` - Test framework for running unit and integration tests
- `requests` - HTTP library for testing service endpoints
- Flask dependencies from `app/requirements.txt`

## Start Minikube
```
minikube start
minikube status
```

* This starts a single-node Kubernetes cluster locally.
* `minikube status` confirms that the cluster is running.

## Build the Docker image for the app
```
eval $(minikube docker-env)
docker build -t hello-flask:latest ./app
```

Ensures the image is available to the Minikube cluster without pushing to Docker Hub.
```
docker images | grep hello-flask
```

## Deploy ConfigMap and Secret (optional for advanced testing)
```
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
```

## Deploy the app to Kubernetes

### Option A: Direct Access (without Ingress)
If you want to access the app via NodePort (simpler, for quick testing):

1. Change Service type back to NodePort in `k8s/service.yaml`:
```yaml
spec:
  type: NodePort  # Change from ClusterIP to NodePort
```

2. Deploy:
```
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

3. Access via: `minikube service hello-flask --url`

### Option B: Using Ingress (production-like setup)
For a more production-like setup with Ingress:

1. Setup Ingress controller (only needed once):
```
bash scripts/setup_ingress.sh
```
This enables nginx ingress on Minikube and configures `/etc/hosts`.

2. Deploy application with Ingress:
```
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

3. Wait for Ingress to be ready:
```
kubectl get ingress hello-flask-ingress -w
```
Wait until you see an ADDRESS assigned (Ctrl+C to exit).

4. Access via: `http://hello-flask.local`

Check that Pods are running:
```
kubectl get pods
kubectl get deployments
kubectl get svc
kubectl get ingress
```

Wait until Pods show `STATUS=Running`.
```
kubectl get pods -o wide -l app=hello-flask
kubectl logs deploy/hello-flask
```
If ConfigMap and Secret was deployed, confirm environment variables inside a running Pod:
```
POD=$(kubectl get pods -l app=hello-flask -o jsonpath="{.items[0].metadata.name}")
echo $POD
kubectl describe pod $POD | grep Status
kubectl exec -it $POD -- env | grep -E 'APP_ENV|LOG_LEVEL|API_KEY|DB_PASSWORD|CUSTOM_MESSAGE'
```

Expected output:
```
APP_ENV=local
LOG_LEVEL=debug
FEATURE_FLAG_GREETING=true
API_KEY=somesecretkey
DB_PASSWORD=password123
CUSTOM_MESSAGE=Deployed via ConfigMap + Secret
```

Note: Kubernetes Secrets must use base64 encoding.
To generate encoded values:
```
echo -n "somesecretkey" | base64
```

## Test Liveness Probe (Self-Healing)

The deployment includes **liveness** and **readiness** probes that work together to provide self-healing and intelligent traffic routing.

### Understanding the Probes

| Probe | Purpose | Failure Action | Config |
|-------|---------|----------------|--------|
| **Liveness** | "Is the app alive?" | **Restart container** 🔄 | 10s delay, check every 10s |
| **Readiness** | "Ready for traffic?" | Remove from Service (no restart) | 2s delay, check every 5s |

**How they work together:**
- **Readiness probe** removes unhealthy pods from traffic (non-destructive, fast detection)
- **Liveness probe** restarts crashed/deadlocked containers (destructive but healing)
- **Result:** Self-healing with zero downtime (when using 2+ replicas)

You can manually test this self-healing behavior:

### Method 1: Delete a Pod (Recommended)
Watch Kubernetes automatically recreate the deleted pod to maintain the desired replica count:

```bash
# Watch pods in real-time (in one terminal)
kubectl get pods -w

# In another terminal, delete one pod
kubectl delete pod <pod-name>
# Example: kubectl delete pod hello-flask-5d856bb855-b7jwp
```

**What you'll see:**
- The deleted pod enters `Terminating` state
- **Readiness probe** marks it NOT READY → removed from Service endpoints
- Kubernetes immediately creates a new pod to maintain 2 replicas
- The new pod goes through: `ContainerCreating` → `Running`
- **Readiness probe** passes → new pod marked READY → receives traffic
- Total time: typically 5-10 seconds

**Why this works:** The ReplicaSet controller watches the desired state (2 replicas) and automatically creates new pods when needed.

### Method 2: Simulate App Crash
Simulate an application crash by killing the Flask process inside the container:

```bash
# Get a pod name
POD=$(kubectl get pods -l app=hello-flask -o jsonpath="{.items[0].metadata.name}")
echo "Testing pod: $POD"

# Watch the pod status in real-time
kubectl get pod $POD -w &

# Kill the main process (PID 1) inside the container
# Note: Use 'bash -c' because the kill command is a bash builtin
# Use -9 (SIGKILL) to force kill the process
kubectl exec $POD -- bash -c "kill -9 1"
```

**What you'll see:**
- The container immediately terminates
- **Readiness probe** fails → Pod marked NOT READY → removed from Service (no traffic)
- **Liveness probe** detects the app is not responding on port 5000
- After 3 consecutive failed checks (~30 seconds total), Kubernetes restarts the container
- Pod shows `RESTARTS` count incremented (0 → 1)
- **Readiness probe** passes → Pod marked READY → receives traffic again
- The pod stays in `Running` state (container restart, not pod recreation)

**Timeline:**
```
t=0s:   Kill process
t=0s:   Readiness fails → Pod NOT READY (no traffic to this pod)
t=10s:  Liveness check 1 → Failed (1/3)
t=20s:  Liveness check 2 → Failed (2/3)
t=30s:  Liveness check 3 → Failed (3/3) → Container restarted
t=32s:  Readiness passes → Pod READY → Traffic resumes
```

**Why does it take ~30 seconds?**
With the current liveness probe settings:
- `initialDelaySeconds: 10` - Waits 10s after container starts before first check
- `periodSeconds: 10` - Checks every 10 seconds
- `failureThreshold: 3` - Needs 3 consecutive failures before restart

**Time to restart after crash:**
- First check fails immediately (app is crashed)
- Wait 10s → Second check fails (1/3 failures counted from when checking starts)
- Wait 10s → Third check fails (2/3)
- Wait 10s → Fourth check fails (3/3) → **Restart triggered**
- **Total:** ~30 seconds from first check failure (10s × 3 failures)

**Note:** The readiness probe (checks every 5s) detects the failure faster and removes the pod from traffic immediately, ensuring no requests are sent to the crashed pod.

**Alternative - More visible crash simulation:**
To see a more gradual failure and recovery, you can crash Python instead:
```bash
kubectl exec $POD -- bash -c "pkill -9 python"
# or
kubectl exec $POD -- bash -c "python -c 'import os; os._exit(1)'"
```

### Verify Probe Configuration

Check both liveness and readiness probe settings in your running pod:

```bash
kubectl describe pod <pod-name> | grep -A 10 "Liveness:\|Readiness:"
```

**Expected output:**
```
Liveness:   http-get http://:5000/health delay=10s timeout=5s period=10s #success=1 #failure=3
Readiness:  http-get http://:5000/ delay=2s timeout=1s period=5s #success=1 #failure=3
```

**What this means:**

| Probe | Initial Delay | Check Frequency | Timeout | Failure Threshold |
|-------|---------------|-----------------|---------|-------------------|
| **Liveness** | 10 seconds | Every 10s | 5s | 3 failures → restart |
| **Readiness** | 2 seconds | Every 5s | 1s | 3 failures → remove from service |

**Key differences:**
- Readiness starts checking sooner (2s vs 10s) - fast traffic control
- Readiness checks more frequently (5s vs 10s) - quicker issue detection
- Liveness is more tolerant (5s timeout vs 1s) - avoid unnecessary restarts

### Check Pod Events for Probe Failures

If you simulated a crash, you can see both probe failures in the pod events:

```bash
kubectl describe pod <pod-name> | grep -A 20 "Events:"
```

Look for events like:
- `Unhealthy` (Readiness): Readiness probe failed - pod removed from Service
- `Unhealthy` (Liveness): Liveness probe failed - container will be restarted
- `Killing`: Container being killed due to liveness failure
- `Started`: Container restarted successfully

**Example event sequence:**
```
Readiness probe failed: Get "http://10.244.0.5:5000/": dial tcp: connection refused
Liveness probe failed: Get "http://10.244.0.5:5000/": dial tcp: connection refused
Killing container with id docker://hello-flask
Pulled container image "hello-flask:latest"
Created container hello-flask
Started container hello-flask
```

### Learn More About Probes

For a comprehensive understanding of how liveness and readiness probes work, including:
- Detailed configuration parameters
- Visual timelines of probe behavior
- Troubleshooting guide
- Best practices

See: **[docs/PROBES_GUIDE.md](docs/PROBES_GUIDE.md)** 📚

## Code Quality & Linting

This project uses **shift-left testing** - catching errors early before they reach later pipeline stages.

### Python Linting (flake8)
```bash
make lint
```

Checks Python code for:
- ✅ Syntax errors and undefined variables
- ✅ Unused imports and variables
- ✅ Code complexity and PEP 8 compliance
- ✅ Common code quality issues

Configuration: `.flake8`

### YAML Validation (yamllint)
YAML files (Kubernetes manifests, workflows) are automatically validated with yamllint.

Configuration: `.yamllint`

**Why This Matters:** Linting runs as the 4th step in the CI/CD pipeline, catching errors before expensive build and test operations. This saves time and provides faster feedback.

See: **[docs/development/CODE_QUALITY.md](docs/development/CODE_QUALITY.md)** for details.

## Run Tests

### Application Unit Tests
```bash
pytest app/tests/ -v
```
Tests the Python/Flask application logic independently of Kubernetes.

### Kubernetes Integration Tests

See the **[Testing](#testing)** section below for detailed test commands and organization.

## Access the App Locally

### With Ingress (Option B):
If you deployed with Ingress:
```bash
curl http://hello-flask.local
# or open http://hello-flask.local in browser
```

### Without Ingress (Option A - NodePort):

#### Method 1: Minikube service URL:
```bash
minikube service hello-flask --url
# Opens the service in browser or shows URL like http://192.168.49.2:32000
```

#### Method 2: Port-forward:
```bash
kubectl port-forward svc/hello-flask 5000:5000
# Then open http://localhost:5000
```

---

## Observability Features (Educational)

This application demonstrates three tiers of observability for Kubernetes applications. These features are designed for learning - production systems would typically use comprehensive platforms like Prometheus/Grafana, ELK Stack, or OpenTelemetry (see [docs/PRODUCTION_CONSIDERATIONS.md](docs/PRODUCTION_CONSIDERATIONS.md)).

### Tier 1: Kubernetes Metrics (Resource Monitoring)

**Enable metrics-server addon** (only needed once):
```bash
minikube addons enable metrics-server
```

**View node resources:**
```bash
kubectl top nodes
```
Shows CPU and memory usage for Minikube nodes.

**View pod resources:**
```bash
kubectl top pods -l app=hello-flask
```
Shows CPU and memory consumption for your application pods.

**Notes:**
- Metrics take ~60 seconds to populate after enabling
- This is Kubernetes-native resource monitoring
- Production uses Prometheus or cloud provider metrics (CloudWatch, Azure Monitor, etc.)

### Tier 2: Application Metrics (/metrics Endpoint)

The application exposes a `/metrics` endpoint returning JSON metrics:

**Query metrics via kubectl port-forward:**
```bash
# In one terminal, forward port 5000
kubectl port-forward svc/hello-flask 5000:5000

# In another terminal, query metrics
curl http://localhost:5000/metrics
```

**Query metrics via Ingress** (if using Option B deployment):
```bash
curl http://hello-flask.local/metrics
```

**Example response:**
```json
{
  "app": "hello-flask",
  "version": "1.0.0",
  "uptime_seconds": 127.45,
  "request_count": 23,
  "timestamp": "2024-01-15T14:30:45.123456+00:00",
  "status": "running"
}
```

**Metrics explained:**
- `uptime_seconds` - Time since pod started (resets on pod restart)
- `request_count` - Number of requests to `/` endpoint (in-memory counter)
- `timestamp` - Current UTC time in ISO 8601 format
- `status` - Application health indicator

**Educational notes:**
- ⚠️ **In-memory counters** - Metrics reset when pod restarts
- ⚠️ **Single pod** - Counts only requests to this specific pod
- 📚 **Production alternative** - Use Prometheus client library with `/metrics` in OpenMetrics format
- 📚 **Aggregation** - Production uses time-series databases for historical data

### Tier 3: Structured Logging

The application uses structured JSON logging for all endpoints:

**View logs:**
```bash
# Get logs from all hello-flask pods
kubectl logs -l app=hello-flask

# Follow logs in real-time
kubectl logs -l app=hello-flask -f

# Get logs from specific pod
POD=$(kubectl get pods -l app=hello-flask -o jsonpath="{.items[0].metadata.name}")
kubectl logs $POD
```

**Example log output:**
```json
{"timestamp": "2024-01-15T14:30:45.123456+00:00", "event": "request", "endpoint": "/", "method": "GET", "remote_addr": "10.244.0.1", "request_count": 23}
{"timestamp": "2024-01-15T14:30:50.789012+00:00", "event": "health_check", "endpoint": "/health", "status": "healthy"}
{"timestamp": "2024-01-15T14:30:55.345678+00:00", "event": "readiness_check", "endpoint": "/ready", "status": "ready"}
{"timestamp": "2024-01-15T14:31:00.901234+00:00", "event": "metrics_request", "endpoint": "/metrics"}
```

**Parse logs with jq** (JSON processor):
```bash
# Filter only request events
kubectl logs -l app=hello-flask | grep -o '{.*}' | jq 'select(.event == "request")'

# Count events by type
kubectl logs -l app=hello-flask | grep -o '{.*}' | jq -r '.event' | sort | uniq -c

# Extract timestamps for performance analysis
kubectl logs -l app=hello-flask | grep -o '{.*}' | jq -r '.timestamp'
```

**Structured logging benefits:**
- ✅ **Machine-readable** - Easy to parse and analyze programmatically
- ✅ **Filterable** - Query by event type, endpoint, etc.
- ✅ **Consistent** - Same structure across all log entries
- ✅ **Integration** - Works with log aggregators (ELK, Loki, CloudWatch)

**Production logging:**
- Use log aggregation platforms (ELK Stack, Grafana Loki, Splunk)
- Add correlation IDs for distributed tracing
- Include severity levels (DEBUG, INFO, WARN, ERROR)
- Integrate with alerting systems

### Putting It All Together: Complete Observability Example

**1. Deploy application:**
```bash
make deploy
```

**2. Enable metrics:**
```bash
minikube addons enable metrics-server
sleep 60  # Wait for metrics to populate
```

**3. Monitor resources:**
```bash
kubectl top nodes
kubectl top pods -l app=hello-flask
```

**4. Generate traffic:**
```bash
# If using NodePort (Option A)
URL=$(minikube service hello-flask --url)
for i in {1..10}; do curl $URL; done

# If using Ingress (Option B)
for i in {1..10}; do curl http://hello-flask.local; done
```

**5. Check application metrics:**
```bash
kubectl port-forward svc/hello-flask 5000:5000 &
curl http://localhost:5000/metrics | jq
```

**6. View structured logs:**
```bash
kubectl logs -l app=hello-flask | grep -o '{.*}' | jq
```

**Expected workflow:**
- 📊 **Tier 1** shows pod CPU/memory usage (infrastructure level)
- 📈 **Tier 2** shows application uptime and request counts (application level)
- 📝 **Tier 3** shows detailed request history with timestamps (request level)

**Visual Alternative - Minikube Dashboard:**

All of these metrics can also be viewed in the Minikube dashboard (see [Visual Exploration](#visual-exploration-optional) section):

```bash
minikube dashboard
```

The dashboard provides:
- 📊 **Tier 1 (Resource Metrics)**: Workloads → Pods → Select pod → View CPU/Memory graphs (requires metrics-server)
- 📝 **Tier 3 (Logs)**: Workloads → Pods → Select pod → Logs tab → View structured JSON logs
- 🔍 **Real-time monitoring**: Auto-refreshing metrics and log streaming

**Note:** The dashboard is great for visual learning and exploration. For automation, scripting, and production workflows, use the `kubectl` commands shown above.

### Learning Path: From Simple to Production

This three-tier approach teaches observability fundamentals:

1. **Start here** (this project):
   - ✅ Learn metrics-server (kubectl top)
   - ✅ Understand application metrics concepts
   - ✅ Practice structured logging

2. **Next steps** (intermediate):
   - Add Prometheus for metrics collection
   - Set up Grafana for visualization
   - Use Loki for log aggregation

3. **Production** (advanced):
   - Full observability platforms (Datadog, New Relic, Dynatrace)
   - Distributed tracing (Jaeger, Zipkin)
   - Service mesh observability (Istio, Linkerd)
   - Custom dashboards and SLO monitoring

📚 See [docs/PRODUCTION_CONSIDERATIONS.md](docs/PRODUCTION_CONSIDERATIONS.md#3-observability-metrics-logs-traces) for comprehensive production patterns.

---

## Visual Exploration (Optional)

### Minikube Dashboard

For visual learners, Minikube includes a built-in Kubernetes dashboard that provides a web UI to explore cluster resources:

```bash
minikube dashboard
```

This opens a browser showing:
- 📊 **Workloads** - Deployments, Pods, ReplicaSets
- 🔧 **Services** - Service endpoints and networking
- ⚙️ **Config** - ConfigMaps and Secrets
- 📝 **Logs** - Pod logs with filtering (including the structured JSON logs from [Observability Features](#observability-features-educational))
- 📈 **Metrics** - CPU/Memory usage (if metrics-server enabled - see [Tier 1 Observability](#tier-1-kubernetes-metrics-resource-monitoring))

**When to use:**
- ✅ Learning Kubernetes - Visualize how resources connect
- ✅ Quick troubleshooting - See pod status, logs, events in one place
- ✅ Understanding deployments - Watch rolling updates in real-time

**Best practices:**
- 💡 Use dashboard for **exploration and learning**
- 💡 Use `kubectl` for **automation and production**
- 💡 This project's tests use `kubectl` (the production approach)

**Alternative CLI tools** (more common in production):
- **[k9s](https://k9scli.io/)** - Terminal UI for Kubernetes (highly recommended)
- **[Lens](https://k8slens.dev/)** - Desktop IDE for Kubernetes
- **[kubectl with plugins](https://krew.sigs.k8s.io/)** - Extend kubectl functionality

**Note:** The dashboard is NOT part of this project's automation or testing workflows. All scripts and tests use `kubectl` commands to teach industry-standard practices.

---

## Clean Up Local Minikube Resources
```bash
kubectl delete -f k8s/ingress.yaml     # if using Ingress
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secret.yaml
minikube stop
```

## Troubleshooting

### Local Testing Issues

**Problem: Getting 404 when accessing Minikube IP directly**

If you try to access the app via `http://$(minikube ip)` and get a 404:

```bash
curl http://192.168.49.2
# Returns: 404 Not Found
```

**Cause:** Nginx Ingress uses the `Host` HTTP header for routing. When you access via IP, it doesn't match the configured hostname.

**Solutions:**

1. **Use the configured hostname** (recommended for local dev):
   ```bash
   curl http://hello-flask.local
   # Make sure /etc/hosts is configured (run scripts/setup_ingress.sh)
   ```

2. **Send the correct Host header**:
   ```bash
   curl -H "Host: hello-flask.local" http://$(minikube ip)
   # This works! Nginx sees the correct host header
   ```

3. **Use port-forward** (bypasses Ingress):
   ```bash
   kubectl port-forward svc/hello-flask 5000:5000
   curl http://localhost:5000
   ```

**Note:** The tests automatically handle this by sending the correct `Host` header when needed!

### CI/CD Pipeline Issues

If `test_service_reachable` fails in GitHub Actions:

1. **Check the workflow logs** for:
   - Ingress controller status
   - Ingress address assignment
   - Minikube IP
   - Service and pod status

2. **Common issue**: Ingress hostname not resolving in CI
   - **Solution**: The test automatically uses Minikube IP in CI/CD environments
   - No `/etc/hosts` configuration needed in GitHub Actions

3. **Debug locally**: Run the same sequence as CI/CD:
   ```bash
   minikube start
   minikube addons enable ingress
   kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=180s
   bash scripts/deploy_local.sh
   pytest test_k8s/ -v
   ```

4. **Manual verification** in CI/CD or locally:
   ```bash
   # Check Minikube IP
   minikube ip
   
   # Test with correct Host header (required for Ingress)
   curl -H "Host: hello-flask.local" http://$(minikube ip)
   
   # Or use hostname if /etc/hosts is configured
   curl http://hello-flask.local
   
   # Check ingress status
   kubectl get ingress hello-flask-ingress
   kubectl describe ingress hello-flask-ingress
   ```

For more detailed debugging steps, see [`docs/INGRESS_CI_CD_TROUBLESHOOTING.md`](docs/INGRESS_CI_CD_TROUBLESHOOTING.md).

# Automation Scripts

Modular Bash scripts for common workflows. Each script has a targeted function, making it easy to run only what you need.

**Important:** Start Minikube before running scripts: `minikube start`

## Quick Reference

```bash
# Build & Deploy
bash scripts/build_image.sh         # Build Docker image
bash scripts/deploy_local.sh        # Deploy with Ingress
bash scripts/delete_local.sh        # Cleanup resources

# Testing
bash scripts/unit_tests.sh          # App unit tests
bash scripts/k8s_tests.sh           # K8s integration tests (automated)
bash scripts/smoke_test.sh          # Quick validation (automated tests)
bash scripts/liveness_test.sh       # Liveness probe tests (see modes below)

# Utilities
bash scripts/port_forward.sh        # Forward to localhost:8080
bash scripts/minikube_service_url.sh # Get service access URL
bash scripts/setup_ingress.sh       # Setup Ingress controller
```

### Liveness Test Modes
```bash
bash scripts/liveness_test.sh           # Automated config tests (default)
bash scripts/liveness_test.sh --manual  # Manual behavioral tests (slow)
bash scripts/liveness_test.sh --config  # Config check only
```

## Makefile Shortcuts

```bash
# Build & Deploy
make build           # Build Docker image
make deploy          # Deploy to cluster
make delete          # Cleanup

# Testing
make unit-tests      # Run unit tests
make k8s-tests       # Run K8s tests
make smoke-test      # Quick validation
make test-all        # Run all automated tests (unit + k8s)
make test-full       # Run ALL tests including manual, educational, nodeport
make health-tests    # Run health endpoint tests (temporarily switches to NodePort)

# Validation (before push)
make validate-repo      # Check repository structure
make validate-workflow  # Check GitHub Actions config
make validate-all       # Run all validations

# Composite targets
make full-deploy     # Build → deploy → smoke test
make release-prep    # Complete release workflow: validate structure/workflow → verify test requirements → test-full → build → deploy → smoke test
make help            # Show all commands
```

📚 **For detailed script documentation, usage examples, and troubleshooting**, see [`scripts/README.md`](scripts/README.md)

---

## Testing

### Quick Test Commands

```bash
# Run all automated tests (excludes manual and educational tests)
pytest test_k8s/ -v -m 'not manual and not educational'

# Run all automated tests (includes educational tests)
pytest test_k8s/ -v -m 'not manual'

# Run specific test categories
pytest test_k8s/ -v -m ingress        # Ingress tests only
pytest test_k8s/ -v -m educational    # Educational tests only (hostname routing, consistency, load balancing)
pytest test_k8s/ -v -m nodeport       # NodePort tests only
pytest test_k8s/ -v -m manual         # Manual tests (slow, timing-dependent)

# Run specific test file
pytest test_k8s/test_deployment.py -v

# Simulate CI/CD environment (uses Minikube IP + Host header)
CI=true pytest test_k8s/test_service_ingress.py -v -s
```

**Or use Makefile shortcuts:**
```bash
make test-all            # All automated tests (unit → k8s → smoke)
make k8s-tests           # Kubernetes integration tests
make health-tests        # Health endpoint tests (NodePort switching)
make educational-tests   # Educational Ingress tests
make test-full           # ALL tests (6 categories)
make release-prep        # Complete release workflow
```

**For comprehensive manual testing workflow**, see the [Full Manual Testing](scripts/README.md#full-manual-testing-workflow) section in the Scripts Guide.

### Test Organization

The test suite uses:
- **Shared utilities** (`test_k8s/utils.py`) - 20+ reusable functions for Kubernetes operations
- **Pytest fixtures** (`test_k8s/conftest.py`) - 10+ fixtures for automated test setup
- **Custom markers** - Categorize tests for selective execution (`@pytest.mark.ingress`, `@pytest.mark.nodeport`, `@pytest.mark.manual`)

📚 **For complete test architecture, utilities reference, and debugging guide**, see [`test_k8s/README.md`](test_k8s/README.md)

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **CI/CD & Automation:**
  - [CI/CD Guide](docs/CI_CD_GUIDE.md) - Pipeline overview, GitHub CLI usage, manual testing
  - [CI/CD Troubleshooting](docs/INGRESS_CI_CD_TROUBLESHOOTING.md) - Ingress and pipeline debugging
  - [Scripts Guide](scripts/README.md) - Automation scripts and service access
- **Test Suite:**
  - [Test Architecture](docs/testing/TEST_ARCHITECTURE.md) - Test design and utilities
  - [Test Refactoring](docs/testing/TEST_REFACTORING.md) - Recent improvements
  - [Test Usage Guide](test_k8s/README.md) - How to run tests
  - [Educational Tests](docs/EDUCATIONAL_TESTS.md) - Learn Ingress concepts through hands-on testing
  - [Educational Tests Quick Reference](docs/EDUCATIONAL_TESTS_QUICKREF.md) - Quick commands
- **Kubernetes & Health:**
  - [Probes Guide](docs/PROBES_GUIDE.md) - Comprehensive liveness and readiness probe guide
  - [Ingress Guide](docs/INGRESS_404_EXPLAINED.md) - Ingress issues and troubleshooting
- **Scripts:**
  - [Scripts Guide](scripts/README.md) - Complete script reference and usage
  - [Script Integration](docs/testing/SCRIPT_INTEGRATION.md) - Script integration with pytest markers
- **Operations:**
  - [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md) - Pre-push validation and best practices
  - [Production Considerations](docs/PRODUCTION_CONSIDERATIONS.md) - Beyond "Hello World": Multi-environment configs, observability, load testing

