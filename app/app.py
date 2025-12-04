"""
This code defines a simple web application using Flask.
It creates a single route at the root URL ("/") that returns the message "Hello from Flask on Kubernetes (Minikube)!".
When run directly, it starts a web server listening on all network interfaces at port 5000.
This is typically used as a minimal example for deploying Flask apps, such as in a Kubernetes environment.
"""

import time
import logging
import json
from datetime import datetime, timezone
import werkzeug
from flask import Flask, jsonify, request

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Use simple format since we're doing structured JSON logging
)
logger = logging.getLogger(__name__)

# Compatibility shim: Werkzeug 3.x removed the `__version__` attribute that
# older Flask test utilities reference. Provide a fallback so tests and
# the Flask test client keep working when Werkzeug 3.x is installed.
if not hasattr(werkzeug, "__version__"):
    # set a reasonable default version string used only for compatibility checks
    werkzeug.__version__ = "3.0.0"


app = Flask(__name__)

# Simple in-memory metrics (educational purposes only - resets on pod restart)
app_start_time = time.time()
request_count = 0


def log_event(event, endpoint, **extra_fields):
    """
    Helper function for structured logging.
    
    Args:
        event: Event type (e.g., 'request', 'health_check', 'metrics_request')
        endpoint: API endpoint being accessed
        **extra_fields: Additional fields to include in the log entry
    """
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "endpoint": endpoint
    }
    log_data.update(extra_fields)
    logger.info(json.dumps(log_data))


@app.route("/")
def hello():
    """Main endpoint - returns greeting message."""
    global request_count
    request_count += 1
    
    # Structured logging
    log_event(
        event="request",
        endpoint="/",
        method=request.method,
        remote_addr=request.remote_addr,
        request_count=request_count
    )
    
    return jsonify(message="Hello from Flask on Kubernetes (Minikube)!")


@app.route("/health")
def health():
    """
    Health check endpoint for Kubernetes liveness probe.
    Returns a simple status indicating the application is alive.
    
    Note: Cache-Control headers prevent caching to ensure real-time health status.
    """
    log_event(
        event="health_check",
        endpoint="/health",
        status="healthy"
    )
    
    response = jsonify(status="healthy")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response, 200


@app.route("/ready")
def ready():
    """
    Readiness check endpoint for Kubernetes readiness probe.
    Indicates whether the application is ready to receive traffic.
    
    For this simple application:
    - Always returns 200 (no dependencies to check)
    - Could be enhanced to check database, cache, or external service connections
    
    Note: Different from /health (liveness) - readiness controls traffic routing,
    liveness controls pod restarts.
    """
    log_event(
        event="readiness_check",
        endpoint="/ready",
        status="ready"
    )
    
    response = jsonify(status="ready")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response, 200


@app.route("/metrics")
def metrics():
    """
    Simple metrics endpoint for observability (educational purposes).
    
    Returns basic application metrics in JSON format.
    
    Note: This is a simplified metrics implementation for learning.
    Production applications would use Prometheus client library for
    standardized metrics format.
    
    See docs/PRODUCTION_CONSIDERATIONS.md for production observability patterns.
    """
    uptime_seconds = time.time() - app_start_time
    
    log_event(
        event="metrics_request",
        endpoint="/metrics"
    )
    
    return jsonify({
        "app": "hello-flask",
        "version": "1.0.0",
        "uptime_seconds": round(uptime_seconds, 2),
        "request_count": request_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "running"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
