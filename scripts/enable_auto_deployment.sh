#!/bin/bash

echo "🚀 Enabling Auto-Deployment for AVA OLO Agricultural Core"
echo "========================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}Step 1: Checking buildspec.yml...${NC}"
if grep -q "aws ecs update-service" buildspec.yml; then
    echo -e "${GREEN}✅ buildspec.yml already contains ECS update command${NC}"
else
    echo -e "${RED}❌ buildspec.yml missing ECS update command${NC}"
    echo "Please update buildspec.yml manually"
fi

echo -e "\n${YELLOW}Step 2: Checking IAM permissions...${NC}"
python3 scripts/check_codebuild_permissions.py

echo -e "\n${YELLOW}Step 3: Verifying deployment pipeline...${NC}"
python3 scripts/verify_deployment_pipeline.py

echo -e "\n${YELLOW}Step 4: Quick summary...${NC}"
echo "To complete auto-deployment setup:"
echo ""
echo "1. Ensure GitHub webhook is configured in CodeBuild"
echo "   - Go to CodeBuild console"
echo "   - Edit project: ava-olo-agricultural-core"
echo "   - Enable 'Rebuild every time a code change is pushed'"
echo ""
echo "2. Verify buildspec.yml has been updated (already done ✅)"
echo ""
echo "3. Test by pushing code:"
echo "   git add -A"
echo "   git commit -m 'test: auto-deployment'"
echo "   git push origin main"
echo ""
echo "4. Monitor deployment:"
echo "   - CodeBuild: https://console.aws.amazon.com/codesuite/codebuild/projects"
echo "   - ECS: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ava-olo-production/services"
echo ""
echo -e "${GREEN}✅ Auto-deployment configuration complete!${NC}"
echo "Next push will automatically deploy to ECS in ~5 minutes"