#!/bin/bash
# AVA OLO Constitutional Design System Deployment Script

set -e

echo "🚀 Deploying AVA OLO Constitutional Design System to ECS"

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="127679825789"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
AGRICULTURAL_REPO="ava-olo/agricultural-core"
MONITORING_REPO="ava-olo/monitoring-dashboards"
VERSION="v2.5.0-constitutional"

# Step 1: Login to ECR
echo "📦 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Step 2: Build Agricultural Core image
echo "🔨 Building Agricultural Core image..."
docker build -f Dockerfile.agricultural-constitutional -t ${AGRICULTURAL_REPO}:${VERSION} -t ${AGRICULTURAL_REPO}:latest .

# Step 3: Tag and push Agricultural Core
echo "📤 Pushing Agricultural Core to ECR..."
docker tag ${AGRICULTURAL_REPO}:${VERSION} ${ECR_REGISTRY}/${AGRICULTURAL_REPO}:${VERSION}
docker tag ${AGRICULTURAL_REPO}:latest ${ECR_REGISTRY}/${AGRICULTURAL_REPO}:latest
docker push ${ECR_REGISTRY}/${AGRICULTURAL_REPO}:${VERSION}
docker push ${ECR_REGISTRY}/${AGRICULTURAL_REPO}:latest

# Step 4: Build Monitoring API image
echo "🔨 Building Monitoring API image..."
docker build -f Dockerfile.monitoring-constitutional -t ${MONITORING_REPO}:${VERSION} -t ${MONITORING_REPO}:latest .

# Step 5: Tag and push Monitoring API
echo "📤 Pushing Monitoring API to ECR..."
docker tag ${MONITORING_REPO}:${VERSION} ${ECR_REGISTRY}/${MONITORING_REPO}:${VERSION}
docker tag ${MONITORING_REPO}:latest ${ECR_REGISTRY}/${MONITORING_REPO}:latest
docker push ${ECR_REGISTRY}/${MONITORING_REPO}:${VERSION}
docker push ${ECR_REGISTRY}/${MONITORING_REPO}:latest

echo "✅ Images built and pushed successfully!"

# Step 6: Update ECS services
echo "🔄 Updating ECS services..."

# Force new deployment for agricultural service
echo "Updating agricultural service..."
aws ecs update-service \
    --cluster ava-olo-cluster \
    --service ava-agricultural-service \
    --force-new-deployment \
    --region ${AWS_REGION}

# Force new deployment for monitoring service
echo "Updating monitoring service..."
aws ecs update-service \
    --cluster ava-olo-cluster \
    --service ava-monitoring-service \
    --force-new-deployment \
    --region ${AWS_REGION}

echo "✅ ECS services updated!"
echo "📊 Deployment initiated. Services will update in a few minutes."
echo "🔍 Check the AWS console for deployment progress."
echo "🌾 Constitutional Design System v${VERSION} deployment complete!"