#!/usr/bin/env python3
"""
Test Coverage Validator

Validates that all documented test requirements are actually implemented.
This goes beyond code coverage to ensure requirement coverage.

Usage:
    python scripts/validate_test_coverage.py
    python scripts/validate_test_coverage.py --verbose
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Expected test inventory based on TEST_COVERAGE_ANALYSIS.md
EXPECTED_TESTS = {
    "root_endpoint": {
        "count": 4,
        "tests": [
            "test_home_returns_200_ok",
            "test_home_response_content",
            "test_response_latency",
            "test_invalid_route_returns_404",
        ],
        "description": "Root endpoint (/) tests"
    },
    "health_endpoint": {
        "count": 9,
        "tests": [
            "test_health_endpoint_returns_200",
            "test_health_endpoint_content",
            "test_health_endpoint_performance",
            "test_health_endpoint_cache_control",
            "test_health_endpoint_headers",
            "test_health_endpoint_http_methods",
            "test_health_endpoint_consistency",
            "test_health_endpoint_no_side_effects",
            "test_health_vs_root_endpoint_independence",
        ],
        "description": "Health endpoint (/health) tests - liveness probe"
    },
    "ready_endpoint": {
        "count": 9,
        "tests": [
            "test_ready_endpoint_returns_200",
            "test_ready_endpoint_content",
            "test_ready_endpoint_performance",
            "test_ready_endpoint_cache_control",
            "test_ready_endpoint_cache_control_detailed",
            "test_ready_endpoint_http_methods",
            "test_ready_endpoint_consistency",
            "test_ready_endpoint_no_side_effects",
            "test_ready_vs_health_independence",
        ],
        "description": "Ready endpoint (/ready) tests - readiness probe"
    }
}

TOTAL_EXPECTED = sum(category["count"] for category in EXPECTED_TESTS.values())


def find_implemented_tests() -> List[str]:
    """Extract test names from test_app.py"""
    test_file = Path("app/tests/test_app.py")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    implemented = []
    content = test_file.read_text()
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('def test_'):
            # Extract test name
            test_name = line.split('(')[0].replace('def ', '')
            implemented.append(test_name)
    
    return implemented


def validate_coverage(verbose: bool = False) -> Tuple[bool, Dict]:
    """
    Validate that all expected tests are implemented.
    
    Returns:
        (is_valid, report_dict)
    """
    print("=" * 70)
    print("TEST REQUIREMENT COVERAGE VALIDATION")
    print("=" * 70)
    print()
    
    implemented = find_implemented_tests()
    
    # Track results
    missing_tests = []
    extra_tests = []
    categories_status = {}
    
    # Check each category
    for category_name, category_data in EXPECTED_TESTS.items():
        expected_tests = set(category_data["tests"])
        implemented_in_category = set(test for test in implemented if test in expected_tests)
        missing_in_category = expected_tests - implemented_in_category
        
        categories_status[category_name] = {
            "expected": len(expected_tests),
            "implemented": len(implemented_in_category),
            "missing": list(missing_in_category),
            "description": category_data["description"]
        }
        
        missing_tests.extend(missing_in_category)
    
    # Check for extra tests not in our documented requirements
    all_expected = set()
    for category_data in EXPECTED_TESTS.values():
        all_expected.update(category_data["tests"])
    
    extra_tests = [test for test in implemented if test not in all_expected]
    
    # Print results
    print("📊 Test Inventory:")
    print(f"   Expected:     {TOTAL_EXPECTED} tests")
    print(f"   Implemented:  {len(implemented)} tests")
    print(f"   Missing:      {len(missing_tests)} tests")
    print(f"   Undocumented: {len(extra_tests)} tests")
    print()
    
    # Category breakdown
    all_good = True
    for category_name, status in categories_status.items():
        symbol = "✅" if status["implemented"] == status["expected"] else "❌"
        print(f"{symbol} {status['description']}")
        print(f"   Expected: {status['expected']}, Implemented: {status['implemented']}")
        
        if status["missing"]:
            all_good = False
            print("   ⚠️  Missing tests:")
            for test in status["missing"]:
                print(f"      - {test}")
        
        if verbose and status["implemented"] == status["expected"]:
            # Show all tests in category
            category_tests = EXPECTED_TESTS[category_name]["tests"]
            for test in category_tests:
                print(f"      ✓ {test}")
        
        print()
    
    # Show extra tests
    if extra_tests:
        all_good = False
        print("⚠️  Undocumented tests (not in TEST_COVERAGE_ANALYSIS.md):")
        for test in extra_tests:
            print(f"   - {test}")
        print()
        print("   Action: Add these to TEST_COVERAGE_ANALYSIS.md or remove if unnecessary")
        print()
    
    # Final verdict
    print("=" * 70)
    if all_good and len(implemented) == TOTAL_EXPECTED:
        print("✅ PASS: All documented test requirements are implemented!")
        print(f"   {len(implemented)}/{TOTAL_EXPECTED} tests present and accounted for")
        coverage_pct = 100.0
    else:
        print("❌ FAIL: Test requirement coverage incomplete")
        coverage_pct = (len(implemented) - len(extra_tests)) / TOTAL_EXPECTED * 100
        print(f"   Requirement Coverage: {coverage_pct:.1f}%")
        
        if missing_tests:
            print(f"   Missing {len(missing_tests)} required test(s)")
        if extra_tests:
            print(f"   Found {len(extra_tests)} undocumented test(s)")
    
    print("=" * 70)
    print()
    
    # Return structured report
    report = {
        "valid": all_good and len(implemented) == TOTAL_EXPECTED,
        "requirement_coverage_pct": coverage_pct,
        "expected_count": TOTAL_EXPECTED,
        "implemented_count": len(implemented),
        "missing_count": len(missing_tests),
        "extra_count": len(extra_tests),
        "missing_tests": missing_tests,
        "extra_tests": extra_tests,
        "categories": categories_status
    }
    
    return (report["valid"], report)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate test requirement coverage")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show detailed test listing")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    
    args = parser.parse_args()
    
    is_valid, report = validate_coverage(verbose=args.verbose)
    
    if args.json:
        print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
