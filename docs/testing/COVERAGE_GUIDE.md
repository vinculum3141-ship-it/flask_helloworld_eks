# Test Coverage Guide

## Overview

This project includes **dual coverage validation**:

1. **Code Coverage** (`pytest-cov`) - Measures which code lines are executed
2. **Requirement Coverage** (`validate_test_coverage.py`) - Validates all documented tests are implemented

> **Important:** Code coverage showing 100% doesn't guarantee all required tests exist. Use both metrics for complete quality assurance.
>
> **See:** [REQUIREMENT_COVERAGE.md](REQUIREMENT_COVERAGE.md) for requirement coverage validation.

## Code Coverage (pytest-cov)

Shows which parts of your code are tested and which lines are missing test coverage.

## Quick Start

### Install Dependencies

First, install the updated requirements including coverage tools:

```bash
pip install -r app/requirements-dev.txt
```

**Note:** This installs both production dependencies (`requirements.txt`) and development/testing tools (`pytest`, `pytest-cov`).

### Run Tests with Coverage

**Option 1: Using Make targets (Recommended)**

```bash
# Terminal report (default - shows coverage % and missing lines)
make test-coverage

# HTML report (opens in browser for detailed visualization)
make test-coverage-html

# XML report (for CI/CD integration)
make test-coverage-xml

# All formats at once
make test-coverage-all
```

**Option 2: Using the script directly**

```bash
# Terminal report
bash scripts/coverage_test.sh terminal

# HTML report
bash scripts/coverage_test.sh html

# XML report
bash scripts/coverage_test.sh xml

# All reports
bash scripts/coverage_test.sh all
```

**Option 3: Using pytest directly**

```bash
# Terminal report with missing lines
pytest app/tests/ --cov=app --cov-report=term-missing

# HTML report
pytest app/tests/ --cov=app --cov-report=html

# Multiple reports
pytest app/tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

## Coverage Report Types

### 1. Terminal Report (`term-missing`)

Shows coverage percentage and lists missing line numbers directly in your terminal.

**Example output:**
```
---------- coverage: platform linux, python 3.x -----------
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
app/__init__.py       5      0   100%
app/app.py           15      0   100%
-----------------------------------------------
TOTAL                20      0   100%
```

**When to use:** Quick checks during development

### 2. HTML Report

Generates an interactive HTML report with:
- Color-coded coverage visualization
- Line-by-line coverage highlighting
- Branch coverage details
- Easy navigation between files

**Location:** `htmlcov/index.html`

**When to use:** 
- Detailed coverage analysis
- Finding specific uncovered code
- Team reviews
- Documentation

**How to view:**
```bash
make test-coverage-html
# Then open htmlcov/index.html in your browser
```

### 3. XML Report

Machine-readable format for CI/CD pipelines and coverage tools.

**Location:** `coverage.xml`

**When to use:**
- CI/CD integration
- Code quality dashboards
- Automated coverage gates

## Configuration

### `.coveragerc` - Coverage Configuration

Located at project root, controls:
- What to measure (`source = app`)
- What to exclude (`omit = */tests/*`)
- Report format settings
- Coverage rules

**Key settings:**
```ini
[run]
source = app              # Measure coverage for app/ directory
omit = */tests/*         # Don't measure test files themselves

[report]
show_missing = True      # Show line numbers of missing coverage
precision = 2            # Show coverage to 2 decimal places
```

### `pytest.ini` - Test Configuration

Contains pytest settings and markers. Coverage can be run via:
```bash
pytest --cov=app --cov-report=html
```

## Understanding Coverage Metrics

### Coverage Percentage

- **100%** - All code lines are executed during tests ✅
- **90-99%** - Excellent coverage, minor gaps
- **80-89%** - Good coverage, some areas untested
- **<80%** - Consider adding more tests

### Statement Coverage vs Branch Coverage

- **Statement coverage** - Are all lines executed?
- **Branch coverage** - Are all if/else paths tested?

Example:
```python
if condition:
    do_something()  # Branch 1
else:
    do_other()      # Branch 2
```

Both branches should be tested for complete coverage.

## Best Practices

### 1. Target 100% Coverage for Critical Code

- Core business logic
- API endpoints
- Error handlers
- Security functions

### 2. Exclude Appropriate Code

Already configured in `.coveragerc`:
- Test files themselves
- Configuration files
- `if __name__ == "__main__"` blocks

### 3. Review Missing Coverage

```bash
# See exactly which lines are missing
make test-coverage

# Or use HTML for visual review
make test-coverage-html
```

### 4. Use in CI/CD

```yaml
# Example GitHub Actions step
- name: Run tests with coverage
  run: |
    pip install -r app/requirements-dev.txt
    make test-coverage-xml
    
- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Current Project Coverage

Based on `docs/testing/TEST_COVERAGE_ANALYSIS.md`, this project has:

- ✅ **100% Flask endpoint coverage** (22 unit tests)
- ✅ **100% Kubernetes resource coverage** (20 integration tests)
- ✅ **Complete test documentation**

Running coverage will confirm:
```bash
make test-coverage
```

Expected result:
```
TOTAL     100%
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make test-coverage` | Terminal coverage report with missing lines |
| `make test-coverage-html` | Generate HTML report in `htmlcov/` |
| `make test-coverage-xml` | Generate XML report for CI/CD |
| `make test-coverage-all` | Generate all report formats |

## Files Created/Modified

### New Files
- `.coveragerc` - Coverage configuration
- `scripts/coverage_test.sh` - Coverage test runner
- `docs/testing/COVERAGE_GUIDE.md` - This guide

### Modified Files
- `app/requirements.txt` - Added `pytest-cov`
- `pytest.ini` - Added coverage notes
- `Makefile` - Added coverage targets
- `.gitignore` - Ignore coverage artifacts

## Troubleshooting

### Coverage shows 0% or unexpected results

1. Check that you're measuring the right source:
   ```bash
   pytest --cov=app  # Not --cov=.
   ```

2. Verify `.coveragerc` source setting:
   ```ini
   [run]
   source = app
   ```

### HTML report not generating

1. Ensure pytest-cov is installed:
   ```bash
   pip install pytest-cov
   ```

2. Check for errors in the output

### Missing lines shown but tests exist

- May indicate unreachable code
- Check for defensive programming (exception handlers never triggered)
- Consider if the code path is actually testable

## Complete Coverage Validation

### Beyond Code Coverage

⚠️ **Important Limitation:** Code coverage at 100% doesn't guarantee all documented tests are implemented!

**Example Problem:**
- Your test plan documents 22 specific tests
- Someone deletes 2 tests
- Remaining 20 tests still execute all code lines
- Result: Code coverage still shows 100% ✅
- Reality: You're missing 2 documented tests ❌

### Solution: Dual Coverage Validation

Use both metrics for complete quality assurance:

```bash
# 1. Code Coverage (line execution)
make test-coverage-html

# 2. Requirement Coverage (test inventory)
make validate-test-requirements
```

**Requirement Coverage Output:**
```
📊 Test Inventory:
   Expected:     22 tests
   Implemented:  22 tests
   Missing:      0 tests
   Undocumented: 0 tests

✅ PASS: All documented test requirements are implemented!
```

### Comprehensive Validation

| Metric | Tool | Measures | Catches |
|--------|------|----------|---------|
| **Code Coverage** | pytest-cov | Line execution | Untested code |
| **Requirement Coverage** | validate_test_coverage.py | Test inventory | Missing tests |

**See:** [REQUIREMENT_COVERAGE.md](REQUIREMENT_COVERAGE.md) for complete documentation.

## Resources

- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Requirement Coverage Guide](REQUIREMENT_COVERAGE.md) - Test inventory validation
- [Keep a Changelog - Testing](https://keepachangelog.com/)

## Next Steps

1. **Run your first coverage report:**
   ```bash
   make test-coverage-html
   ```

2. **Review the HTML report** - Open `htmlcov/index.html`

3. **Check current coverage** - Should be 100% for this project

4. **Validate requirement coverage:**
   ```bash
   make validate-test-requirements
   ```

5. **Integrate into workflow** - Add both to CI/CD pipeline

5. **Set coverage gates** - Fail builds if coverage drops below threshold
