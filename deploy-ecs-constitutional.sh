#!/bin/bash
# ECS Deployment Script (without Docker build)
# Run this after Docker images are built and pushed

set -e

echo "🚀 Deploying Constitutional Design System to ECS"

AWS_REGION="us-east-1"

# Step 1: Register new task definitions
echo "📝 Registering new task definitions..."

# Register agricultural task
echo "Registering agricultural task definition..."
aws ecs register-task-definition \
    --cli-input-json file://task-definition-agricultural-constitutional.json \
    --region ${AWS_REGION}

# Register monitoring task  
echo "Registering monitoring task definition..."
aws ecs register-task-definition \
    --cli-input-json file://task-definition-monitoring-constitutional.json \
    --region ${AWS_REGION}

# Step 2: Update services with new task definitions
echo "🔄 Updating ECS services..."

# Update agricultural service
echo "Updating agricultural service..."
aws ecs update-service \
    --cluster ava-olo-production \
    --service agricultural-core \
    --task-definition ava-agricultural-task \
    --force-new-deployment \
    --region ${AWS_REGION}

# Update monitoring service
echo "Updating monitoring service..."
aws ecs update-service \
    --cluster ava-olo-production \
    --service monitoring-dashboards \
    --task-definition ava-monitoring-task \
    --force-new-deployment \
    --region ${AWS_REGION}

echo "✅ Task definitions registered and services updated!"
echo ""
echo "📊 Deployment Status:"
echo "- Agricultural Service: Updating..."
echo "- Monitoring Service: Updating..."
echo ""
echo "🔍 Monitor deployment progress:"
echo "aws ecs describe-services --cluster ava-olo-production --services agricultural-core monitoring-dashboards --region ${AWS_REGION}"
echo ""
echo "🌾 Constitutional Design System deployment initiated!"