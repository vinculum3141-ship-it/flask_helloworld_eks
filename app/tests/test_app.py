"""
Unit tests for the Flask application.

This module contains unit tests that validate the core functionality of the Flask
application, including:

- HTTP response validation: Ensures the root endpoint returns 200 OK status
- Content validation: Verifies the response body contains the expected JSON message
- Performance testing: Validates that the application responds within acceptable latency (<1s)
- Error handling: Tests that invalid routes properly return 404 Not Found status

Test Scenarios:
    1. test_home_returns_200_ok(): Validates that GET request to '/' returns 200 OK status
    2. test_home_response_content(): Verifies the response contains the expected JSON message
    3. test_response_latency(): Ensures app responds within 1 second
    4. test_invalid_route_returns_404(): Verifies 404 status for non-existent routes

Fixtures:
    - client: Flask test client for making requests
    - home_response: Response object from GET request to '/'

Usage:
    Run tests using pytest:
        $ pytest app/tests/test_app.py -v
    
    Or using the Makefile:
        $ make unit-tests
"""

import time
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def home_response(client):
    """Get the response from the home route."""
    return client.get('/')


def test_home_returns_200_ok(home_response):
    """Test that HTTP GET to / returns 200 OK status."""
    assert home_response.status_code == 200


def test_home_response_content(home_response):
    """Test that the response body contains the expected JSON message."""
    # The Flask view now returns JSON. Check the content type and JSON payload.
    assert home_response.content_type == "application/json"
    assert home_response.get_json() == {"message": "Hello from Flask on Kubernetes (Minikube)!"}


def test_response_latency(client):
    """Test that the app responds within acceptable latency (< 1 second)."""
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    latency = end_time - start_time
    assert response.status_code == 200
    assert latency < 1.0, f"Response took {latency:.3f}s, expected < 1.0s"


def test_invalid_route_returns_404(client):
    """Test that invalid routes return 404 Not Found."""
    # Test various invalid routes
    invalid_routes = [
        '/invalid',
        '/nonexistent',
        '/api/unknown',
        '/random/path'
    ]
    
    for route in invalid_routes:
        response = client.get(route)
        assert response.status_code == 404, f"Route {route} should return 404, got {response.status_code}"


def test_health_endpoint_returns_200(client):
    """Test that the /health endpoint returns 200 OK status."""
    response = client.get('/health')
    assert response.status_code == 200


def test_health_endpoint_content(client):
    """Test that the /health endpoint returns the expected JSON response."""
    response = client.get('/health')
    assert response.content_type == "application/json"
    assert response.get_json() == {"status": "healthy"}


def test_health_endpoint_performance(client):
    """
    Test that the /health endpoint responds quickly.
    
    Educational Note:
    Kubernetes liveness probe has timeoutSeconds: 5, but health checks
    should be much faster. This test ensures /health responds in < 100ms.
    """
    start_time = time.time()
    response = client.get('/health')
    end_time = time.time()
    
    latency = end_time - start_time
    assert response.status_code == 200
    assert latency < 0.1, f"/health took {latency:.3f}s, expected < 0.1s (liveness timeout is 5s)"


def test_ready_endpoint_returns_200(client):
    """Test that the /ready endpoint returns 200 OK status."""
    response = client.get('/ready')
    assert response.status_code == 200


def test_ready_endpoint_content(client):
    """Test that the /ready endpoint returns the expected JSON response."""
    response = client.get('/ready')
    assert response.content_type == "application/json"
    assert response.get_json() == {"status": "ready"}


def test_ready_endpoint_performance(client):
    """
    Test that the /ready endpoint responds quickly.
    
    Readiness checks happen frequently (every 5s by default).
    Slow responses can delay pod receiving traffic.
    """
    start_time = time.time()
    response = client.get('/ready')
    end_time = time.time()
    
    latency = end_time - start_time
    assert response.status_code == 200
    assert latency < 0.1, f"Readiness check took {latency:.3f}s, expected < 0.1s"


def test_ready_endpoint_cache_control(client):
    """
    Test that /ready endpoint explicitly disables caching.
    
    Similar to /health, readiness checks need real-time status.
    Cached responses could route traffic to pods that aren't actually ready.
    """
    response = client.get('/ready')
    
    # Verify Cache-Control headers
    assert response.headers.get('Cache-Control') == 'no-cache, no-store, must-revalidate', \
        "Cache-Control header should prevent caching"
    assert response.headers.get('Pragma') == 'no-cache', "Pragma header should prevent HTTP/1.0 caching"
    assert response.headers.get('Expires') == '0', "Expires header should prevent caching"
    
    assert response.status_code == 200


def test_ready_vs_health_independence(client):
    """
    Test that /ready and /health are independent endpoints.
    
    Educational Note:
    - /health (liveness): Is the process alive? → Restarts pod if fails
    - /ready (readiness): Ready for traffic? → Removes from service if fails
    
    Both should work independently.
    """
    health_response = client.get('/health')
    ready_response = client.get('/ready')
    
    assert health_response.status_code == 200
    assert ready_response.status_code == 200
    
    # Different content
    assert health_response.get_json() == {"status": "healthy"}
    assert ready_response.get_json() == {"status": "ready"}
    
    # Both should be fast
    for endpoint in ['/health', '/ready']:
        start = time.time()
        client.get(endpoint)
        latency = time.time() - start
        assert latency < 0.1, f"{endpoint} too slow: {latency:.3f}s"


def test_ready_endpoint_http_methods(client):
    """
    Test that /ready only accepts GET requests.
    
    Educational Note:
    Kubernetes readiness probes only send GET requests. Other HTTP methods
    should return 405 Method Not Allowed to follow REST principles.
    
    Why this matters:
    - Readiness endpoint should be read-only (checking status, not modifying)
    - POST/PUT/DELETE could imply state changes (inappropriate for health checks)
    - Proper HTTP semantics improve API clarity and security
    """
    # GET should work (this is what K8s probe uses)
    response = client.get('/ready')
    assert response.status_code == 200
    
    # POST should fail (readiness check is read-only)
    response = client.post('/ready')
    assert response.status_code == 405, "POST to /ready should return 405 Method Not Allowed"
    
    # PUT should fail
    response = client.put('/ready')
    assert response.status_code == 405, "PUT to /ready should return 405 Method Not Allowed"
    
    # DELETE should fail
    response = client.delete('/ready')
    assert response.status_code == 405, "DELETE to /ready should return 405 Method Not Allowed"


def test_ready_endpoint_consistency(client):
    """
    Test that /ready returns consistent results across multiple calls.
    
    Educational Note:
    From k8s/deployment.yaml:
      readinessProbe:
        periodSeconds: 5        # Checked every 5 seconds
        initialDelaySeconds: 2  # First check after 2 seconds
    
    With 2 replicas: 2 pods × 12 checks/min = 24 checks/min = 1,440 checks/hour
    
    Implications of inconsistent results:
    - Pod repeatedly added/removed from Service endpoints
    - "Flapping" causes traffic routing instability
    - Users experience intermittent connection failures
    - Load balancer constantly reconfigures
    
    The endpoint MUST be idempotent and stateless.
    """
    responses = [client.get('/ready') for _ in range(10)]
    
    # All should return 200
    for i, response in enumerate(responses, 1):
        assert response.status_code == 200, f"Call {i} failed"
        assert response.get_json() == {"status": "ready"}, \
            f"Call {i} returned different content"
    
    # All should have same cache headers (no randomness/variation)
    first_cache_control = responses[0].headers.get('Cache-Control')
    for i, response in enumerate(responses[1:], 2):
        assert response.headers.get('Cache-Control') == first_cache_control, \
            f"Call {i} has different Cache-Control headers"


def test_ready_endpoint_no_side_effects(client):
    """
    Test that calling /ready has no side effects.
    
    Educational Note:
    Readiness checks run every 5 seconds (periodSeconds: 5).
    
    Daily call volume:
    - 1 pod: 12 calls/min × 60 min × 24 hrs = 17,280 calls/day
    - 2 pods (our config): 34,560 calls/day
    
    The endpoint must:
    - Not modify application state
    - Not write to databases or logs excessively
    - Not consume significant resources (CPU, memory, I/O)
    - Not trigger downstream operations
    - Be truly read-only and lightweight
    
    Violating this causes:
    - Resource exhaustion (disk from logs, memory from state)
    - Performance degradation
    - Unexpected side effects from "health checks"
    """
    # Simulate frequent probe calls (20 rapid calls)
    for _ in range(20):
        response = client.get('/ready')
        assert response.status_code == 200
    
    # Main app should still work normally (no state corruption)
    root_response = client.get('/')
    assert root_response.status_code == 200
    assert root_response.get_json() == {
        "message": "Hello from Flask on Kubernetes (Minikube)!"
    }
    
    # Health check should also be unaffected
    health_response = client.get('/health')
    assert health_response.status_code == 200
    assert health_response.get_json() == {"status": "healthy"}


def test_ready_endpoint_cache_control_detailed(client):
    """
    Test that /ready endpoint explicitly disables caching with full documentation.
    
    Educational Note:
    Kubernetes readiness probe determines traffic routing. Cached responses are dangerous.
    
    Scenario - Cached "ready" response when pod is NOT ready:
    1. t=0s:  Pod is ready, /ready returns 200 OK
    2. t=1s:  Database connection fails, pod is NOW UNREADY
    3. t=2s:  Cached response still says "ready" (stale data)
    4. t=3s:  Service continues routing NEW traffic to failing pod
    5. t=4s:  Users get 500 errors (database unavailable)
    6. t=5s:  Next probe check (non-cached) detects failure
    7. Result: 4 seconds of bad traffic routing, user impact
    
    Cache-Control headers ensure real-time status:
    - no-cache: Must revalidate with server before using cached copy
    - no-store: Must not store response in cache at all
    - must-revalidate: Cached copy must not be used when stale
    
    Comparison with Liveness:
    - Liveness (cached): Delays pod restart → extended downtime
    - Readiness (cached): Routes traffic to bad pods → user-facing errors
    - Readiness is MORE CRITICAL (immediate user impact)
    
    Additional headers for compatibility:
    - Pragma: no-cache (HTTP/1.0 clients, old proxies)
    - Expires: 0 (immediate expiration fallback)
    """
    response = client.get('/ready')
    
    # Verify all cache prevention headers present
    cache_control = response.headers.get('Cache-Control')
    assert cache_control is not None, "Cache-Control header must be present"
    
    # Verify specific directives
    assert 'no-cache' in cache_control, \
        "Must include 'no-cache' - prevents serving stale readiness status"
    assert 'no-store' in cache_control, \
        "Must include 'no-store' - prevents storage of readiness state"
    assert 'must-revalidate' in cache_control, \
        "Must include 'must-revalidate' - ensures fresh traffic routing decisions"
    
    # HTTP/1.0 compatibility (older proxies, load balancers)
    assert response.headers.get('Pragma') == 'no-cache', \
        "Pragma ensures old proxies/load balancers don't cache readiness status"
    
    # Immediate expiration (fallback mechanism)
    assert response.headers.get('Expires') == '0', \
        "Expires: 0 prevents any temporal caching of traffic routing state"
    
    # Verify endpoint still works correctly
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_health_endpoint_http_methods(client):
    """
    Test that /health only accepts GET requests.
    
    Educational Note:
    Kubernetes probes only send GET requests. Other HTTP methods
    should return 405 Method Not Allowed to follow REST principles.
    """
    # GET should work
    response = client.get('/health')
    assert response.status_code == 200
    
    # POST should fail (not supported)
    response = client.post('/health')
    assert response.status_code == 405, "POST to /health should return 405 Method Not Allowed"
    
    # PUT should fail
    response = client.put('/health')
    assert response.status_code == 405, "PUT to /health should return 405 Method Not Allowed"
    
    # DELETE should fail
    response = client.delete('/health')
    assert response.status_code == 405, "DELETE to /health should return 405 Method Not Allowed"


def test_health_endpoint_consistency(client):
    """
    Test that /health returns consistent results across multiple calls.
    
    Educational Note:
    Health checks should be idempotent and deterministic. Multiple calls
    should return identical results (Kubernetes makes frequent probe checks).
    """
    responses = [client.get('/health') for _ in range(10)]
    
    # All should return 200
    for i, response in enumerate(responses, 1):
        assert response.status_code == 200, f"Call {i} failed"
        assert response.get_json() == {"status": "healthy"}, f"Call {i} returned different content"


def test_health_vs_root_endpoint_independence(client):
    """
    Test that /health is independent from / (main app logic).
    
    Educational Note:
    Liveness probe (/health) should check if Flask is alive, not business logic.
    Readiness probe (/) checks if the app can serve traffic.
    They serve different purposes and should remain independent.
    """
    # Both endpoints should work
    health_response = client.get('/health')
    root_response = client.get('/')
    
    assert health_response.status_code == 200, "/health should work"
    assert root_response.status_code == 200, "/ should work"
    
    # They should return different content (different purposes)
    assert health_response.get_json() != root_response.get_json(), \
        "/health and / should have different responses (different purposes)"
    
    # Health should be simpler (just status check)
    health_data = health_response.get_json()
    assert "status" in health_data, "/health should have 'status' field"
    assert len(health_data) == 1, "/health should be simple (only 1 field)"
    
    # Root has application data
    root_data = root_response.get_json()
    assert "message" in root_data, "/ should have 'message' field (app data)"


def test_health_endpoint_no_side_effects(client):
    """
    Test that calling /health has no side effects.
    
    Educational Note:
    Health checks are called frequently (every 10s for liveness).
    They must not modify application state, write to databases,
    or consume significant resources.
    """
    # Call /health multiple times
    for _ in range(5):
        response = client.get('/health')
        assert response.status_code == 200
    
    # Main app should still work normally (no side effects)
    root_response = client.get('/')
    assert root_response.status_code == 200
    assert root_response.get_json() == {"message": "Hello from Flask on Kubernetes (Minikube)!"}


def test_health_endpoint_headers(client):
    """
    Test that /health returns appropriate HTTP headers.
    
    Educational Note:
    Health endpoints should return proper Content-Type and
    avoid caching (health status should be real-time).
    """
    response = client.get('/health')
    
    # Should be JSON
    assert response.content_type == "application/json"
    
    # Should not be cached (health status should be real-time)
    cache_control = response.headers.get('Cache-Control', '')
    assert 'no-cache' in cache_control, "Health endpoint should have 'no-cache' directive"
    assert 'no-store' in cache_control, "Health endpoint should have 'no-store' directive"
    
    # Additional cache prevention headers
    assert response.headers.get('Pragma') == 'no-cache', "Pragma header should prevent HTTP/1.0 caching"
    assert response.headers.get('Expires') == '0', "Expires header should prevent caching"
    
    assert response.status_code == 200


def test_health_endpoint_cache_control(client):
    """
    Test that /health endpoint explicitly disables caching.
    
    Educational Note:
    Kubernetes liveness probes check current health status. Cached responses
    could hide failures, leading to:
    - False-positive health checks (serving stale "healthy" when actually failed)
    - Delayed pod restarts (probe doesn't detect failure in time)
    - Inaccurate health monitoring
    
    Cache-Control headers ensure real-time health status:
    - no-cache: Must revalidate with server before using cached copy
    - no-store: Must not store response in cache at all
    - must-revalidate: Cached copy must not be used after it becomes stale
    
    Additional headers for compatibility:
    - Pragma: no-cache (for HTTP/1.0 compatibility)
    - Expires: 0 (immediate expiration)
    """
    response = client.get('/health')
    
    # Verify all cache prevention headers are present
    cache_control = response.headers.get('Cache-Control')
    assert cache_control is not None, "Cache-Control header must be present"
    
    # Verify Cache-Control directives
    assert 'no-cache' in cache_control, "Must include 'no-cache' to prevent cached responses"
    assert 'no-store' in cache_control, "Must include 'no-store' to prevent storage"
    assert 'must-revalidate' in cache_control, "Must include 'must-revalidate' for strictness"
    
    # Verify HTTP/1.0 compatibility
    assert response.headers.get('Pragma') == 'no-cache', \
        "Pragma: no-cache ensures HTTP/1.0 clients don't cache"
    
    # Verify immediate expiration
    assert response.headers.get('Expires') == '0', \
        "Expires: 0 indicates immediate expiration"
    
    # Verify endpoint still works correctly
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}

