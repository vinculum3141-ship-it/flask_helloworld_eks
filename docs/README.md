# Documentation Index

This directory contains comprehensive documentation for the Flask Hello World Mini Project.

## 📁 Directory Structure

```
docs/
├── README.md (this file)              # Documentation index
├── operations/                        # Kubernetes operations & deployment
│   ├── README.md                      # Operations documentation index
│   ├── CI_CD_GUIDE.md                # CI/CD pipeline reference
│   ├── probes/
│   │   └── PROBES_GUIDE.md           # Liveness/readiness probes
│   └── ingress/
│       └── INGRESS_GUIDE.md          # Complete Ingress guide
├── testing/                           # Test suite documentation
│   ├── README.md                      # Testing documentation index
│   ├── architecture/                  # Test suite architecture
│   │   ├── TEST_ARCHITECTURE.md
│   │   └── TEST_REFACTORING.md
│   ├── integration/                   # Integration tests
│   │   ├── SCRIPT_INTEGRATION.md
│   │   └── educational/               # Educational test guides
│   │       ├── EDUCATIONAL_TESTS_GUIDE.md
│   │       └── EDUCATIONAL_TESTS_QUICKREF.md
│   └── health-endpoint/               # Health endpoint tests
│       ├── README.md
│       ├── HEALTH_ENDPOINT_TESTING_GUIDE.md
│       └── HEALTH_TEST_COVERAGE_EVALUATION.md
└── development/                       # Development processes
    ├── DEVELOPMENT_WORKFLOW.md
    └── CHANGELOG_GUIDE.md
```

## 📚 Documentation Categories

### Operations & Deployment
**Location:** `docs/operations/`

Comprehensive guides for Kubernetes operations, CI/CD, and troubleshooting.

- **[operations/](operations/README.md)** - Operations documentation index
- **[operations/CI_CD_GUIDE.md](operations/CI_CD_GUIDE.md)** - Complete CI/CD pipeline reference
  - Workflow triggers and stages
  - Features checklist and capabilities
  - GitHub CLI usage and examples
  - Manual testing and validation
  - Troubleshooting guide

- **[operations/probes/PROBES_GUIDE.md](operations/probes/PROBES_GUIDE.md)** - Kubernetes probes guide
  - Liveness and readiness probe concepts
  - Configuration reference with all parameters
  - Visual timelines and examples
  - Self-healing behavior demonstrations
  - Testing and verification commands
  - Troubleshooting common issues
  - Best practices for probe configuration

- **[operations/ingress/](operations/ingress/)** - Ingress troubleshooting guides
  - **[INGRESS_GUIDE.md](operations/ingress/INGRESS_GUIDE.md)** - Complete Ingress guide: understanding, troubleshooting, and CI/CD

### Testing Documentation
**Location:** `docs/testing/`

All testing documentation including workflows, architecture, integration tests, and health endpoint testing.

- **[testing/](testing/README.md)** - Testing documentation index
- **[testing/TESTING_WORKFLOWS.md](testing/TESTING_WORKFLOWS.md)** - 🔄 **Complete testing workflows and command sequences**
  - Standard development workflow
  - Test sequences (fast, comprehensive, health endpoint)
  - Full manual testing with step-by-step commands
  - Make targets reference
  - Common scenarios and use cases

- **[testing/architecture/](testing/architecture/)** - Test suite architecture
  - **[TEST_ARCHITECTURE.md](testing/architecture/TEST_ARCHITECTURE.md)** - Complete test suite architecture
  - **[TEST_REFACTORING.md](testing/architecture/TEST_REFACTORING.md)** - Refactoring summary and best practices

- **[testing/integration/](testing/integration/)** - Integration tests
  - **[SCRIPT_INTEGRATION.md](testing/integration/SCRIPT_INTEGRATION.md)** - Script integration with pytest markers
  - **[educational/](testing/integration/educational/)** - Educational Ingress tests
    - **[EDUCATIONAL_TESTS_GUIDE.md](testing/integration/educational/EDUCATIONAL_TESTS_GUIDE.md)** - Complete guide to educational tests
    - **[EDUCATIONAL_TESTS_QUICKREF.md](testing/integration/educational/EDUCATIONAL_TESTS_QUICKREF.md)** - Quick reference

- **[testing/health-endpoint/](testing/health-endpoint/)** - Health endpoint tests
  - **[README.md](testing/health-endpoint/README.md)** - Navigation and quick start
  - **[HEALTH_ENDPOINT_TESTING_GUIDE.md](testing/health-endpoint/HEALTH_ENDPOINT_TESTING_GUIDE.md)** - Complete testing guide
  - **[HEALTH_TEST_COVERAGE_EVALUATION.md](testing/health-endpoint/HEALTH_TEST_COVERAGE_EVALUATION.md)** - Detailed test analysis

### Development Processes
**Location:** `docs/development/`

Development workflow, changelog management, and contribution guidelines.

- **[development/](development/README.md)** - Development documentation index
- **[development/DEVELOPMENT_WORKFLOW.md](development/DEVELOPMENT_WORKFLOW.md)** - Development workflow and best practices
  - Git workflow
  - Pre-push validation scripts
  - Code review process
  - Testing requirements

- **[development/CHANGELOG_GUIDE.md](development/CHANGELOG_GUIDE.md)** - Changelog maintenance guide
  - Manual changelog (recommended for releases)
  - Auto-generated changelog
  - Commit message conventions

## 🔍 Quick Links

### Getting Started
- [Main README](../README.md) - Project overview and setup
- [Test README](../test_k8s/README.md) - Test usage guide

### For Developers
- [Development Workflow](development/DEVELOPMENT_WORKFLOW.md) - Pre-push validation and best practices
- [Test Architecture](testing/architecture/TEST_ARCHITECTURE.md) - Understand the test suite
- [Test Refactoring](testing/architecture/TEST_REFACTORING.md) - Recent improvements
- [Health Endpoint Testing](testing/health-endpoint/HEALTH_ENDPOINT_TESTING_GUIDE.md) - Health endpoint tests
- [Educational Tests](testing/integration/educational/EDUCATIONAL_TESTS_GUIDE.md) - Learn Ingress concepts through testing

### For Operations
- [CI/CD Guide](operations/CI_CD_GUIDE.md) - Complete pipeline reference
- [Probes Guide](operations/probes/PROBES_GUIDE.md) - Health monitoring and self-healing
- [Ingress Guide](operations/ingress/INGRESS_GUIDE.md) - Complete Ingress troubleshooting and CI/CD guide
- [Scripts Guide](../scripts/README.md) - Automation scripts including service access

## 📝 Contributing

When adding new documentation:
- **Operations docs** go in `docs/operations/` (CI/CD, K8s, troubleshooting)
- **Testing docs** go in `docs/testing/` (architecture, test guides, coverage)
- **Development docs** go in `docs/development/` (workflow, changelog, processes)
- **Usage guides** stay with the code (e.g., `test_k8s/README.md` for test usage)
- **Update this index file** when adding new documentation
- **Follow Markdown best practices** (clear headings, code blocks, links)

### Documentation Organization Principles

- ✅ **Separation of Concerns**: Group related documentation by category (ops, testing, dev)
- ✅ **Clear Hierarchy**: Use subdirectories for related content (probes/, ingress/, educational/)
- ✅ **Discoverability**: Maintain README.md in each directory for navigation
- ✅ **Keep Usage with Code**: User-facing guides stay near the code they document
- ✅ **Centralize Architecture**: Design and architecture docs belong in `docs/`
