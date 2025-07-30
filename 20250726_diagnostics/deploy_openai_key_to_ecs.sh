#!/bin/bash
# Deploy OpenAI API Key to ECS Task Definition
# This script updates the ECS task definition with the OpenAI API key

set -e

echo "🔧 Updating ECS Task Definition with OpenAI API Key..."
echo "=================================================="

# Get the OpenAI key from .env.production
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env.production | cut -d'=' -f2)

if [ -z "$OPENAI_KEY" ]; then
    echo "❌ ERROR: OpenAI API key not found in .env.production"
    exit 1
fi

echo "✅ Found OpenAI API key (first 10 chars): ${OPENAI_KEY:0:10}..."

# Get current task definition
echo "📥 Fetching current task definition..."
TASK_FAMILY="ava-agricultural-task"
CURRENT_TASK_DEF=$(aws ecs describe-task-definition --task-definition $TASK_FAMILY --region us-east-1)

# Extract the task definition JSON and clean it
echo "🔧 Preparing new task definition..."
NEW_TASK_DEF=$(echo $CURRENT_TASK_DEF | jq '.taskDefinition | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')

# Check if OPENAI_API_KEY already exists
if echo "$NEW_TASK_DEF" | jq -e '.containerDefinitions[0].environment[] | select(.name == "OPENAI_API_KEY")' > /dev/null 2>&1; then
    echo "⚠️  OPENAI_API_KEY already exists, updating value..."
    NEW_TASK_DEF=$(echo "$NEW_TASK_DEF" | jq --arg key "$OPENAI_KEY" '(.containerDefinitions[0].environment[] | select(.name == "OPENAI_API_KEY")).value = $key')
else
    echo "➕ Adding OPENAI_API_KEY to environment variables..."
    NEW_TASK_DEF=$(echo "$NEW_TASK_DEF" | jq --arg key "$OPENAI_KEY" '.containerDefinitions[0].environment += [{"name": "OPENAI_API_KEY", "value": $key}]')
fi

# Save the new task definition to a file
echo "$NEW_TASK_DEF" > /tmp/new-task-def.json

# Register the new task definition
echo "📤 Registering new task definition..."
REGISTER_OUTPUT=$(aws ecs register-task-definition --cli-input-json file:///tmp/new-task-def.json --region us-east-1)
NEW_REVISION=$(echo $REGISTER_OUTPUT | jq -r '.taskDefinition.revision')

echo "✅ New task definition registered: $TASK_FAMILY:$NEW_REVISION"

# Update the service
echo "🚀 Updating ECS service..."
SERVICE_NAME="ava-olo-agricultural-core"
CLUSTER_NAME="ava-olo-cluster"

UPDATE_OUTPUT=$(aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_FAMILY:$NEW_REVISION \
    --force-new-deployment \
    --region us-east-1)

if [ $? -eq 0 ]; then
    echo "✅ Service update initiated successfully!"
    echo ""
    echo "📊 Deployment Status:"
    echo "- Cluster: $CLUSTER_NAME"
    echo "- Service: $SERVICE_NAME"
    echo "- New Task Definition: $TASK_FAMILY:$NEW_REVISION"
    echo "- Deployment: STARTED"
    echo ""
    echo "⏳ Deployment will take 2-3 minutes to complete."
    echo ""
    echo "🧪 To verify after deployment:"
    echo "curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/registration/llm-status"
    echo ""
    echo "Should show: \"openai_key_exists\": true"
else
    echo "❌ Failed to update service"
    exit 1
fi

# Clean up
rm -f /tmp/new-task-def.json

echo ""
echo "🎉 OpenAI API Key deployment initiated!"