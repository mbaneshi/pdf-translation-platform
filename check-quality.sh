#!/bin/bash

# Quality Check Script for PDF Translation Platform
# This script runs all the same checks that would run in CI/CD

set -e  # Exit on any error

echo "🚀 Running Quality Checks for PDF Translation Platform"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a command and check result
run_check() {
    local description="$1"
    local command="$2"
    
    echo -e "\n🔍 ${YELLOW}$description${NC}"
    echo "Running: $command"
    
    if eval "$command"; then
        echo -e "✅ ${GREEN}$description - PASSED${NC}"
        return 0
    else
        echo -e "❌ ${RED}$description - FAILED${NC}"
        return 1
    fi
}

# Track failed checks
failed_checks=0

# Backend Quality Checks
echo -e "\n${YELLOW}📦 BACKEND QUALITY CHECKS${NC}"
echo "=========================="

cd backend

# Type checking
if ! run_check "MyPy Static Type Checking" "python -m mypy app/ --show-error-codes --ignore-missing-imports"; then
    ((failed_checks++))
fi

# Import analysis
if ! run_check "Import Analysis" "python -c \"
import sys
sys.path.append('.')
try:
    from app.main import app
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
\""; then
    ((failed_checks++))
fi

# Code formatting
if ! run_check "Black Code Formatting Check" "python -m black --check --diff app/ tests/"; then
    ((failed_checks++))
fi

# Import sorting
if ! run_check "Import Sorting Check" "python -m isort --check-only --diff app/ tests/"; then
    ((failed_checks++))
fi

# Linting
if ! run_check "Ruff Linting" "python -m ruff check app/ tests/"; then
    ((failed_checks++))
fi

# Tests
if ! run_check "Unit Tests" "python -m pytest tests/ -v --tb=short"; then
    ((failed_checks++))
fi

cd ..

# Frontend Quality Checks
echo -e "\n${YELLOW}🎨 FRONTEND QUALITY CHECKS${NC}"
echo "============================"

cd frontend

# TypeScript check
if ! run_check "TypeScript Compilation Check" "npx tsc --noEmit"; then
    ((failed_checks++))
fi

# ESLint
if ! run_check "ESLint Check" "npx eslint . --ext .js,.jsx,.ts,.tsx"; then
    ((failed_checks++))
fi

# Tests
if ! run_check "Frontend Tests" "npm test -- --watchAll=false"; then
    ((failed_checks++))
fi

cd ..

# Summary
echo -e "\n${YELLOW}📊 QUALITY CHECK SUMMARY${NC}"
echo "=========================="

if [ $failed_checks -eq 0 ]; then
    echo -e "✅ ${GREEN}All quality checks passed!${NC}"
    echo -e "🎉 ${GREEN}Your code is ready for commit and deployment!${NC}"
    exit 0
else
    echo -e "❌ ${RED}$failed_checks checks failed${NC}"
    echo -e "💡 ${YELLOW}Please fix the issues above before committing${NC}"
    echo -e "\n${YELLOW}Quick fixes:${NC}"
    echo "  - Run 'cd backend && python -m black app/ tests/' to fix formatting"
    echo "  - Run 'cd backend && python -m isort app/ tests/' to fix imports"
    echo "  - Run 'cd frontend && npx eslint . --fix' to fix linting issues"
    exit 1
fi
