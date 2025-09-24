#!/bin/bash

# Comprehensive Code Quality Check Script
# This script runs all quality checks for both backend and frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Check function
run_check() {
    local name=$1
    local command=$2
    local directory=$3
    
    ((TOTAL_CHECKS++))
    
    echo ""
    print_status "INFO" "Running: $name"
    
    if [ -n "$directory" ]; then
        cd "$directory"
    fi
    
    if eval "$command" >/dev/null 2>&1; then
        print_status "PASS" "$name completed successfully"
        ((PASSED_CHECKS++))
    else
        print_status "FAIL" "$name failed"
        ((FAILED_CHECKS++))
        
        # Show error details
        echo "Command: $command"
        echo "Directory: ${directory:-$(pwd)}"
        echo "Error output:"
        eval "$command" 2>&1 | head -20
        echo ""
    fi
    
    if [ -n "$directory" ]; then
        cd - >/dev/null
    fi
}

echo "🔍 Starting Comprehensive Code Quality Checks"
echo "============================================="

# Backend Quality Checks
echo ""
echo "🐍 Backend Quality Checks"
echo "-------------------------"

# Check if backend directory exists
if [ ! -d "backend" ]; then
    print_status "FAIL" "Backend directory not found"
    exit 1
fi

# Python formatting check
run_check "Black formatting check" "python -m black --check --diff ." "backend"

# Python import sorting check
run_check "isort import sorting check" "python -m isort --check-only --diff ." "backend"

# Python linting with Ruff
run_check "Ruff linting check" "python -m ruff check ." "backend"

# Python type checking with MyPy
run_check "MyPy type checking" "python -m mypy ." "backend"

# Python security check with Bandit
run_check "Bandit security check" "python -m bandit -r app/ -f json" "backend"

# Python test coverage
run_check "Python test coverage" "python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80" "backend"

# Frontend Quality Checks
echo ""
echo "⚛️  Frontend Quality Checks"
echo "--------------------------"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_status "FAIL" "Frontend directory not found"
    exit 1
fi

# TypeScript type checking
run_check "TypeScript type checking" "npx tsc --noEmit" "frontend"

# ESLint linting
run_check "ESLint linting check" "npx eslint . --ext .js,.jsx,.ts,.tsx" "frontend"

# Prettier formatting check
run_check "Prettier formatting check" "npx prettier --check ." "frontend"

# Jest tests with coverage
run_check "Jest test coverage" "npm run test:coverage" "frontend"

# Next.js build check
run_check "Next.js build check" "npm run build" "frontend"

# Docker Quality Checks
echo ""
echo "🐳 Docker Quality Checks"
echo "-----------------------"

# Docker Compose configuration validation
run_check "Docker Compose config validation" "docker compose config"

# Dockerfile linting (if dockerfile-lint is available)
if command -v dockerfile-lint >/dev/null 2>&1; then
    run_check "Dockerfile linting" "dockerfile-lint Dockerfile*"
else
    print_status "WARN" "dockerfile-lint not available, skipping Dockerfile linting"
fi

# Security scanning (if trivy is available)
if command -v trivy >/dev/null 2>&1; then
    run_check "Container security scan" "trivy fs ."
else
    print_status "WARN" "trivy not available, skipping security scan"
fi

# Overall Quality Summary
echo ""
echo "📊 Quality Check Summary"
echo "========================"

print_status "INFO" "Total checks: $TOTAL_CHECKS"
print_status "PASS" "Passed: $PASSED_CHECKS"
print_status "FAIL" "Failed: $FAILED_CHECKS"

# Calculate success rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    print_status "INFO" "Success rate: ${SUCCESS_RATE}%"
fi

echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    print_status "PASS" "All quality checks passed! 🎉"
    echo ""
    print_status "INFO" "Code is ready for commit and deployment."
    exit 0
else
    print_status "FAIL" "Quality checks failed. Please fix issues before proceeding."
    echo ""
    print_status "INFO" "Run the following commands to fix common issues:"
    echo ""
    echo "Backend fixes:"
    echo "  cd backend"
    echo "  python -m black ."
    echo "  python -m isort ."
    echo "  python -m ruff check --fix ."
    echo ""
    echo "Frontend fixes:"
    echo "  cd frontend"
    echo "  npm run lint:fix"
    echo "  npm run format"
    echo ""
    exit 1
fi
