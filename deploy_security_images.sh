#!/bin/bash
# AVA OLO Security Deployment Script
# This script builds and deploys the security-enhanced container images

set -e

echo "🔒 AVA OLO Security Image Deployment"
echo "===================================="
echo ""

# Configuration
AWS_ACCOUNT_ID="127679825789"
AWS_REGION="us-east-1"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
VERSION="v2.6.0-security"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Login to ECR
echo_info "Step 1: Logging into AWS ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Step 2: Build Agricultural Core Image
echo_info "Step 2: Building Agricultural Core image with security features..."
docker build -f Dockerfile.agricultural-constitutional -t ava-olo/agricultural-core:${VERSION} .
docker tag ava-olo/agricultural-core:${VERSION} ${ECR_REGISTRY}/ava-olo/agricultural-core:${VERSION}
docker tag ava-olo/agricultural-core:${VERSION} ${ECR_REGISTRY}/ava-olo/agricultural-core:latest

# Step 3: Build Monitoring Dashboards Image
echo_info "Step 3: Building Monitoring Dashboards image with security features..."
docker build -f Dockerfile.monitoring-constitutional -t ava-olo/monitoring-dashboards:${VERSION} .
docker tag ava-olo/monitoring-dashboards:${VERSION} ${ECR_REGISTRY}/ava-olo/monitoring-dashboards:${VERSION}
docker tag ava-olo/monitoring-dashboards:${VERSION} ${ECR_REGISTRY}/ava-olo/monitoring-dashboards:latest

# Step 4: Push images to ECR
echo_info "Step 4: Pushing images to ECR..."
docker push ${ECR_REGISTRY}/ava-olo/agricultural-core:${VERSION}
docker push ${ECR_REGISTRY}/ava-olo/agricultural-core:latest
docker push ${ECR_REGISTRY}/ava-olo/monitoring-dashboards:${VERSION}
docker push ${ECR_REGISTRY}/ava-olo/monitoring-dashboards:latest

# Step 5: Update ECS Services
echo_info "Step 5: Updating ECS services with new images..."

# Force new deployment for Agricultural Core
echo_info "Updating Agricultural Core service..."
aws ecs update-service \
    --cluster ava-olo-production \
    --service agricultural-core \
    --force-new-deployment \
    --region ${AWS_REGION} \
    --output json > /dev/null

# Force new deployment for Monitoring Dashboards
echo_info "Updating Monitoring Dashboards service..."
aws ecs update-service \
    --cluster ava-olo-production \
    --service monitoring-dashboards \
    --force-new-deployment \
    --region ${AWS_REGION} \
    --output json > /dev/null

echo_info "Services update initiated. Waiting for stability..."

# Wait for services to stabilize
echo_info "Waiting for Agricultural Core to stabilize (this may take 3-5 minutes)..."
aws ecs wait services-stable \
    --cluster ava-olo-production \
    --services agricultural-core \
    --region ${AWS_REGION}

echo_info "Waiting for Monitoring Dashboards to stabilize..."
aws ecs wait services-stable \
    --cluster ava-olo-production \
    --services monitoring-dashboards \
    --region ${AWS_REGION}

# Step 6: Verify deployment
echo_info "Step 6: Verifying deployment..."

# Check service status
AGRI_STATUS=$(aws ecs describe-services \
    --cluster ava-olo-production \
    --services agricultural-core \
    --region ${AWS_REGION} \
    --query 'services[0].deployments[0].status' \
    --output text)

MONITOR_STATUS=$(aws ecs describe-services \
    --cluster ava-olo-production \
    --services monitoring-dashboards \
    --region ${AWS_REGION} \
    --query 'services[0].deployments[0].status' \
    --output text)

echo_info "Agricultural Core deployment status: $AGRI_STATUS"
echo_info "Monitoring Dashboards deployment status: $MONITOR_STATUS"

# Test endpoints
echo_info "Testing service endpoints..."
FARMERS_ALB="http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
INTERNAL_ALB="http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com"

echo_info "Testing Farmers ALB..."
curl -s -o /dev/null -w "Response: %{http_code}\n" ${FARMERS_ALB}/health || echo_warn "Health check failed"

echo_info "Testing Internal ALB..."
curl -s -o /dev/null -w "Response: %{http_code}\n" ${INTERNAL_ALB}/health || echo_warn "Health check failed"

echo ""
echo_info "🎉 Security image deployment completed!"
echo ""
echo_warn "Next Steps:"
echo "1. Verify security headers are active: curl -I ${FARMERS_ALB}/"
echo "2. Test authentication on dashboards"
echo "3. Run HTTPS configuration script: ./scripts/enable_https_alb.sh"
echo ""
echo_info "Version deployed: ${VERSION}"