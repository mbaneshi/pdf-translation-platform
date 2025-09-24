#!/bin/bash

# Preflight validation script for PDF Translation Platform
# This script performs comprehensive checks before building/deploying

set -e

echo "🚀 Starting PDF Translation Platform Preflight Checks..."
echo "=================================================="

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check file exists
file_exists() {
    [ -f "$1" ]
}

# Function to check directory exists
dir_exists() {
    [ -d "$1" ]
}

# Initialize counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Check function that increments counters
check() {
    local status=$1
    local message=$2
    print_status "$status" "$message"
    case $status in
        "PASS") ((PASS_COUNT++)) ;;
        "FAIL") ((FAIL_COUNT++)) ;;
        "WARN") ((WARN_COUNT++)) ;;
    esac
}

echo ""
echo "📋 Environment Checks"
echo "---------------------"

# Check Docker
if command_exists docker; then
    check "PASS" "Docker is installed ($(docker --version))"
else
    check "FAIL" "Docker is not installed"
fi

# Check Docker Compose
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    check "PASS" "Docker Compose is available"
else
    check "FAIL" "Docker Compose is not available"
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    check "PASS" "Node.js is installed ($NODE_VERSION)"
    
    # Check Node version compatibility
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -ge 18 ]; then
        check "PASS" "Node.js version is compatible (>=18)"
    else
        check "WARN" "Node.js version may be too old (recommend >=18)"
    fi
else
    check "FAIL" "Node.js is not installed"
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    check "PASS" "Python3 is installed ($PYTHON_VERSION)"
    
    # Check Python version compatibility
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$PYTHON_MAJOR" -ge 11 ]; then
        check "PASS" "Python version is compatible (>=3.11)"
    else
        check "WARN" "Python version may be too old (recommend >=3.11)"
    fi
else
    check "FAIL" "Python3 is not installed"
fi

echo ""
echo "📁 Project Structure Checks"
echo "---------------------------"

# Check essential directories
for dir in "backend" "frontend" "scripts" "uploads" "logs"; do
    if dir_exists "$dir"; then
        check "PASS" "Directory '$dir' exists"
    else
        check "FAIL" "Directory '$dir' is missing"
    fi
done

# Check essential files
for file in "docker-compose.yml" "backend/requirements.txt" "frontend/package.json" "backend/app/main.py" "frontend/app/layout.tsx"; do
    if file_exists "$file"; then
        check "PASS" "File '$file' exists"
    else
        check "FAIL" "File '$file' is missing"
    fi
done

echo ""
echo "🔧 Configuration Checks"
echo "----------------------"

# Check environment files
if file_exists ".env"; then
    check "PASS" "Environment file (.env) exists"
    
    # Check for required environment variables
    if grep -q "OPENAI_API_KEY" .env; then
        check "PASS" "OPENAI_API_KEY is configured"
    else
        check "WARN" "OPENAI_API_KEY not found in .env"
    fi
    
    if grep -q "DATABASE_URL" .env; then
        check "PASS" "DATABASE_URL is configured"
    else
        check "WARN" "DATABASE_URL not found in .env"
    fi
    
    if grep -q "REDIS_URL" .env; then
        check "PASS" "REDIS_URL is configured"
    else
        check "WARN" "REDIS_URL not found in .env"
    fi
else
    check "WARN" "Environment file (.env) not found - using defaults"
fi

echo ""
echo "🐍 Backend Validation"
echo "--------------------"

# Check Python dependencies
if file_exists "backend/requirements.txt"; then
    check "PASS" "Python requirements file exists"
    
    # Check if virtual environment exists (optional)
    if dir_exists "backend/venv" || dir_exists "venv"; then
        check "PASS" "Python virtual environment found"
    else
        check "WARN" "No Python virtual environment found (recommended)"
    fi
else
    check "FAIL" "Python requirements file missing"
fi

# Check backend structure
for file in "backend/app/main.py" "backend/app/core/config.py" "backend/app/models/models.py"; do
    if file_exists "$file"; then
        check "PASS" "Backend file '$file' exists"
    else
        check "FAIL" "Backend file '$file' is missing"
    fi
done

echo ""
echo "⚛️  Frontend Validation"
echo "----------------------"

# Check Node.js dependencies
if file_exists "frontend/package.json"; then
    check "PASS" "Node.js package.json exists"
    
    # Check if node_modules exists
    if dir_exists "frontend/node_modules"; then
        check "PASS" "Node modules installed"
    else
        check "WARN" "Node modules not installed (run 'npm install')"
    fi
else
    check "FAIL" "Frontend package.json missing"
fi

# Check frontend structure
for file in "frontend/app/layout.tsx" "frontend/components" "frontend/lib/api.ts"; do
    if file_exists "$file" || dir_exists "$file"; then
        check "PASS" "Frontend '$file' exists"
    else
        check "FAIL" "Frontend '$file' is missing"
    fi
done

echo ""
echo "🔍 Type Checking"
echo "----------------"

# Check TypeScript configuration
if file_exists "frontend/tsconfig.json"; then
    check "PASS" "TypeScript configuration exists"
    
    # Try to run TypeScript check
    if command_exists npx && dir_exists "frontend"; then
        cd frontend
        if npx tsc --noEmit --skipLibCheck >/dev/null 2>&1; then
            check "PASS" "TypeScript compilation check passed"
        else
            check "FAIL" "TypeScript compilation errors found"
        fi
        cd ..
    else
        check "WARN" "Cannot run TypeScript check (npx not available)"
    fi
else
    check "WARN" "TypeScript configuration not found"
fi

echo ""
echo "🧪 Test Coverage"
echo "---------------"

# Check for test files
if dir_exists "backend/tests" || dir_exists "frontend/tests"; then
    check "PASS" "Test directories found"
else
    check "WARN" "No test directories found"
fi

# Check for test configuration
if file_exists "backend/pytest.ini" || file_exists "frontend/jest.config.ts"; then
    check "PASS" "Test configuration found"
else
    check "WARN" "No test configuration found"
fi

echo ""
echo "🐳 Docker Validation"
echo "------------------"

# Check Docker Compose file
if file_exists "docker-compose.yml"; then
    check "PASS" "Docker Compose file exists"
    
    # Validate Docker Compose syntax
    if docker compose config >/dev/null 2>&1; then
        check "PASS" "Docker Compose configuration is valid"
    else
        check "FAIL" "Docker Compose configuration has errors"
    fi
else
    check "FAIL" "Docker Compose file missing"
fi

# Check Dockerfiles
for dockerfile in "backend/Dockerfile" "frontend/Dockerfile"; do
    if file_exists "$dockerfile"; then
        check "PASS" "Dockerfile '$dockerfile' exists"
    else
        check "FAIL" "Dockerfile '$dockerfile' missing"
    fi
done

echo ""
echo "📊 Summary"
echo "=========="

print_status "INFO" "Total checks: $((PASS_COUNT + FAIL_COUNT + WARN_COUNT))"
print_status "PASS" "Passed: $PASS_COUNT"
print_status "FAIL" "Failed: $FAIL_COUNT"
print_status "WARN" "Warnings: $WARN_COUNT"

echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    if [ $WARN_COUNT -eq 0 ]; then
        print_status "PASS" "All preflight checks passed! Ready for deployment."
        exit 0
    else
        print_status "WARN" "Preflight checks passed with warnings. Review warnings before deployment."
        exit 0
    fi
else
    print_status "FAIL" "Preflight checks failed. Fix errors before proceeding."
    exit 1
fi
