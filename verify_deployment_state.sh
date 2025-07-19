#!/bin/bash
# Deployment State Verification Script
# Helps diagnose AWS App Runner deployment issues

echo "🔬 AVA OLO Deployment State Verification"
echo "========================================"
echo "Generated: $(date)"
echo ""

# Service URL
SERVICE_URL="https://ujvej9snpp.us-east-1.awsapprunner.com"

echo "📊 1. Repository State Check"
echo "---------------------------"
echo "Current branch: $(git branch --show-current)"
echo "Latest commit: $(git log -1 --oneline)"
echo "Expected version: 3.1.0-constitutional-ui"
echo ""

# Check if constitutional UI file exists
if [ -f "api_gateway_constitutional_ui.py" ]; then
    echo "✅ Constitutional UI file exists"
    echo "   Size: $(ls -lh api_gateway_constitutional_ui.py | awk '{print $5}')"
    echo "   Modified: $(ls -lh api_gateway_constitutional_ui.py | awk '{print $6, $7, $8}')"
else
    echo "❌ Constitutional UI file NOT FOUND"
fi

# Check apprunner.yaml
echo ""
echo "📋 2. Configuration Check"
echo "------------------------"
if [ -f "apprunner.yaml" ]; then
    echo "apprunner.yaml start command:"
    grep "command:" apprunner.yaml | head -1
    echo ""
    echo "apprunner.yaml version:"
    grep "value:" apprunner.yaml | grep "constitutional" | head -1
else
    echo "❌ apprunner.yaml NOT FOUND"
fi

echo ""
echo "🌐 3. Deployed Service Check"
echo "----------------------------"
echo "Testing: $SERVICE_URL"

# Test health endpoint
echo ""
echo "Health endpoint response:"
HEALTH=$(curl -s "$SERVICE_URL/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
    
    # Extract version
    VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "Deployed version: $VERSION"
    
    if [[ "$VERSION" == "3.1.0-constitutional-ui" ]]; then
        echo "✅ CORRECT VERSION DEPLOYED!"
    else
        echo "❌ WRONG VERSION - Expected 3.1.0-constitutional-ui"
    fi
else
    echo "❌ Health endpoint not responding"
fi

# Test UI endpoint
echo ""
echo "UI endpoint test:"
UI_TEST=$(curl -s -H "Accept: text/html" "$SERVICE_URL/" 2>/dev/null | head -5)
if [[ "$UI_TEST" == *"AVA OLO"* ]]; then
    if [[ "$UI_TEST" == *"Constitutional"* ]] || [[ "$UI_TEST" == *"Bulgarian"* ]]; then
        echo "✅ Constitutional UI detected"
    else
        echo "❌ Minimal UI detected (not constitutional)"
    fi
else
    echo "❌ UI endpoint not responding"
fi

echo ""
echo "🔍 4. Deployment Gap Analysis"
echo "-----------------------------"
echo "Repository version: 3.1.0-constitutional-ui"
echo "Deployed version: $VERSION"
echo ""

if [[ "$VERSION" != "3.1.0-constitutional-ui" ]]; then
    echo "⚠️  DEPLOYMENT ISSUE DETECTED!"
    echo ""
    echo "Recommended Actions:"
    echo "1. Manual deployment via AWS Console"
    echo "2. Check GitHub connection status"
    echo "3. Verify auto-deployment is enabled"
    echo "4. Clear build cache if needed"
else
    echo "✅ Deployment is up to date!"
fi

echo ""
echo "📊 5. Bulgarian Mango Farmer Test"
echo "---------------------------------"
MANGO_TEST=$(curl -s -X POST "$SERVICE_URL/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "How to grow mangoes in Bulgaria?", "farmer_id": 1}' 2>/dev/null)

if [[ "$MANGO_TEST" == *"greenhouse"* ]] || [[ "$MANGO_TEST" == *"Bulgarian"* ]]; then
    echo "✅ Bulgarian mango farmer test PASSED"
    echo "Response: ${MANGO_TEST:0:100}..."
elif [[ "$MANGO_TEST" == *"Thank you for your agricultural question"* ]]; then
    echo "⚠️  Generic response (not constitutional)"
    echo "Response: ${MANGO_TEST:0:100}..."
else
    echo "❌ Bulgarian mango farmer test FAILED"
    echo "Response: $MANGO_TEST"
fi

echo ""
echo "========================================"
echo "Verification complete: $(date)"