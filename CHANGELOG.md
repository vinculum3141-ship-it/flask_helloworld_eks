# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Observability Features (Educational)**
  - Added three-tier observability approach for learning Kubernetes monitoring
  - **Tier 1: Kubernetes Metrics (Resource Monitoring)**
    - Documented metrics-server addon usage (`kubectl top nodes/pods`)
    - Shows CPU and memory consumption for pods and nodes
    - Teaches Kubernetes-native resource monitoring
  - **Tier 2: Application Metrics (/metrics Endpoint)**
    - Added `/metrics` JSON endpoint to Flask app
    - Returns uptime_seconds, request_count, version, timestamp, status
    - Demonstrates application-level telemetry (educational alternative to Prometheus)
    - In-memory counters (resets on pod restart) suitable for learning scope
    - 12 comprehensive unit tests covering structure, data types, performance
  - **Tier 3: Structured Logging**
    - Implemented structured JSON logging for all endpoints (/, /health, /ready, /metrics)
    - Logs include timestamp (ISO 8601), event type, endpoint, method, remote_addr
    - Machine-readable format for parsing with jq and log aggregators
    - Fixed datetime.utcnow() deprecation (migrated to datetime.now(timezone.utc))
  - **Documentation**
    - Added comprehensive "Observability Features (Educational)" section to README.md
    - Includes usage examples for all three tiers with kubectl/curl commands
    - Complete observability workflow example (deploy → monitor → generate traffic → analyze)
    - Learning path from beginner (this project) to production (Prometheus/Grafana)
    - Added "Visual Alternative - Minikube Dashboard" subsection linking CLI commands to dashboard UI
    - Cross-linked observability features with Visual Exploration section
    - References docs/PRODUCTION_CONSIDERATIONS.md for advanced patterns
  - Demonstrates observability fundamentals without complexity of full monitoring stack
- **Visual Exploration Tools (Optional)**
  - Added "Visual Exploration (Optional)" section to main README.md
  - Documents Minikube dashboard for learning and troubleshooting
  - Includes alternative tools: k9s, Lens, kubectl plugins
  - Positioned as optional learning aid, not part of automation workflows
  - Emphasizes kubectl as primary tool (production practice)
  - Added brief mention in scripts/README.md for completeness
- **Production Considerations Documentation**
  - Created `docs/PRODUCTION_CONSIDERATIONS.md` - comprehensive guide for production patterns
    - Multi-environment configuration with Kustomize (why to use, when to skip)
    - Performance and load testing with k6/Locust (tools, examples, when needed)
    - Observability with Prometheus/Grafana (metrics, logs, traces, setup examples)
    - Chaos engineering and resilience testing with Chaos Mesh/Litmus (relates to manual crash recovery tests)
    - Additional production patterns (security, HA, deployment strategies)
    - Clear distinction between educational scope and production requirements
  - Referenced from main README.md and docs/README.md for discoverability
- **Docker Build Optimization**
  - Added `.dockerignore` file to `app/` directory
    - Excludes Python cache (`__pycache__/`), tests, development dependencies
    - Excludes documentation, IDE files, and version control data
    - Improves build speed, reduces image size, enhances security
    - Documented in `app/README.md` with rationale and excluded files list
- **Code Quality & Linting (Shift-Left Testing)**
  - Added Python linting with flake8
    - Created `.flake8` configuration file with educational rules
    - Added `make lint` target for local development
    - Integrated as Step 4 in CI/CD pipeline (early validation)
    - Added `flake8==6.1.0` to `app/requirements-dev.txt`
  - Added YAML validation with yamllint
    - Created `.yamllint` configuration file optimized for GitHub Actions
    - Configured for 160-char line length (practical for CI/CD workflows)
    - Updated `scripts/validate_workflow.sh` to use `.yamllint` config
  - Added comprehensive documentation
    - Created `docs/development/CODE_QUALITY.md` - Complete linting guide
    - Updated `README.md` with "Code Quality & Linting" section
    - Updated `docs/operations/CI_CD_GUIDE.md` with linting pipeline details
    - Updated `docs/development/README.md` index
  - Demonstrates shift-left testing pattern (catch errors early, save time)
- Test coverage metrics using `pytest-cov`
  - Added `.coveragerc` configuration file
  - Added `scripts/coverage_test.sh` for generating coverage reports
  - Added `make test-coverage*` targets (terminal, HTML, XML, all formats)
  - Added comprehensive coverage documentation (`docs/testing/COVERAGE_GUIDE.md`)
  - Added implementation details (`docs/testing/COVERAGE_IMPLEMENTATION.md`)
- Separated development dependencies from production dependencies
  - Created `app/requirements-dev.txt` for development/testing dependencies
  - Includes: pytest, pytest-cov, requests, yamllint, flake8
  - Production `app/requirements.txt` remains clean (Flask only)
- Documentation improvements
  - Created `app/README.md` explaining requirements files structure
  - Reorganized testing documentation into `docs/testing/` folder
  - Moved `TEST_COVERAGE_ANALYSIS.md` to `docs/testing/`
  - Moved `TESTING_IMPROVEMENTS_SUMMARY.md` to `docs/testing/`

### Changed
- **Code Refactoring: Reduced Duplication in app.py**
  - Created `log_event()` helper function to eliminate duplicated structured logging code
  - Consolidated 4 identical logging blocks into single reusable function with **kwargs
  - Function signature: `log_event(event, endpoint, **extra_fields)`
  - Reduces maintenance burden and improves code clarity
  - All 34 unit tests pass with zero changes required
  - Educational benefit: Demonstrates DRY (Don't Repeat Yourself) principle
- Enhanced CI/CD pipeline
  - Renumbered workflow steps after adding linting (Step 4)
  - Linting now runs before expensive build operations
  - Faster feedback on code quality issues (~10 minute savings on errors)
- Enhanced `make release-prep` workflow
  - Added test requirement coverage validation as Step 2/6
  - Now runs 6 steps: validate structure/workflow → verify test requirements → test-full → build → deploy → smoke
  - Updated release checklist to include requirement coverage validation
  - Ensures all documented tests are present before release
- Consolidated `CHANGELOG.md` and `CHANGELOG_DEV.md` into single unified changelog
  - Single file now serves both production releases and development tracking
  - Updated all documentation references
  - Updated Makefile targets to use consolidated file
- Updated GitHub Actions workflow to use `requirements-dev.txt`
- Updated all documentation to reference `requirements-dev.txt` for testing
- Updated documentation to reflect release-prep integration
  - Updated `README.md` with new release-prep description
  - Updated `scripts/README.md` with 6-step workflow and release-prep details
  - Updated `docs/testing/REQUIREMENT_COVERAGE.md` with release-prep reference
- Simplified developer setup to single command: `pip install -r app/requirements-dev.txt`

### Removed
- `CHANGELOG_DEV.md` (merged into `CHANGELOG.md`)
- Test dependencies from production `requirements.txt`

### Fixed
- **Documentation Corrections**
  - Fixed incorrect Makefile target in README.md observability example (line 508)
  - Changed `make deploy-local` to `make deploy` (correct target name)
  - The Makefile target is `deploy`, not `deploy-local` (which runs `scripts/deploy_local.sh`)
- **Test Fixture Dependencies**
  - Fixed `test_environment_variables_affect_app_response` in `test_k8s/test_app_config.py`
  - Added `service` and `ingress` fixtures to ensure backend pods are ready before testing
  - Prevents race condition where Ingress is configured but pods aren't ready yet
  - Test now properly skips (app doesn't have `/env` endpoint) instead of failing with 404/503 errors
  - Resolves `make full-deploy` smoke test failures

### Security

---

## Development Log

> **Purpose**: Track development changes, refactorings, and improvements not captured in production releases.  
> **Audience**: Developers working on this project.  
> **Format**: Manual entries for significant work; auto-generated entries archived below.

### Guidelines for Development Entries

**When to add manual entries**:
- Significant refactoring or architectural changes
- Breaking changes affecting developers
- New testing strategies or patterns
- Documentation consolidation efforts

**What to include**:
- Clear context and rationale
- Before/after comparisons
- Impact on workflows
- Related file changes

**Auto-generated entries**: Run `make changelog-dev` or `make changelog-dev-since TAG=v1.0.0` to append auto-generated changelog entries below.

---

## [Dev] 2025-11-22 - Test Coverage & Documentation Improvements

**Context**: Enhanced testing infrastructure with automated coverage metrics and improved dependency management following Python best practices.

**Changes**:

1. **Test Coverage Implementation**
   - Added `pytest-cov` for automated test coverage metrics
   - Created `.coveragerc` configuration (excludes tests, shows missing lines)
   - Implemented `scripts/coverage_test.sh` with 4 report formats:
     - Terminal: Quick console output with missing lines
     - HTML: Interactive report in `htmlcov/index.html`
     - XML: CI/CD compatible format
     - All: Generate all formats simultaneously
   - Added Makefile targets: `test-coverage`, `test-coverage-html`, `test-coverage-xml`, `test-coverage-all`
   - Current coverage: **100%** (22/22 statements in app.py)

2. **Requirements Separation** (Production vs Development)
   - **Before**: Single `requirements.txt` with mixed dependencies
   - **After**: Clean separation
     - `app/requirements.txt` - Production only (Flask 2.3.2)
     - `app/requirements-dev.txt` - Development/testing (inherits production + adds pytest, pytest-cov, requests, yamllint)
   - **Benefits**:
     - Smaller Docker images (no test dependencies)
     - Faster deployments
     - Better security (reduced attack surface)
     - Single command setup: `pip install -r app/requirements-dev.txt`

3. **Changelog Consolidation**
   - Merged `CHANGELOG.md` and `CHANGELOG_DEV.md` into unified changelog
   - Single file now has:
     - Top: Production releases ([Unreleased], version sections)
     - Middle: Development Log with guidelines
     - Bottom: Templates for both types of entries
   - Updated Makefile `changelog-dev*` targets to append to unified file
   - Updated all documentation references

4. **Documentation Reorganization**
   - Moved testing docs from root to `docs/testing/`:
     - `TEST_COVERAGE_ANALYSIS.md` → `docs/testing/TEST_COVERAGE_ANALYSIS.md`
     - `TESTING_IMPROVEMENTS_SUMMARY.md` → `docs/testing/TESTING_IMPROVEMENTS_SUMMARY.md`
     - Added: `docs/testing/COVERAGE_GUIDE.md` (comprehensive guide)
     - Added: `docs/testing/COVERAGE_IMPLEMENTATION.md` (implementation details)
   - Created `app/README.md` documenting requirements files
   - Updated all internal cross-references
   - Root directory now clean (only CHANGELOG.md and README.md)

5. **CI/CD & Workflow Updates**
   - Updated `.github/workflows/ci-cd.yml` to use `requirements-dev.txt`
   - Updated `docs/development/DEVELOPMENT_WORKFLOW.md`
   - Updated `docs/operations/CI_CD_GUIDE.md`
   - Simplified all setup instructions to single pip install

**Impact on Workflows**:
- **Developers**: Easier setup (`pip install -r app/requirements-dev.txt` installs everything)
- **CI/CD**: Clearer separation between build and test stages
- **Production**: Leaner Docker images, faster deployments
- **Testing**: Easy access to coverage metrics (`make test-coverage-html`)

**Related Files**:
- New: `.coveragerc`, `app/requirements-dev.txt`, `scripts/coverage_test.sh`
- New: `docs/testing/COVERAGE_GUIDE.md`, `docs/testing/COVERAGE_IMPLEMENTATION.md`, `app/README.md`
- Moved: `TEST_COVERAGE_ANALYSIS.md`, `TESTING_IMPROVEMENTS_SUMMARY.md`
- Modified: `CHANGELOG.md`, `Makefile`, `.gitignore`, `pytest.ini`, `app/requirements.txt`
- Modified: `README.md`, `.github/workflows/ci-cd.yml`, various docs
- Deleted: `CHANGELOG_DEV.md`

**Verification**:
```bash
# Install and verify
pip install -r app/requirements-dev.txt
make test-coverage-html
# Result: ✅ 100% coverage, all 22 tests passed
```

---

## Templates

### Production Release Template

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security updates
```

### Development Entry Template

```markdown
## [Dev] YYYY-MM-DD - Description

**Context**: Why this change was needed

**Changes**:
- List of specific changes
- Impact on workflows

**Related Files**:
- `path/to/file1.md`
- `path/to/file2.py`
```
