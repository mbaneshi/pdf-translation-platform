#!/usr/bin/env python3
"""
Comprehensive linting script for the PDF Translation Platform backend.
This script runs all linting and static analysis tools to catch issues early.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Run all linting checks."""
    print("🚀 Running comprehensive linting checks...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    checks = [
        # Import analysis
        (["python", "-m", "unimport", "--check", "--diff", "app/"], "Unused imports check"),
        (["python", "-m", "import-linter", "app/"], "Import dependency analysis"),
        
        # Static type checking
        (["python", "-m", "mypy", "app/", "--show-error-codes"], "MyPy static type checking"),
        
        # Code formatting and style
        (["python", "-m", "black", "--check", "--diff", "app/", "tests/"], "Black code formatting"),
        (["python", "-m", "isort", "--check-only", "--diff", "app/", "tests/"], "Import sorting"),
        
        # Linting
        (["python", "-m", "ruff", "check", "app/", "tests/"], "Ruff linting"),
        (["python", "-m", "flake8", "app/", "tests/"], "Flake8 linting"),
        
        # Security analysis
        (["python", "-m", "bandit", "-r", "app/", "-f", "json"], "Security analysis"),
        
        # Run tests to ensure nothing is broken
        (["python", "-m", "pytest", "tests/", "-v", "--tb=short"], "Unit tests"),
    ]
    
    failed_checks = []
    
    for cmd, description in checks:
        if not run_command(cmd, description):
            failed_checks.append(description)
    
    print(f"\n{'='*60}")
    print("📊 LINTING SUMMARY")
    print(f"{'='*60}")
    
    if failed_checks:
        print(f"❌ {len(failed_checks)} checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        print(f"\n💡 Fix the issues above and run this script again.")
        sys.exit(1)
    else:
        print("✅ All linting checks passed!")
        print("🎉 Your code is ready for commit!")

if __name__ == "__main__":
    main()
