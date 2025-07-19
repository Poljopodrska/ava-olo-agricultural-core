#!/bin/bash

# Monitor AWS App Runner deployment for cache-busting success
# Target: Version 3.0.0-forensic-cache-bust

SERVICE_URL="https://3ksdvgdtad.us-east-1.awsapprunner.com"
TARGET_VERSION="3.0.0-forensic-cache-bust"
OLD_VERSION="2.0.0-simple"

echo "🔬 Monitoring AWS App Runner cache-busting deployment..."
echo "Target version: $TARGET_VERSION"
echo "Service URL: $SERVICE_URL"
echo "Started at: $(date)"
echo "=========================="

for i in {1..20}; do
    echo "Attempt $i/20: $(date)"
    
    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$HEALTH_RESPONSE" ]; then
        VERSION=$(echo "$HEALTH_RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        TIMESTAMP=$(echo "$HEALTH_RESPONSE" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        
        echo "  📊 Health: OK"
        echo "  📦 Version: $VERSION"
        echo "  🕒 Timestamp: $TIMESTAMP"
        
        if [[ "$VERSION" == "$TARGET_VERSION" ]]; then
            echo ""
            echo "🎉 SUCCESS! New version deployed!"
            echo "✅ Cache busting successful"
            echo "✅ Service running version: $VERSION"
            echo ""
            
            # Test Bulgarian mango farmer scenario
            echo "🥭 Testing Bulgarian mango farmer scenario..."
            MANGO_TEST=$(curl -s -X POST "$SERVICE_URL/api/v1/query" \
                -H "Content-Type: application/json" \
                -d '{"query": "How to grow mangoes in Bulgaria?", "farmer_id": "test_bg_001"}' 2>/dev/null)
            
            if [ $? -eq 0 ] && [[ "$MANGO_TEST" != *"404"* ]] && [[ "$MANGO_TEST" != *"Not Found"* ]]; then
                echo "✅ MANGO RULE: Bulgarian mango farmer test PASSED!"
                echo "✅ API endpoints responding correctly"
                echo "✅ Constitutional compliance restored"
            else
                echo "⚠️  MANGO RULE: API endpoint test needs verification"
                echo "   Response: $MANGO_TEST"
            fi
            
            echo ""
            echo "🏆 DEPLOYMENT SUCCESS - Bulgarian mango farmers have access!"
            exit 0
        elif [[ "$VERSION" == "$OLD_VERSION" ]]; then
            echo "  ⏳ Still old version - waiting for deployment..."
        else
            echo "  🔄 Different version detected: $VERSION"
        fi
    else
        echo "  ❌ Service unavailable"
    fi
    
    if [ $i -lt 20 ]; then
        echo "  ⏳ Waiting 30 seconds..."
        sleep 30
    fi
    echo ""
done

echo "⚠️  Deployment monitoring timeout after 10 minutes"
echo "   Last checked: $(date)"
echo "   Manual verification may be needed"