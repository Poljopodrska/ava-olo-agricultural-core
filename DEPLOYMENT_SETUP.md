# Deployment Setup Instructions

## GitHub Actions Deployment Configuration

The GitHub Actions workflows are now properly configured, but the deployments are failing due to missing AWS credentials. To complete the setup, you need to add the following secrets to this repository.

### Required GitHub Secrets

Add these secrets to the `ava-olo-agricultural-core` repository:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key ID for the deployment user
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret access key for the deployment user

### How to Add Secrets

1. Go to the repository on GitHub
2. Click on "Settings" tab
3. Navigate to "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Add each secret with its corresponding value

### AWS Permissions Required

The AWS credentials should have permissions to:
- Push images to ECR repository
- Update ECS task definitions
- Deploy to ECS services
- Access CloudWatch logs

### Verification

After adding the secrets, the deployments should automatically succeed on the next push to the main branch. You can manually trigger a deployment by:
1. Making a small change to any file
2. Pushing to the main branch
3. Monitoring the Actions tab for deployment status

## Current Infrastructure

- **ECS Cluster**: ava-olo-production
- **Service**: agricultural-core
- **Container**: agricultural-core
- **ALB Endpoint**: https://ava-olo-65365776.us-east-1.elb.amazonaws.com/