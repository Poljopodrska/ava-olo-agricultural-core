# Deployment Check for v3.3.21

## Why you might still see v3.3.20

The code has been successfully pushed to GitHub, but the ECS service needs to be updated to use the new code. Here's what to check:

### 1. Check Current ECS Task Status
```bash
aws ecs describe-services \
  --cluster ava-olo-production \
  --services agricultural-core \
  --region us-east-1 \
  --query "services[0].deployments[*].[status,taskDefinition,desiredCount,runningCount]" \
  --output table
```

### 2. Force New Deployment
To deploy the latest code from GitHub:

```bash
# Force a new deployment to pull latest code
aws ecs update-service \
  --cluster ava-olo-production \
  --service agricultural-core \
  --force-new-deployment \
  --region us-east-1
```

### 3. Alternative: Update via Console
1. Go to: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ava-olo-production/services
2. Click on `agricultural-core` service
3. Click "Update" button
4. Check "Force new deployment"
5. Click "Update Service"

### 4. Monitor Deployment
Watch the deployment progress:
```bash
aws ecs wait services-stable \
  --cluster ava-olo-production \
  --services agricultural-core \
  --region us-east-1
```

### 5. Verify Version After Deployment
Once the new tasks are running (2-3 minutes), check:
- http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health
- The dashboard should show v3.3.21-services-verified

## Quick Troubleshooting

### If still showing v3.3.20:
1. **Check container logs** in ECS console for any startup errors
2. **Verify GitHub webhook** triggered the deployment
3. **Check task definition** has correct image tag
4. **Ensure health checks** are passing

### Manual Container Restart
If needed, you can manually stop tasks to force new ones:
```bash
# Get running task ARNs
aws ecs list-tasks \
  --cluster ava-olo-production \
  --service-name agricultural-core \
  --region us-east-1

# Stop each task (ECS will start new ones automatically)
aws ecs stop-task \
  --cluster ava-olo-production \
  --task <TASK_ARN> \
  --region us-east-1
```

## Expected Timeline
- Force new deployment: ~30 seconds
- Old tasks draining: ~1-2 minutes  
- New tasks starting: ~30 seconds
- Health checks passing: ~30 seconds
- **Total: ~2-3 minutes**

## Version Confirmation Endpoints
After deployment completes, verify at:
- `/` - Homepage should show v3.3.21
- `/api/v1/system/health` - Full health check
- `/api/v1/system/debug/services` - Detailed debug info