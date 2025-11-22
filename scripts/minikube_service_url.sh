#!/bin/bash
# -----------------------------------------------------------------------------
# NOTE: Manual helper script (not used by CI)
#
# This script gets the service URL and tests access to the Flask app.
# Works with both NodePort and ClusterIP (Ingress) service types.
#
# For NodePort:
#   - Uses `minikube service hello-flask --url`
#
# For ClusterIP with Ingress:
#   - Uses Ingress hostname (hello-flask.local) or Minikube IP with Host header
#
# In CI, this functionality is tested via pytest:
#   - See: `test_k8s/test_service_nodeport.py` (NodePort tests)
#   - See: `test_k8s/test_service_ingress.py` (Ingress tests)
#
# Use this script locally during development; CI runs stronger assertions in tests.
# -----------------------------------------------------------------------------
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

get_service_url() {
    log_info "Checking service type..."
    SERVICE_TYPE=$(kubectl get svc hello-flask -o jsonpath='{.spec.type}' 2>/dev/null || echo "NotFound")
    
    if [ "$SERVICE_TYPE" = "NotFound" ]; then
        log_error "Service 'hello-flask' not found. Please deploy it first."
        exit 1
    fi
    
    echo "[INFO] Service type: $SERVICE_TYPE"
    
    if [ "$SERVICE_TYPE" = "NodePort" ]; then
        echo "[INFO] Fetching NodePort service URL..."
        URL=$(minikube service hello-flask --url)
        echo "[INFO] Access your app at: $URL"
        echo "[INFO] Testing the service..."
        curl -s $URL || echo "[ERROR] Curl failed"
        
    elif [ "$SERVICE_TYPE" = "ClusterIP" ]; then
        echo "[INFO] Service is ClusterIP (used with Ingress)"
        
        # Check if Ingress exists
        if kubectl get ingress hello-flask-ingress &> /dev/null; then
            INGRESS_HOST=$(kubectl get ingress hello-flask-ingress -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "hello-flask.local")
            MINIKUBE_IP=$(minikube ip)
            
            echo "[INFO] Ingress hostname: $INGRESS_HOST"
            echo "[INFO] Minikube IP: $MINIKUBE_IP"
            echo ""
            echo "Access your app via one of these methods:"
            echo ""
            echo "  1. Via hostname (requires /etc/hosts configured):"
            echo "     curl http://$INGRESS_HOST"
            echo ""
            echo "  2. Via Minikube IP with Host header:"
            echo "     curl -H \"Host: $INGRESS_HOST\" http://$MINIKUBE_IP"
            echo ""
            echo "  3. Via port-forward (bypasses Ingress):"
            echo "     kubectl port-forward svc/hello-flask 5000:5000"
            echo "     curl http://localhost:5000"
            echo ""
            
            # Try hostname first
            echo "[INFO] Testing via hostname..."
            if curl -s http://$INGRESS_HOST --max-time 3 &> /dev/null; then
                echo "[SUCCESS] App is accessible via: http://$INGRESS_HOST"
                curl -s http://$INGRESS_HOST
            else
                echo "[INFO] Hostname not resolving (run scripts/setup_ingress.sh to configure /etc/hosts)"
                echo "[INFO] Testing via Minikube IP with Host header..."
                curl -s -H "Host: $INGRESS_HOST" http://$MINIKUBE_IP || echo "[ERROR] Curl failed"
            fi
        else
            echo "[WARN] No Ingress found. For ClusterIP services, you need Ingress."
            echo "[INFO] Either:"
            echo "  1. Deploy Ingress: kubectl apply -f k8s/ingress.yaml"
            echo "  2. Change service to NodePort in k8s/service.yaml"
            echo "  3. Use port-forward: kubectl port-forward svc/hello-flask 5000:5000"
        fi
    else
        echo "[WARN] Unsupported service type: $SERVICE_TYPE"
        exit 1
    fi
}

# Run function
get_service_url
