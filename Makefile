build:
	@bash scripts/build_image.sh

deploy:
	@bash scripts/deploy_local.sh

delete:
	@bash scripts/delete_local.sh

# Additional script targets
k8s-tests:
	@bash scripts/k8s_tests.sh

liveness-test:
	@bash scripts/liveness_test.sh

liveness-test-manual:
	@bash scripts/liveness_test.sh --manual

liveness-test-config:
	@bash scripts/liveness_test.sh --config

readiness-test:
	@bash scripts/readiness_test.sh

readiness-test-manual:
	@bash scripts/readiness_test.sh --manual

readiness-test-config:
	@bash scripts/readiness_test.sh --config

minikube-url:
	@bash scripts/minikube_service_url.sh

port-forward:
	@bash scripts/port_forward.sh

smoke-test:
	@bash scripts/smoke_test.sh

unit-tests:
	@bash scripts/unit_tests.sh

# Coverage tests
test-coverage:
	@bash scripts/coverage_test.sh terminal

test-coverage-html:
	@bash scripts/coverage_test.sh html

test-coverage-xml:
	@bash scripts/coverage_test.sh xml

test-coverage-all:
	@bash scripts/coverage_test.sh all

# Test requirement coverage validation
validate-test-requirements:
	@python scripts/validate_test_coverage.py

validate-test-requirements-verbose:
	@python scripts/validate_test_coverage.py --verbose

# Educational tests (Ingress concepts)
educational-tests:
	@echo "Running educational Ingress tests..."
	@pytest test_k8s/ -m educational -v -s

# All Ingress tests (basic + educational)
ingress-tests:
	@echo "Running all Ingress tests (basic + educational)..."
	@pytest test_k8s/ -m ingress -v -s

# Health endpoint tests (requires NodePort, temporarily switches service)
health-tests:
	@bash scripts/health_endpoint_tests.sh

# Validation targets
validate-repo:
	@bash scripts/validate_repo_structure.sh

validate-workflow:
	@bash scripts/validate_workflow.sh

validate-all: validate-repo validate-workflow

# Changelog generation
changelog:
	@bash scripts/generate_changelog.sh

changelog-since:
	@bash scripts/generate_changelog.sh $(TAG)

changelog-range:
	@bash scripts/generate_changelog.sh $(FROM) $(TO)

changelog-dev:
	@echo "" >> CHANGELOG.md
	@echo "---" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "## Auto-generated Entry" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "**Generated:** $$(date '+%Y-%m-%d %H:%M:%S')" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@bash scripts/generate_changelog.sh $(if $(TAG),$(TAG)) $(if $(TO),$(TO)) --markdown-only >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "✅ Changelog appended to CHANGELOG.md"

changelog-dev-since:
	@echo "" >> CHANGELOG.md
	@echo "---" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "## Auto-generated Entry" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "**Generated:** $$(date '+%Y-%m-%d %H:%M:%S')" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "**Since:** $(TAG)" >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@bash scripts/generate_changelog.sh $(TAG) --markdown-only >> CHANGELOG.md
	@echo "" >> CHANGELOG.md
	@echo "✅ Changelog appended to CHANGELOG.md"

# Run all tests (unit + k8s)
test-all: unit-tests k8s-tests

# Run ALL tests including manual and educational (comprehensive development testing)
test-full:
	@echo "======================================"
	@echo "Running FULL Test Suite"
	@echo "======================================"
	@echo ""
	@echo "1/5: Unit Tests"
	@echo "--------------------------------------"
	@bash scripts/unit_tests.sh
	@echo ""
	@echo "2/5: K8s Integration Tests (automated)"
	@echo "--------------------------------------"
	@bash scripts/k8s_tests.sh
	@echo ""
	@echo "3/5: Educational Ingress Tests"
	@echo "--------------------------------------"
	@pytest test_k8s/ -m educational -v
	@echo ""
	@echo "4/5: Health Endpoint Tests (NodePort)"
	@echo "--------------------------------------"
	@bash scripts/health_endpoint_tests.sh
	@echo ""
	@echo "5/5: Manual Tests (crash recovery)"
	@echo "--------------------------------------"
	@pytest test_k8s/ -m manual -v
	@echo ""
	@echo "======================================"
	@echo "✅ FULL TEST SUITE COMPLETED"
	@echo "======================================"

# Complete workflow
full-deploy: build deploy smoke-test

# Release preparation workflow
release-prep:
	@echo "=========================================="
	@echo "🚀 RELEASE PREPARATION WORKFLOW"
	@echo "=========================================="
	@echo ""
	@echo "Step 1/6: Repository Validation"
	@echo "------------------------------------------"
	@bash scripts/validate_repo_structure.sh
	@bash scripts/validate_workflow.sh
	@echo ""
	@echo "Step 2/6: Test Requirement Coverage"
	@echo "------------------------------------------"
	@python scripts/validate_test_coverage.py
	@echo ""
	@echo "Step 3/6: Running Full Test Suite"
	@echo "------------------------------------------"
	@$(MAKE) test-full
	@echo ""
	@echo "Step 4/6: Building Docker Image"
	@echo "------------------------------------------"
	@bash scripts/build_image.sh
	@echo ""
	@echo "Step 5/6: Deploying to Local Cluster"
	@echo "------------------------------------------"
	@bash scripts/deploy_local.sh
	@echo ""
	@echo "Step 6/6: Final Smoke Test"
	@echo "------------------------------------------"
	@bash scripts/smoke_test.sh
	@echo ""
	@echo "=========================================="
	@echo "✅ RELEASE PREPARATION COMPLETED"
	@echo "=========================================="
	@echo ""
	@echo "📋 RELEASE CHECKLIST:"
	@echo "  [✓] Repository structure validated"
	@echo "  [✓] Development workflow validated"
	@echo "  [✓] Test requirement coverage validated (22/22 tests present)"
	@echo "  [✓] All tests passed (unit + integration)"
	@echo "  [✓] Docker image built successfully"
	@echo "  [✓] Application deployed to local cluster"
	@echo "  [✓] Smoke test passed"
	@echo "  [ ] Review and update CHANGELOG.md"
	@echo "  [ ] Update version numbers (if applicable)"
	@echo "  [ ] Commit all changes: git add . && git commit -m 'Release vX.Y.Z'"
	@echo "  [ ] Create git tag: git tag -a vX.Y.Z -m 'Release vX.Y.Z'"
	@echo "  [ ] Push changes: git push origin main"
	@echo "  [ ] Push tag: git push origin vX.Y.Z"
	@echo "  [ ] Create GitHub release from tag"
	@echo ""
	@echo "To generate changelog since last tag, run:"
	@echo "  make changelog-since TAG=<previous-tag>"
	@echo ""

# Help target to show available commands
help:
	@echo "Available targets:"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build         - Build Docker image"
	@echo "  deploy        - Deploy to local cluster"
	@echo "  delete        - Delete local deployment"
	@echo "  full-deploy   - Build, deploy, and run smoke tests"
	@echo "  release-prep  - Complete release preparation workflow (validate structure & workflow, verify test requirements, test-full, build, deploy, smoke)"
	@echo ""
	@echo "Testing:"
	@echo "  unit-tests           - Run unit tests"
	@echo "  test-coverage        - Run unit tests with coverage (terminal report)"
	@echo "  test-coverage-html   - Run unit tests with HTML coverage report"
	@echo "  test-coverage-xml    - Run unit tests with XML coverage report (CI/CD)"
	@echo "  test-coverage-all    - Run unit tests with all coverage formats"
	@echo "  validate-test-requirements - Validate all documented tests are implemented"
	@echo "  validate-test-requirements-verbose - Same with detailed test listing"
	@echo "  k8s-tests            - Run k8s integration tests (excludes manual & educational)"
	@echo "  educational-tests    - Run educational Ingress tests (hostname routing, consistency, load balancing)"
	@echo "  ingress-tests        - Run all Ingress tests (basic + educational)"
	@echo "  health-tests         - Run health endpoint tests (temporarily uses NodePort)"
	@echo "  smoke-test           - Run smoke tests (quick validation)"
	@echo "  test-all             - Run all automated tests (unit + k8s)"
	@echo "  test-full            - Run ALL tests including manual, educational, and nodeport (comprehensive)"
	@echo ""
	@echo "Probe Tests:"
	@echo "  Liveness Probe:"
	@echo "    liveness-test        - Run automated liveness probe configuration tests"
	@echo "    liveness-test-manual - Run manual behavioral tests (pod deletion, crash recovery)"
	@echo "    liveness-test-config - Run only liveness probe configuration check"
	@echo "  Readiness Probe:"
	@echo "    readiness-test        - Run automated readiness probe configuration tests"
	@echo "    readiness-test-manual - Run manual readiness behavioral tests"
	@echo "    readiness-test-config - Run only readiness probe configuration check"
	@echo ""
	@echo "Utilities:"
	@echo "  port-forward  - Forward service port to localhost"
	@echo "  minikube-url  - Get service URL and access methods"
	@echo ""
	@echo "Validation:"
	@echo "  validate-repo     - Validate repository structure"
	@echo "  validate-workflow - Validate GitHub Actions workflow configuration"
	@echo "  validate-all      - Run all validation checks"
	@echo "  changelog     - Generate changelog from all commits"
	@echo "  changelog-since TAG=v1.0.0 - Generate changelog since a specific tag"
	@echo "  changelog-range FROM=v1.0.0 TO=v2.0.0 - Generate changelog between tags"
	@echo "  changelog-dev - Append auto-generated changelog to CHANGELOG.md"
	@echo "  changelog-dev-since TAG=v1.0.0 - Append changelog since tag to CHANGELOG.md"
	@echo "  full-deploy   - Complete build, deploy, and smoke test"
	@echo "  help          - Show this help message"
