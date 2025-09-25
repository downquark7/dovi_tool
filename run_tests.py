#!/usr/bin/env python3
"""
Test runner for HDR10+ Generator

This script runs the complete test suite and provides detailed reporting.
"""

import sys
import os
import subprocess
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"✓ {description} completed successfully")
        print(f"  Duration: {end_time - start_time:.2f} seconds")
        
        if result.stdout:
            print("\nOutput:")
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        
        print(f"✗ {description} failed")
        print(f"  Duration: {end_time - start_time:.2f} seconds")
        print(f"  Return code: {e.returncode}")
        
        if e.stdout:
            print("\nOutput:")
            print(e.stdout)
        
        if e.stderr:
            print("\nError output:")
            print(e.stderr)
        
        return False


def main():
    """Main test runner function"""
    
    print("HDR10+ Generator Test Suite")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Test commands
    test_commands = [
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_rpu_parser.py", "-v"], 
         "RPU Parser Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_hdr10plus_generator.py", "-v"], 
         "HDR10+ Generator Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_validator.py", "-v"], 
         "Validator Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_integration.py", "-v"], 
         "Integration Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_golden_files.py", "-v"], 
         "Golden File Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/test_stress.py", "-v"], 
         "Stress Tests"),
        
        (["python", "-m", "pytest", "hdr10plus_gen/tests/", "-v", "--cov=hdr10plus_gen", 
          "--cov-report=term-missing", "--cov-report=html:htmlcov"], 
         "Complete Test Suite with Coverage"),
    ]
    
    # Run tests
    results = []
    total_start_time = time.time()
    
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
    
    total_end_time = time.time()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {description}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    print(f"Total time: {total_end_time - total_start_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())