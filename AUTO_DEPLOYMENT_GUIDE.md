# Auto-Deployment Guide

## Overview
The AVA OLO Agricultural Core now has **fully automated deployments**. When you push code to GitHub, it automatically deploys to ECS within 5 minutes.

## How It Works

```
Git Push → GitHub Webhook → CodeBuild → Docker Build → ECR Push → ECS Update → Live!
```

## Quick Start

### 1. Enable Auto-Deployment (One Time)
```bash
./scripts/enable_auto_deployment.sh
```

### 2. Deploy by Pushing Code
```bash
git add -A
git commit -m "feat: your changes"
git push origin main
```

### 3. Monitor Deployment
- **CodeBuild**: https://console.aws.amazon.com/codesuite/codebuild/projects
- **ECS Service**: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ava-olo-production/services

## What Changed in v3.3.22

### buildspec.yml Enhanced
```yaml
post_build:
  commands:
    # Push to ECR (existing)
    - docker push $REPOSITORY_URI:latest
    
    # NEW: Update ECS service automatically
    - aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --force-new-deployment
    
    # NEW: Wait for deployment
    - aws ecs wait services-stable \
        --cluster ava-olo-production \
        --services agricultural-core
    
    # NEW: Verify deployment
    - curl -s http://ava-olo-alb.../api/v1/system/health
```

### Scripts Added
1. **check_codebuild_permissions.py** - Ensures IAM permissions
2. **verify_deployment_pipeline.py** - Validates entire pipeline
3. **enable_auto_deployment.sh** - One-click setup

## Troubleshooting

### Build Succeeds but ECS Not Updated
1. Check IAM permissions:
   ```bash
   python3 scripts/check_codebuild_permissions.py
   ```

2. Verify buildspec.yml has ECS commands:
   ```bash
   grep "update-service" buildspec.yml
   ```

### Version Not Updating
1. Check ECS service events in console
2. Ensure health checks are passing
3. Wait full 5 minutes for deployment

### Pipeline Verification
Run full diagnostic:
```bash
python3 scripts/verify_deployment_pipeline.py
```

## Manual Deployment (If Needed)
```bash
./force_deployment.sh
```

## Timeline
- **0:00** - Push code to GitHub
- **0:05** - CodeBuild starts
- **1:00** - Docker image built
- **1:30** - Image pushed to ECR
- **2:00** - ECS service updated
- **3:00** - Old tasks draining
- **4:00** - New tasks running
- **5:00** - Deployment complete

## Success Indicators
- CodeBuild shows ✅ SUCCEEDED
- ECS shows new task definition number
- Health endpoint shows new version
- No manual intervention required

## Important Notes
- Always check CodeBuild logs if deployment fails
- ECS takes 2-3 minutes to fully update
- Version verification happens automatically
- Old containers gracefully drain connections