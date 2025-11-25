# Code Quality & Linting

This document describes the code quality tools and practices used in this project.

---

## Overview

This project implements **shift-left testing** by integrating linting early in the development workflow. Code quality checks run before expensive build and test operations, providing faster feedback and catching errors early.

```
Traditional Pipeline:
Code → Build → Test → [ERROR FOUND HERE] 💥 (Late, expensive)

Shift-Left Pipeline:
Code → Lint → [ERROR FOUND HERE] ✅ → Build → Test (Early, fast)
         ↑
    Faster feedback!
```

---

## Python Linting (flake8)

### Quick Start

```bash
# Run linting locally before committing
make lint
```

### What It Checks

- **Syntax errors**: Missing colons, unclosed brackets, invalid Python syntax
- **Undefined variables**: References to variables that don't exist
- **Unused imports**: Imported modules that are never used (cleanup opportunity)
- **Unused variables**: Variables assigned but never referenced
- **Function complexity**: Functions that are too complex (cyclomatic complexity > 10)
- **PEP 8 compliance**: Basic Python style guide violations
- **Code smells**: f-strings without placeholders, redefined functions, etc.

### Configuration

Linting rules are defined in `.flake8`:

```ini
[flake8]
max-line-length = 100        # Reasonable for modern displays
max-complexity = 10          # Keeps functions manageable
exclude = .git,__pycache__,venv,.pytest_cache,htmlcov
ignore = E501,W503,W504,W293,W291,W391,W292  # Minor style issues
select = E,F,W               # Errors, PyFlakes, Warnings
show-source = True           # Educational - shows the problematic code
statistics = True            # Summary at the end
count = True                 # Count total errors
```

### Example Output

```
test_k8s/utils.py:11:1: F401 'typing.Tuple' imported but unused
app/app.py:145:1: F811 redefinition of unused 'get_status' from line 12
test_k8s/conftest.py:22:5: F841 local variable 'result' is assigned to but never used
```

### Integration Points

1. **Local Development**: Run `make lint` before committing
2. **Git Hooks** (optional): Can be added to pre-commit hooks
3. **CI/CD Pipeline**: Runs as Step 4 in `.github/workflows/ci-cd.yml`
4. **IDE Integration**: Most Python IDEs support flake8 natively

---

## YAML Validation (yamllint)

### Quick Start

```bash
# Validate workflow YAML
make validate-workflow

# Or validate specific YAML files
yamllint .github/workflows/ci-cd.yml
yamllint k8s/*.yaml
```

### What It Checks

- **YAML syntax**: Valid YAML structure
- **Line length**: Reasonable line limits (160 chars for GitHub Actions)
- **Indentation**: Consistent 2-space indentation
- **Trailing spaces**: Clean formatting
- **Document structure**: Proper YAML conventions

### Configuration

YAML linting rules are defined in `.yamllint`:

```yaml
---
extends: default

rules:
  line-length:
    max: 160                              # GitHub Actions needs longer lines
    level: warning
  
  document-start:
    present: false                        # Don't require --- in workflows
  
  truthy:
    allowed-values: ['true', 'false', 'on', 'off']
    check-keys: false                     # Allow 'on:' in workflow triggers
```

### Why This Matters for CI/CD

GitHub Actions workflows often have:
- Long conditional expressions
- Multi-line shell commands
- Complex Boolean logic

The configuration balances strict YAML standards with practical CI/CD needs.

---

## Shift-Left Testing in CI/CD

### Pipeline Order

```yaml
jobs:
  build-and-test:
    steps:
      - Checkout repository          # Step 1
      - Setup Python                 # Step 2
      - Install dependencies         # Step 3
      - Run Python linting ⚡        # Step 4 ← SHIFT-LEFT!
      - Validate repo structure      # Step 5
      - Validate workflow YAML       # Step 6
      - Setup Docker & Minikube      # Step 7 (expensive)
      - Build Docker image           # Step 8 (expensive)
      - Deploy to Kubernetes         # Step 9 (expensive)
      - Run unit tests               # Step 10
      - Run integration tests        # Step 11
      ...
```

**Benefits:**
- ✅ Fails fast on syntax errors (saves 10-15 minutes of build time)
- ✅ Provides immediate feedback to developers
- ✅ Prevents broken code from reaching expensive pipeline stages
- ✅ Reduces CI/CD costs by avoiding unnecessary builds

### Example: Time Saved

| Scenario | Without Linting | With Linting (Shift-Left) |
|----------|----------------|---------------------------|
| Syntax error in Python | Fails at Step 10 (~12 min) | Fails at Step 4 (~2 min) |
| Unused import | Never caught | Caught at Step 4 (~2 min) |
| YAML syntax error | Fails at runtime (~15 min) | Fails at Step 6 (~3 min) |

---

## Best Practices

### Before Committing

```bash
# Run linting locally
make lint

# Fix any errors before pushing
# Linting will run again in CI/CD
```

### Handling Linting Errors

1. **Fix the error** (preferred):
   ```bash
   # Remove unused import
   # Fix syntax error
   # Simplify complex function
   ```

2. **Disable specific check** (use sparingly):
   ```python
   # noqa: F401 - Intentionally imported for re-export
   from .utils import KubectlError
   ```

3. **Update configuration** (for project-wide exceptions):
   ```ini
   # .flake8
   ignore = E501,F401
   ```

### Educational Value

The current configuration intentionally finds **real issues**:
- Unused imports (cleanup opportunities)
- f-strings without placeholders (should be regular strings)
- Function redefinitions (actual bugs!)
- Code complexity (maintainability concerns)

These are perfect examples for learning what linting catches and why it matters.

---

## Tools Reference

| Tool | Purpose | Config File | Command |
|------|---------|-------------|---------|
| **flake8** | Python linting | `.flake8` | `make lint` |
| **yamllint** | YAML validation | `.yamllint` | `yamllint <file>` |
| **pytest** | Python testing | `pytest.ini` | `pytest` |

---

## Further Reading

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [yamllint Documentation](https://yamllint.readthedocs.io/)
- [Shift-Left Testing](https://en.wikipedia.org/wiki/Shift-left_testing)

---

## Related Documentation

- [Development Workflow](DEVELOPMENT_WORKFLOW.md) - Git workflow and branching
- [Testing Documentation](../testing/README.md) - Test organization and practices
- [CI/CD Guide](../operations/CI_CD_GUIDE.md) - Pipeline details

---

[← Back to Development Documentation](README.md)
