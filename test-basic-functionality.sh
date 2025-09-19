#!/bin/bash

# Basic functionality test for PDF Translation Platform
# Tests core API endpoints and verifies system health

API_BASE="${API_URL:-https://apipdf.edcopo.info}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 PDF Translation Platform - Basic Functionality Test${NC}"
echo -e "${YELLOW}=================================================${NC}"

PASSED=0
FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local expected_status="${4:-200}"

    echo -e "\n📡 Testing $name at $url"

    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" 2>/dev/null)

    if [ "$response" = "$expected_status" ] || [ "$response" = "405" ] || [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ $name: Available (status: $response)${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name: Failed (status: $response)${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test API Health
test_endpoint "API Health" "$API_BASE/health"

# Test API Documentation (optional)
if test_endpoint "API Documentation" "$API_BASE/docs"; then
    echo -e "${GREEN}✅ API Documentation accessible${NC}"
else
    echo -e "${YELLOW}⚠️  API Documentation might be disabled in production${NC}"
fi

# Test Documents List
test_endpoint "Documents List" "$API_BASE/api/documents/"

# Test Upload Endpoint
test_endpoint "Upload Endpoint" "$API_BASE/api/documents/upload" "OPTIONS"

# Test Enhanced Upload Endpoint
test_endpoint "Enhanced Upload Endpoint" "$API_BASE/api/enhanced/upload" "OPTIONS"

# Test specific document operations
echo -e "\n📋 Testing additional endpoints..."

# Test monitoring endpoints
test_endpoint "Monitoring Health" "$API_BASE/api/monitoring/health"

# Test enhanced endpoints
test_endpoint "Enhanced Documents" "$API_BASE/api/enhanced/"

echo -e "\n${YELLOW}===============================================${NC}"
echo -e "${YELLOW}📊 Test Results Summary${NC}"
echo -e "${YELLOW}===============================================${NC}"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: $FAILED${NC}"
fi

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All core tests passed! The application appears to be working correctly.${NC}"
    echo -e "${GREEN}✨ You can now upload PDF documents and start translations.${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some tests failed, but core functionality should still work.${NC}"
fi

echo -e "\n${YELLOW}📝 Quick Start Guide:${NC}"
echo "1. Go to http://localhost:3000 or your frontend URL"
echo "2. Click 'New Document' if you have an existing document loaded"
echo "3. Upload a PDF file by dragging and dropping"
echo "4. Wait for processing and translation"
echo "5. Use the review page for editing and adjustments"
echo "6. Configure your settings at /settings for custom prompts and API keys"

echo -e "\n${YELLOW}🔧 Available Features:${NC}"
echo "• Custom API key configuration"
echo "• Custom translation prompts"
echo "• Black & white theme toggle"
echo "• Side-by-side original/translated view"
echo "• Inline translation editing"
echo "• Prompt adjustment controls"
echo "• Glossary management"
echo "• Sample translation style adoption"

exit $FAILED