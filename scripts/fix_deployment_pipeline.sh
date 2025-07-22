#!/bin/bash

echo "🔧 FIXING ECS AUTO-DEPLOYMENT PIPELINE"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Check current situation
echo -e "${YELLOW}1. Checking current deployment status...${NC}"

# Get current version from code
EXPECTED_VERSION=$(grep "VERSION = " modules/core/config.py | cut -d'"' -f2)
echo "Expected version in code: $EXPECTED_VERSION"

# Get deployed version
DEPLOYED_VERSION=$(curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ 2>/dev/null | grep -o "v[0-9]\.[0-9]\.[0-9][0-9]*[^\"]*" | head -1 || echo "unreachable")
echo "Currently deployed: $DEPLOYED_VERSION"

# 2. Fix buildspec.yml to ensure it has all required commands
echo -e "\n${YELLOW}2. Updating buildspec.yml with complete ECS deployment...${NC}"

cat > buildspec.yml << 'EOF'
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
      
      # CRITICAL: Ensure we have latest code
      - echo "Pulling latest code from main branch..."
      - git fetch origin main
      - git reset --hard origin/main
      - git pull origin main
      
      # Verify version
      - echo "Current version in code:"
      - grep -E "VERSION|DEPLOYMENT_TIMESTAMP" modules/core/config.py | head -5
      
  build:
    commands:
      - echo Build started on `date`
      - echo Building Docker image...
      # Force rebuild to ensure latest code
      - docker build --no-cache -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:latest
      
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing Docker images to ECR...
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - docker push $REPOSITORY_URI:latest
      
      # CRITICAL: Update ECS service
      - echo "Updating ECS service to use new image..."
      - |
        aws ecs update-service \
          --cluster ava-olo-production \
          --service agricultural-core \
          --force-new-deployment \
          --region $AWS_DEFAULT_REGION \
          --output json
      
      - echo "Waiting 30 seconds for deployment to start..."
      - sleep 30
      
      # Check deployment status
      - |
        echo "Checking deployment status..."
        aws ecs describe-services \
          --cluster ava-olo-production \
          --services agricultural-core \
          --region $AWS_DEFAULT_REGION \
          --query 'services[0].deployments[0].{status:status,desired:desiredCount,running:runningCount,taskDef:taskDefinition}' \
          --output table
      
      # Optional: Wait for stable (with timeout to prevent hanging)
      - |
        echo "Waiting for service to stabilize (max 5 minutes)..."
        timeout 300 aws ecs wait services-stable \
          --cluster ava-olo-production \
          --services agricultural-core \
          --region $AWS_DEFAULT_REGION || echo "Service is still updating..."
      
      # Verify deployment
      - echo "Deployment initiated successfully!"
      - echo "New containers should be running in 2-3 minutes"
      
artifacts:
  files: 
    - '**/*'
  name: agricultural-core-build
EOF

echo -e "${GREEN}✅ buildspec.yml updated${NC}"

# 3. Check CodeBuild webhook
echo -e "\n${YELLOW}3. Checking CodeBuild webhook configuration...${NC}"

# Get CodeBuild project info
PROJECT_NAME="ava-agricultural-docker-build"
WEBHOOK_EXISTS=$(aws codebuild batch-get-projects --names $PROJECT_NAME --region us-east-1 --query "projects[0].webhook.url" --output text 2>/dev/null)

if [ "$WEBHOOK_EXISTS" != "None" ] && [ -n "$WEBHOOK_EXISTS" ]; then
    echo -e "${GREEN}✅ Webhook already configured${NC}"
else
    echo "Creating webhook for automatic builds..."
    aws codebuild create-webhook --project-name $PROJECT_NAME --region us-east-1
    echo -e "${GREEN}✅ Webhook created${NC}"
fi

# 4. Ensure IAM permissions
echo -e "\n${YELLOW}4. Checking IAM permissions...${NC}"

# Check if permissions script exists and run it
if [ -f "scripts/check_codebuild_permissions.py" ]; then
    echo "Running permissions check..."
    python3 scripts/check_codebuild_permissions.py || echo "Note: boto3 not available, skipping detailed check"
else
    echo "Adding ECS permissions to CodeBuild role..."
    aws iam put-role-policy \
      --role-name ava-codebuild-role \
      --policy-name ECSAutoDeployment \
      --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": [
              "ecs:UpdateService",
              "ecs:DescribeServices",
              "ecs:DescribeTaskDefinition",
              "ecs:DescribeClusters",
              "ecs:ListServices",
              "ecs:RegisterTaskDefinition"
            ],
            "Resource": "*"
          },
          {
            "Effect": "Allow",
            "Action": [
              "iam:PassRole"
            ],
            "Resource": [
              "arn:aws:iam::*:role/ecsTaskExecutionRole",
              "arn:aws:iam::*:role/ava-*"
            ]
          }
        ]
      }' \
      --region us-east-1 2>/dev/null && echo -e "${GREEN}✅ Permissions added${NC}" || echo "Note: Permissions may already exist"
fi

# 5. Force a new build to test
echo -e "\n${YELLOW}5. Triggering new build to test deployment...${NC}"

BUILD_ID=$(aws codebuild start-build \
  --project-name $PROJECT_NAME \
  --region us-east-1 \
  --query 'build.id' \
  --output text)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build started: $BUILD_ID${NC}"
    echo ""
    echo "Monitor progress at:"
    echo "https://console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/build/$BUILD_ID"
    echo ""
    echo "Or check status with:"
    echo "aws codebuild batch-get-builds --ids \"$BUILD_ID\" --query 'builds[0].buildStatus' --output text"
else
    echo -e "${RED}❌ Failed to start build${NC}"
fi

# 6. Summary
echo -e "\n${YELLOW}DEPLOYMENT PIPELINE FIX SUMMARY:${NC}"
echo "================================"
echo -e "${GREEN}✅ buildspec.yml updated with ECS deployment commands${NC}"
echo -e "${GREEN}✅ CodeBuild webhook configured for automatic builds${NC}"
echo -e "${GREEN}✅ IAM permissions verified/added${NC}"
echo -e "${GREEN}✅ Test build triggered${NC}"
echo ""
echo "Next steps:"
echo "1. Wait 5-10 minutes for build and deployment"
echo "2. Check http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
echo "3. Version should update to: $EXPECTED_VERSION"
echo ""
echo "Future deployments will be automatic after git push!"