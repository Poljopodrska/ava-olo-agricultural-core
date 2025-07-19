#!/bin/bash
# Deployment Verification Script for AVA OLO
# Version: 3.2.7-pipeline-fix

echo "=== AVA OLO Deployment Verification ==="
echo "Testing version 3.2.7-pipeline-fix"
echo ""

URL="https://ujvej9snpp.us-east-1.awsapprunner.com"

# 1. Check version
echo "1. Checking version endpoint..."
VERSION=$(curl -s $URL/api/v1/deployment/verify | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
echo "   Deployed version: $VERSION"

# 2. Check functionality hash
echo ""
echo "2. Checking functionality hash..."
HASH=$(curl -s $URL/api/v1/deployment/verify | grep -o '"functionality_hash":"[^"]*"' | cut -d'"' -f4)
echo "   Functionality hash: $HASH"

# 3. Test CAVA endpoint
echo ""
echo "3. Testing CAVA conversation endpoint..."
RESPONSE=$(curl -s -X POST $URL/api/v1/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","farmer_id":1}' | grep -o '"response":"[^"]*"' | cut -d'"' -f4)
if [ -n "$RESPONSE" ]; then
    echo "   ✓ CAVA endpoint working"
    echo "   Response: ${RESPONSE:0:50}..."
else
    echo "   ✗ CAVA endpoint failed"
fi

# 4. Check for debug logs in chat page
echo ""
echo "4. Checking for debug logs in /chat..."
DEBUG_LOGS=$(curl -s $URL/chat | grep -c "console.log")
echo "   Found $DEBUG_LOGS console.log statements"

# 5. Check specific debug messages
echo ""
echo "5. Verifying specific debug messages..."
if curl -s $URL/chat | grep -q "console.log('Key pressed:', event.key)"; then
    echo "   ✓ Enter key debug log present"
else
    echo "   ✗ Enter key debug log missing"
fi

if curl -s $URL/chat | grep -q "console.log('sendMessage called')"; then
    echo "   ✓ sendMessage debug log present"
else
    echo "   ✗ sendMessage debug log missing"
fi

if curl -s $URL/chat | grep -q "DOMContentLoaded"; then
    echo "   ✓ DOMContentLoaded handler present"
else
    echo "   ✗ DOMContentLoaded handler missing"
fi

# 6. Summary
echo ""
echo "=== Deployment Verification Complete ==="
echo "Expected version: 3.2.7-pipeline-fix"
echo "Actual version: $VERSION"

if [ "$VERSION" = "3.2.7-pipeline-fix" ]; then
    echo "✓ VERSION MATCH - Deployment successful!"
else
    echo "✗ VERSION MISMATCH - Deployment may be pending or failed"
fi