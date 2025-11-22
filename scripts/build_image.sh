#!/bin/bash
# -----------------------------------------------------------------------------
# NOTE: Example helper script (manual use)
#
# This script demonstrates building the Docker image inside Minikube's Docker
# daemon for local/manual testing. It is NOT invoked by the CI workflows.
#
# In CI, the image build is handled directly in the workflow steps (pointing the
# Docker CLI to Minikube and running `docker build` inline). The workflow also
# manages tags (e.g., both `:latest` and `:${GITHUB_SHA}`) and logging.
#
# Use this script locally to validate a build in your Minikube environment. The
# Deployment in k8s/deployment.yaml references `hello-flask:latest`, so this
# script tags `:latest` only.
# -----------------------------------------------------------------------------

set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

# Function: build Docker image for Minikube
build_image() {
    log_info "Switching to Minikube Docker environment..."
    eval $(minikube docker-env)

    log_info "Building Docker image 'hello-flask:latest'..."
    docker build -t hello-flask:latest ./app

    echo ""
    log_info "Docker image built successfully."
    log_note "Available images:"
    docker images | grep hello-flask || echo "No hello-flask images found"
}

# Main execution
print_header "Building Docker Image"
echo ""
build_image
echo ""
log_success "Image build completed!"
echo ""
