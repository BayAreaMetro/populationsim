#!/usr/bin/env python3
"""
run_validation_test.py

Standalone script to run the output structure validation test.
This can be called from batch files or run independently.

Usage:
    python run_validation_test.py [--verbose] [--output-dir <path>]
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project directory to sys.path for imports
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def main():
    """Main function to run the validation test."""

    
    try:
        from test_output_structure import OutputStructureTest
        
        # Create and run the test
        test_runner = OutputStructureTest(verbose=True)
        test_results = test_runner.run_all_tests(output_dir='output_2023')
        
        # Print summary if not in quiet mode

        if test_results['success']:
                print(f"✓ VALIDATION PASSED: All {test_results['tests_run']} tests completed successfully")
        else:
                print(f"✗ VALIDATION FAILED: {test_results['failures']} out of {test_results['tests_run']} tests failed")
                print("\nFailure details:")
                for failure in test_results['failure_details']:
                    print(f"  - {failure}")
        
        # Exit with appropriate code
        return 0 if test_results['success'] else 1
        
    except ImportError as e:
            print(f"ERROR: Could not import test_output_structure: {e}")
            return 2
    except Exception as e:
            print(f"ERROR: Unexpected error running validation test: {e}")
            return 3

if __name__ == '__main__':
    sys.exit(main())
