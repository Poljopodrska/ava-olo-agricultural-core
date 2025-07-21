# Deployment Failure Root Cause Analysis Report
Date: 2025-07-21
Investigator: Claude Code

## Executive Summary
- **Success Rate**: ~50% (Manual intervention required)
- **Root Cause**: Dual pipeline confusion - GitHub Actions AND CodeBuild both exist
- **Primary Issue**: CodeBuild has no webhooks, requires manual triggering
- **Secondary Issue**: Docker images not containing latest code changes

## Key Findings

### 1. Two Competing Deployment Pipelines
- **GitHub Actions**: `.github/workflows/deploy-ecs.yml` exists in repo
- **AWS CodeBuild**: `ava-agricultural-docker-build` project configured
- **Problem**: No automatic connection between GitHub pushes and CodeBuild

### 2. CodeBuild Configuration Issues
```json
{
  "webhook": null,
  "triggers": null,
  "source": {
    "type": "GITHUB",
    "location": "https://github.com/Poljopodrska/ava-olo-agricultural-core.git"
  }
}
```
- No webhook configured
- No triggers configured
- Builds only run when manually triggered by user "AVA_OLO"

### 3. Deployment Timeline Analysis
```
10:05 UTC - Git push of v3.3.6 (commit 3fa04cb)
11:21 CEST - CodeBuild manually triggered (1h 16m delay)
11:22 CEST - Docker image pushed to ECR
11:25 CEST - ECS task updated with new image
11:30 CEST - Service still returning v3.3.5
```

### 4. Image Content Mismatch
- CodeBuild successfully built and pushed image at 11:22
- ECS deployed the new image (task definition 5)
- BUT: The image contains old v3.3.5 code, not v3.3.6

## Pattern Analysis

### Successful Deployments
- All had manual CodeBuild triggers
- User "AVA_OLO" initiated builds
- Timing varied based on when manual trigger occurred

### Failed Deployments
- Git pushes without manual CodeBuild trigger
- No automatic webhook to start builds
- Code sits in GitHub without being built

## Root Cause Hypothesis

### Primary Issue: No Automation
1. GitHub webhook not configured on CodeBuild
2. GitHub Actions workflow exists but may not have AWS credentials
3. Manual intervention required for every deployment

### Secondary Issue: Build Cache
1. CodeBuild may be using cached layers
2. Source code not being pulled fresh
3. Version numbers in config.py not being picked up

## Evidence of 50% Success Rate
- Recent commits show multiple version updates
- Only some versions appear in production
- Pattern: Deployments work when someone manually triggers CodeBuild

## Immediate Solution

### Option 1: Fix CodeBuild Webhook
```bash
aws codebuild create-webhook \
  --project-name ava-agricultural-docker-build \
  --filter-groups '[
    [{
      "type": "EVENT",
      "pattern": "PUSH",
      "excludeMatchedPattern": false
    },{
      "type": "HEAD_REF",
      "pattern": "^refs/heads/main$",
      "excludeMatchedPattern": false
    }]
  ]' \
  --region us-east-1
```

### Option 2: Use GitHub Actions
- Ensure AWS credentials are configured in GitHub secrets
- Remove CodeBuild dependency
- Let GitHub Actions handle everything

### Option 3: Force Fresh Builds
```yaml
# In buildspec.yml
pre_build:
  commands:
    - echo "Pulling latest code..."
    - git pull origin main
    - echo "Current version:"
    - grep VERSION modules/core/config.py
```

## Verification Steps
1. Configure webhook on CodeBuild
2. Make small commit to test
3. Monitor CodeBuild triggers automatically
4. Verify new version deploys
5. Repeat 10 times to ensure reliability

## Long-term Recommendations
1. Choose ONE deployment pipeline (not both)
2. Add deployment monitoring that alerts on failures
3. Implement the feature verification system fully
4. Add CloudWatch alarms for stuck deployments
5. Document the chosen pipeline clearly

## Metrics to Track
- Time from git push to deployment complete
- Success rate of automatic deployments
- Number of manual interventions required
- Version drift between GitHub and production