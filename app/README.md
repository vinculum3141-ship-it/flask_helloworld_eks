# Flask Application

Simple "Hello World" Flask application for Kubernetes deployment.

## Requirements Files

This directory contains two requirements files:

### `requirements.txt` (Production)
Production dependencies only - used in Docker image and production deployment.

**Contents:**
- `Flask==2.3.2` - Web framework

**Used by:**
- Dockerfile
- Production deployments
- CI/CD pipelines (for building images)

**Install:**
```bash
pip install -r requirements.txt
```

### `requirements-dev.txt` (Development/Testing)
Development and testing dependencies - includes production requirements plus testing tools.

**Contents:**
- `-r requirements.txt` - Inherits production dependencies
- `pytest==7.4.3` - Testing framework
- `pytest-cov==4.1.0` - Test coverage metrics
- `requests==2.31.0` - HTTP client for K8s API and service testing
- `yamllint==1.32.0` - YAML validation for K8s manifests

**Used by:**
- Local development
- Running unit tests
- Running K8s integration tests
- Coverage analysis
- YAML manifest validation
- CI/CD pipelines (for testing)

**Install:**
```bash
pip install -r requirements-dev.txt
```

## Why Separate Files?

**Benefits:**
- ✅ **Smaller Docker images** - Production images don't include test dependencies
- ✅ **Faster deployments** - Fewer packages to install in production
- ✅ **Security** - Reduced attack surface in production
- ✅ **Clear separation** - Explicit distinction between production and development needs
- ✅ **Standard practice** - Follows Python packaging best practices

## Usage Examples

### Production Deployment
```bash
# In Dockerfile
RUN pip install -r requirements.txt
```

### Local Development
```bash
# Install everything needed for development
pip install -r requirements-dev.txt

# Run tests
pytest app/tests/

# Run tests with coverage
pytest app/tests/ --cov=app --cov-report=html
```

### CI/CD Pipeline
```yaml
# Build stage (for Docker image)
- pip install -r app/requirements.txt

# Test stage (for running tests)
- pip install -r app/requirements-dev.txt
- pytest app/tests/ --cov=app
```

## Application Structure

```
app/
├── __init__.py           # Package initialization
├── app.py                # Flask application code
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development/testing dependencies
├── Dockerfile            # Container image definition
└── tests/
    └── test_app.py       # Unit tests
```

## Running the Application

### Locally (Development)
```bash
cd app
python app.py
```

### In Docker
```bash
# Build
docker build -t flask-hello-world:local app/

# Run
docker run -p 5000:5000 flask-hello-world:local
```

### In Kubernetes
See main project README for Kubernetes deployment instructions.
