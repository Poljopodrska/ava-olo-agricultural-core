#!/bin/bash

echo "📊 MONITORING ECS DEPLOYMENT"
echo "============================"
echo ""

# Get expected version
EXPECTED_VERSION=$(grep "VERSION = " modules/core/config.py | cut -d'"' -f2)
echo "Expected version: $EXPECTED_VERSION"
echo ""

# Monitor build first
BUILD_ID="$1"
if [ -z "$BUILD_ID" ]; then
    # Get latest build ID
    BUILD_ID=$(aws codebuild list-builds-for-project \
        --project-name ava-agricultural-docker-build \
        --sort-order DESCENDING \
        --max-items 1 \
        --region us-east-1 \
        --query 'ids[0]' \
        --output text)
fi

echo "Monitoring build: $BUILD_ID"
echo ""

# Monitor build progress
echo "=== BUILD PROGRESS ==="
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Get build status
    BUILD_INFO=$(aws codebuild batch-get-builds --ids "$BUILD_ID" --region us-east-1 --query 'builds[0]' --output json)
    BUILD_STATUS=$(echo "$BUILD_INFO" | grep -o '"buildStatus": "[^"]*"' | cut -d'"' -f4)
    CURRENT_PHASE=$(echo "$BUILD_INFO" | grep -o '"currentPhase": "[^"]*"' | cut -d'"' -f4)
    
    echo -ne "\r[${ELAPSED}s] Build: $BUILD_STATUS | Phase: $CURRENT_PHASE    "
    
    if [ "$BUILD_STATUS" != "IN_PROGRESS" ]; then
        echo ""
        if [ "$BUILD_STATUS" == "SUCCEEDED" ]; then
            echo "✅ Build completed successfully!"
            break
        else
            echo "❌ Build failed with status: $BUILD_STATUS"
            exit 1
        fi
    fi
    
    sleep 5
done

echo ""
echo "=== ECS DEPLOYMENT ==="
echo "Waiting for ECS to update..."
sleep 10

# Monitor ECS deployment
DEPLOYMENT_START=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - DEPLOYMENT_START))
    
    # Get service info
    SERVICE_INFO=$(aws ecs describe-services \
        --cluster ava-olo-production \
        --services agricultural-core \
        --region us-east-1 \
        --output json)
    
    # Extract deployment info
    DEPLOYMENTS=$(echo "$SERVICE_INFO" | grep -A 10 '"deployments"')
    ACTIVE_COUNT=$(echo "$DEPLOYMENTS" | grep -c '"status": "ACTIVE"')
    PRIMARY_COUNT=$(echo "$DEPLOYMENTS" | grep -c '"status": "PRIMARY"')
    
    # Get running/desired counts
    RUNNING=$(echo "$SERVICE_INFO" | grep '"runningCount":' | head -1 | grep -o '[0-9]*')
    DESIRED=$(echo "$SERVICE_INFO" | grep '"desiredCount":' | head -1 | grep -o '[0-9]*')
    
    echo -ne "\r[${ELAPSED}s] Running: $RUNNING/$DESIRED | Deployments: $ACTIVE_COUNT active, $PRIMARY_COUNT primary    "
    
    # Check if deployment is complete
    if [ "$PRIMARY_COUNT" -eq "1" ] && [ "$ACTIVE_COUNT" -eq "1" ] && [ "$RUNNING" -eq "$DESIRED" ]; then
        echo ""
        echo "✅ ECS deployment complete!"
        break
    fi
    
    # Timeout after 10 minutes
    if [ $ELAPSED -gt 600 ]; then
        echo ""
        echo "⚠️  Deployment taking longer than expected"
        break
    fi
    
    sleep 10
done

echo ""
echo "=== VERSION VERIFICATION ==="
echo "Checking deployed version..."
sleep 30  # Give ALB time to update

# Check version multiple times
for i in {1..5}; do
    DEPLOYED_VERSION=$(curl -s -m 5 http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ 2>/dev/null | grep -o "v[0-9]\.[0-9]\.[0-9][0-9]*[^\"]*" | head -1 || echo "")
    
    if [ -n "$DEPLOYED_VERSION" ]; then
        echo "Deployed version: $DEPLOYED_VERSION"
        
        if [ "$DEPLOYED_VERSION" == "$EXPECTED_VERSION" ]; then
            echo ""
            echo "✅ SUCCESS! Version $EXPECTED_VERSION is now deployed!"
            echo ""
            echo "Deployment completed in $(($(date +%s) - START_TIME)) seconds"
            exit 0
        else
            echo "Version mismatch - attempt $i/5"
        fi
    else
        echo "Could not reach endpoint - attempt $i/5"
    fi
    
    if [ $i -lt 5 ]; then
        sleep 15
    fi
done

echo ""
echo "❌ Version verification failed"
echo "Expected: $EXPECTED_VERSION"
echo "Got: $DEPLOYED_VERSION"
echo ""
echo "Check manually at:"
echo "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health"