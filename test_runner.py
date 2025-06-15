#!/usr/bin/env python3
"""
Test runner script for heic2jpg
Provides an easy way to run tests on Windows without Make
"""

import sys
import subprocess
import argparse

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test runner for heic2jpg')
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'coverage'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ['python', '-m', 'pytest']
    
    if args.verbose:
        base_cmd.append('-v')
    
    success = True
    
    if args.type == 'all':
        success &= run_command(base_cmd, "All tests")
    
    elif args.type == 'unit':
        cmd = base_cmd + ['-m', 'not integration']
        success &= run_command(cmd, "Unit tests")
    
    elif args.type == 'integration':
        cmd = base_cmd + ['-m', 'integration']
        success &= run_command(cmd, "Integration tests")
    
    elif args.type == 'coverage':
        cmd = base_cmd + ['--cov=heic2jpg', '--cov-report=html', '--cov-report=term']
        success &= run_command(cmd, "Tests with coverage")
        
        if success:
            print("\n" + "="*50)
            print("Coverage report generated in htmlcov/index.html")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())