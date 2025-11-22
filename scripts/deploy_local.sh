#!/bin/bash
set -euo pipefail

# Source common utilities
source "$(dirname "$0")/lib/common.sh"

# Enable debug mode if requested
enable_debug_mode

LOG_DIR="${PWD}/logs"
mkdir -p "${LOG_DIR}"

collect_diagnostics() {
  log_error "=== COLLECTING DIAGNOSTICS ==="
  echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" | tee "${LOG_DIR}/diag.txt"

  echo -e "\n--- kubectl cluster-info ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube kubectl -- cluster-info 2>&1 | tee -a "${LOG_DIR}/diag.txt"

  echo -e "\n--- kubectl get nodes -o wide ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube kubectl -- get nodes -o wide 2>&1 | tee -a "${LOG_DIR}/diag.txt"

  echo -e "\n--- kubectl get pods -A -o wide ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube kubectl -- get pods -A -o wide 2>&1 | tee -a "${LOG_DIR}/diag.txt"

  echo -e "\n--- kubectl describe pods (app label) ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube kubectl -- describe pod -l app=hello-flask --all-namespaces 2>&1 | tee -a "${LOG_DIR}/diag.txt" || true

  echo -e "\n--- kubectl get events (last 200) ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube kubectl -- get events -A --sort-by='.metadata.creationTimestamp' 2>&1 | tail -n 200 | tee -a "${LOG_DIR}/diag.txt" || true

  PODS=$(minikube kubectl -- get pods -l app=hello-flask -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' || true)
  if [[ -n "${PODS}" ]]; then
    for p in ${PODS}; do
      echo -e "\n--- logs for pod: ${p} ---" | tee -a "${LOG_DIR}/diag.txt"
      CONTAINERS=$(minikube kubectl -- get pod "${p}" -o jsonpath='{.spec.containers[*].name}' || true)
      for c in ${CONTAINERS}; do
        echo "--- container: ${c} ---" >> "${LOG_DIR}/diag.txt"
        minikube kubectl -- logs "${p}" -c "${c}" --tail=500 2>&1 | tee -a "${LOG_DIR}/diag.txt" || true
      done
    done
  else
    echo "No pods found with label app=hello-flask" | tee -a "${LOG_DIR}/diag.txt"
  fi

  echo -e "\n--- minikube logs (tail 500) ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube logs 2>&1 | tail -n 500 | tee -a "${LOG_DIR}/diag.txt" || true

  echo -e "\n--- minikube image list ---" | tee -a "${LOG_DIR}/diag.txt"
  minikube image list 2>&1 | tee -a "${LOG_DIR}/diag.txt" || true

  echo -e "\n--- docker images (current DOCKER env) ---" | tee -a "${LOG_DIR}/diag.txt"
  docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}' 2>&1 | tee -a "${LOG_DIR}/diag.txt" || true

  log_note "Diagnostics collected in ${LOG_DIR}/diag.txt"
}

trap 'rc=$?; log_error "deploy_local.sh failed with exit ${rc}"; collect_diagnostics; exit ${rc}' ERR

deploy_app() {
    echo ""
    log_info "Applying ConfigMap..."
    minikube kubectl -- apply -f k8s/configmap.yaml

    log_info "Applying Secret..."
    minikube kubectl -- apply -f k8s/secret.yaml

    log_info "Deploying Deployment & Service..."
    minikube kubectl -- apply -f k8s/deployment.yaml
    minikube kubectl -- apply -f k8s/service.yaml

    log_info "Deploying Ingress..."
    minikube kubectl -- apply -f k8s/ingress.yaml

    log_info "Waiting for deployment rollout (timeout 5m)..."
    # add a timeout so this step doesn't hang indefinitely
    minikube kubectl -- rollout status deployment/hello-flask --timeout=5m

    log_info "App deployed successfully."
}

# Main execution
print_header "Deploying to Minikube"
deploy_app
log_success "Deployment completed!"
log_note "Run 'kubectl get pods' to check pod status"
echo ""
