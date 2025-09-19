#!/bin/bash

# Verify Frontend Updates Script
# Checks if new features are actually deployed and accessible

FRONTEND_URL="${FRONTEND_URL:-https://pdf.edcopo.info}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Frontend Update Verification${NC}"
echo -e "${YELLOW}================================${NC}"
echo -e "Testing: $FRONTEND_URL"

# Function to check if a page contains expected content
check_page_content() {
    local page="$1"
    local search_term="$2"
    local description="$3"

    echo -e "\n📄 Testing $description"

    response=$(curl -s "$FRONTEND_URL$page" 2>/dev/null)

    if [ $? -eq 0 ]; then
        if echo "$response" | grep -q "$search_term"; then
            echo -e "${GREEN}✅ $description: Feature found${NC}"
            return 0
        else
            echo -e "${RED}❌ $description: Feature not found${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $description: Page not accessible${NC}"
        return 1
    fi
}

# Test main page
check_page_content "/" "New Document" "Main page with 'New Document' button"

# Test settings page
check_page_content "/settings" "OpenAI API Key" "Settings page with API key configuration"
check_page_content "/settings" "Custom Prompts" "Settings page with custom prompts"
check_page_content "/settings" "Glossary Terms" "Settings page with glossary management"
check_page_content "/settings" "Quick Theme" "Settings page with theme toggle"

# Test review page
check_page_content "/review" "Side-by-Side" "Review page with side-by-side view" || \
check_page_content "/review" "Original Text" "Review page with original text panel"

# Test if the application loads without JavaScript errors (basic check)
echo -e "\n🔧 Testing JavaScript and CSS loading..."

# Check if main CSS is included
if curl -s "$FRONTEND_URL" | grep -q "/_next/static/css/"; then
    echo -e "${GREEN}✅ CSS files are being loaded${NC}"
else
    echo -e "${YELLOW}⚠️  CSS files might not be loading properly${NC}"
fi

# Check if main JS is included
if curl -s "$FRONTEND_URL" | grep -q "/_next/static/chunks/"; then
    echo -e "${GREEN}✅ JavaScript files are being loaded${NC}"
else
    echo -e "${YELLOW}⚠️  JavaScript files might not be loading properly${NC}"
fi

echo -e "\n${YELLOW}================================${NC}"
echo -e "${YELLOW}📋 Manual Testing Checklist${NC}"
echo -e "${YELLOW}================================${NC}"
echo "Open your browser and test:"
echo "1. Go to: $FRONTEND_URL"
echo "2. Look for 'New Document' button in top-right"
echo "3. Go to: $FRONTEND_URL/settings"
echo "4. Check for API key input field"
echo "5. Check for Custom Prompts section"
echo "6. Check for Quick Theme toggle (White/Black)"
echo "7. Check for Glossary Terms section"
echo "8. Try uploading a PDF file"
echo "9. Go to: $FRONTEND_URL/review"
echo "10. Look for side-by-side layout"

echo -e "\n${GREEN}🎯 Expected New Features:${NC}"
echo "• Custom API key configuration"
echo "• Custom translation prompts (System, Translation, Style)"
echo "• Quick black/white theme toggle"
echo "• Glossary management (add/remove terms)"
echo "• Sample translations for style adoption"
echo "• Side-by-side original/translated view"
echo "• Inline translation editing"
echo "• Prompt adjustment controls"
echo "• 'New Document' reset button"

echo -e "\n${YELLOW}💡 If features aren't visible:${NC}"
echo "1. Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Clear browser cache"
echo "3. Check browser console for errors"
echo "4. Verify Docker containers are healthy: docker-compose ps"