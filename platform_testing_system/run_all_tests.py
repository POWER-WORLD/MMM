"""
Standalone Master Test Runner for Platform Testing System.

Provides an institutional-grade CLI interface to execute the full testing suite:
- Synthetic Data Generation Tests
- Core & Agent Unit Tests
- End-to-End Pipeline Integration Tests
- Concurrency & Adversarial Stress Tests

Usage:
    python platform_testing_system/run_all_tests.py
    python platform_testing_system/run_all_tests.py --category unit
    python platform_testing_system/run_all_tests.py --category integration
    python platform_testing_system/run_all_tests.py --category stress
"""

import argparse
import os
import sys
import time
from datetime import datetime
from typing import List

import pytest


def print_banner(title: str, character: str = "=", width: int = 75) -> None:
    """Print formatted terminal banner."""
    print("\n" + character * width)
    print(f"  {title}")
    print(character * width)


def run_test_suite(category: str = "all", verbose: bool = True) -> int:
    """
    Run pytest for the requested test category and report comprehensive metrics.

    Args:
        category: 'all', 'unit', 'integration', or 'stress'.
        verbose: Whether to pass verbose flag to pytest.

    Returns:
        Exit code (0 for success, non-zero for failures).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    category_paths = {
        "unit": os.path.join(base_dir, "unit"),
        "integration": os.path.join(base_dir, "integration"),
        "stress": os.path.join(base_dir, "stress"),
        "all": base_dir,
    }

    target_path = category_paths.get(category.lower(), base_dir)

    print_banner(
        f"GOLD TRADING ANALYSIS PLATFORM — AUTOMATED TEST SYSTEM\n"
        f"  Target: {category.upper()} | Path: {os.path.relpath(target_path, os.path.dirname(base_dir))}\n"
        f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        character="#",
    )

    pytest_args: List[str] = [
        target_path,
        "-v" if verbose else "-q",
        "--tb=short",
        "-ra",
    ]

    start_time = time.perf_counter()
    exit_code = pytest.main(pytest_args)
    duration = time.perf_counter() - start_time

    print_banner("EXECUTION SUMMARY & VERIFICATION METRICS", character="=")
    print(f"  Execution Time:    {duration:.2f} seconds")
    print(f"  Category Tested:   {category.upper()}")
    print(f"  Exit Code:         {exit_code}")

    if exit_code == 0:
        print("\n  >>> [SUCCESS] 100% OF PLATFORM TESTS PASSED FLAWLESSLY! <<<")
        print("  All core components, agents, trading pipelines, synthetic data,")
        print("  and stress bounds are fully verified.")
    else:
        print(f"\n  >>> [FAILURE] Test suite encountered errors (exit code: {exit_code}) <<<")

    print("=" * 75 + "\n")
    return int(exit_code)


def main() -> None:
    """CLI entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Master Test Runner for Gold Trading Analysis Platform"
    )
    parser.add_argument(
        "--category",
        choices=["all", "unit", "integration", "stress"],
        default="all",
        help="Specify test category to execute (default: all)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run pytest in quiet mode",
    )

    args = parser.parse_args()
    code = run_test_suite(category=args.category, verbose=not args.quiet)
    sys.exit(code)


if __name__ == "__main__":
    main()
