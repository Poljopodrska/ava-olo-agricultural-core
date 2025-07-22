#!/bin/bash

echo "🚀 Ensuring v3.3.22 is fully deployed..."
echo "========================================="

# Step 1: Check current version in code
echo -e "\n1️⃣ Checking version in code..."
EXPECTED_VERSION=$(grep "VERSION = " modules/core/config.py | cut -d'"' -f2)
echo "Expected version: $EXPECTED_VERSION"

# Step 2: Check currently deployed version
echo -e "\n2️⃣ Checking currently deployed version..."
CURRENT_VERSION=$(curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ | grep -o "v[0-9]\.[0-9]\.[0-9][0-9]*[^\"]*" | head -1 || echo "unknown")
echo "Currently deployed: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" == "$EXPECTED_VERSION" ]; then
    echo "✅ Already deployed!"
    exit 0
fi

# Step 3: Check if CodeBuild is running
echo -e "\n3️⃣ Checking CodeBuild status..."
LATEST_BUILD=$(aws codebuild list-builds-for-project \
    --project-name ava-agricultural-docker-build \
    --sort-order DESCENDING \
    --max-items 1 \
    --region us-east-1 \
    --query 'ids[0]' \
    --output text)

if [ "$LATEST_BUILD" != "None" ]; then
    BUILD_STATUS=$(aws codebuild batch-get-builds \
        --ids "$LATEST_BUILD" \
        --region us-east-1 \
        --query 'builds[0].buildStatus' \
        --output text)
    
    echo "Latest build: $LATEST_BUILD"
    echo "Status: $BUILD_STATUS"
    
    if [ "$BUILD_STATUS" == "IN_PROGRESS" ]; then
        echo "⏳ Build in progress. Waiting for completion..."
        # Wait up to 5 minutes for build to complete
        for i in {1..10}; do
            sleep 30
            BUILD_STATUS=$(aws codebuild batch-get-builds \
                --ids "$LATEST_BUILD" \
                --region us-east-1 \
                --query 'builds[0].buildStatus' \
                --output text)
            echo "Build status: $BUILD_STATUS"
            if [ "$BUILD_STATUS" != "IN_PROGRESS" ]; then
                break
            fi
        done
    fi
fi

# Step 4: Pull latest ECR image tag
echo -e "\n4️⃣ Updating ECR latest tag..."
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 127679825789.dkr.ecr.us-east-1.amazonaws.com

# Pull and tag as latest to ensure it's current
REPO_URI="127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core"
echo "Pulling latest image..."
docker pull $REPO_URI:latest || echo "Could not pull latest"

# Step 5: Force ECS update
echo -e "\n5️⃣ Forcing ECS service update..."
aws ecs update-service \
    --cluster ava-olo-production \
    --service agricultural-core \
    --force-new-deployment \
    --region us-east-1 \
    --output json > /dev/null

echo "✅ Deployment initiated"

# Step 6: Wait for deployment
echo -e "\n6️⃣ Waiting for deployment to complete..."
echo "This typically takes 2-3 minutes..."

# Wait for service to stabilize
aws ecs wait services-stable \
    --cluster ava-olo-production \
    --services agricultural-core \
    --region us-east-1 || echo "Service taking longer than expected..."

# Step 7: Verify deployment
echo -e "\n7️⃣ Verifying deployment..."
sleep 10  # Give ALB time to update

NEW_VERSION=$(curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ | grep -o "v[0-9]\.[0-9]\.[0-9][0-9]*[^\"]*" | head -1 || echo "unknown")
echo "New deployed version: $NEW_VERSION"

if [ "$NEW_VERSION" == "$EXPECTED_VERSION" ]; then
    echo -e "\n✅ SUCCESS! Version $EXPECTED_VERSION is now deployed!"
else
    echo -e "\n⚠️  Version mismatch. Expected: $EXPECTED_VERSION, Got: $NEW_VERSION"
    echo "Checking health endpoint..."
    curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health | grep version || true
fi

echo -e "\n📊 Deployment Summary:"
echo "- Expected: $EXPECTED_VERSION"
echo "- Deployed: $NEW_VERSION"
echo "- Status: $([ "$NEW_VERSION" == "$EXPECTED_VERSION" ] && echo "✅ Success" || echo "⚠️  Needs attention")"
echo ""
echo "Check full status at:"
echo "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health"