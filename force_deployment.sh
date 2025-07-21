#!/bin/bash

echo "🚀 Forcing new deployment of agricultural-core service..."

# Force new deployment
aws ecs update-service \
  --cluster ava-olo-production \
  --service agricultural-core \
  --force-new-deployment \
  --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Deployment initiated successfully!"
    echo "⏳ Waiting for service to stabilize (this may take 2-3 minutes)..."
    
    # Wait for service to be stable
    aws ecs wait services-stable \
      --cluster ava-olo-production \
      --services agricultural-core \
      --region us-east-1
    
    echo "✅ Service is stable!"
    echo "🔍 Check version at: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
else
    echo "❌ Failed to initiate deployment"
fi