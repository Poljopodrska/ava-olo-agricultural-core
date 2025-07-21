#!/bin/bash
# Update ECS Task Definitions with Environment Variables
# Usage: ./scripts/update_ecs_env.sh

set -e

echo "=== ECS Environment Variables Update Script ==="
echo "This script will update both ECS task definitions with environment variables"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   Visit: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo "   Run: python3 scripts/recover_env_vars.py"
    exit 1
fi

# Check if jq is installed (needed for JSON processing)
if ! command -v jq &> /dev/null; then
    echo "❌ jq is not installed. Installing..."
    echo "   Run: sudo apt-get install jq (Linux) or brew install jq (Mac)"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Function to update a task definition
update_task_definition() {
    local TASK_NAME=$1
    local SERVICE_NAME=$2
    
    echo "📋 Updating $TASK_NAME..."
    
    # Get current task definition
    echo "  - Fetching current task definition..."
    TASK_DEF=$(aws ecs describe-task-definition --task-definition $TASK_NAME --region us-east-1 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo "  ❌ Failed to fetch task definition. Check AWS credentials."
        return 1
    fi
    
    # Extract container definitions
    CONTAINER_DEFS=$(echo $TASK_DEF | jq '.taskDefinition.containerDefinitions')
    
    # Read environment variables from ecs-env-vars.json
    if [ ! -f "ecs-env-vars.json" ]; then
        echo "  ❌ ecs-env-vars.json not found. Run recovery script first."
        return 1
    fi
    
    # Update container definitions with new environment variables
    UPDATED_CONTAINER_DEFS=$(echo $CONTAINER_DEFS | jq ".[0].environment = $(cat ecs-env-vars.json)")
    
    # Get other required fields from existing task definition
    FAMILY=$(echo $TASK_DEF | jq -r '.taskDefinition.family')
    TASK_ROLE=$(echo $TASK_DEF | jq -r '.taskDefinition.taskRoleArn // empty')
    EXECUTION_ROLE=$(echo $TASK_DEF | jq -r '.taskDefinition.executionRoleArn // empty')
    NETWORK_MODE=$(echo $TASK_DEF | jq -r '.taskDefinition.networkMode // "bridge"')
    CPU=$(echo $TASK_DEF | jq -r '.taskDefinition.cpu // "256"')
    MEMORY=$(echo $TASK_DEF | jq -r '.taskDefinition.memory // "512"')
    REQUIRES_COMPATIBILITIES=$(echo $TASK_DEF | jq -r '.taskDefinition.requiresCompatibilities[]' | tr '\n' ' ')
    
    # Create new task definition JSON
    cat > temp-task-def.json << EOF
{
    "family": "$FAMILY",
    "containerDefinitions": $UPDATED_CONTAINER_DEFS,
    "taskRoleArn": "$TASK_ROLE",
    "executionRoleArn": "$EXECUTION_ROLE",
    "networkMode": "$NETWORK_MODE",
    "cpu": "$CPU",
    "memory": "$MEMORY",
    "requiresCompatibilities": ["EC2"]
}
EOF
    
    # Register new task definition
    echo "  - Registering new task definition revision..."
    NEW_TASK_DEF=$(aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region us-east-1)
    
    if [ $? -eq 0 ]; then
        NEW_REVISION=$(echo $NEW_TASK_DEF | jq -r '.taskDefinition.revision')
        echo "  ✅ Created new revision: $FAMILY:$NEW_REVISION"
        
        # Update service if provided
        if [ ! -z "$SERVICE_NAME" ]; then
            echo "  - Updating service $SERVICE_NAME..."
            aws ecs update-service \
                --cluster ava-olo-cluster \
                --service $SERVICE_NAME \
                --task-definition $FAMILY:$NEW_REVISION \
                --region us-east-1 \
                > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo "  ✅ Service updated to use new task definition"
            else
                echo "  ⚠️  Failed to update service. Update manually in AWS console."
            fi
        fi
    else
        echo "  ❌ Failed to register new task definition"
        return 1
    fi
    
    # Clean up
    rm -f temp-task-def.json
    
    return 0
}

# Check current environment variables
echo "📊 Current environment variables in .env.production:"
echo "---------------------------------------------------"
grep -E "^[A-Z_]+=" .env.production | while read line; do
    KEY=$(echo $line | cut -d'=' -f1)
    VALUE=$(echo $line | cut -d'=' -f2-)
    
    # Mask sensitive values
    if [[ $KEY == *"PASSWORD"* ]] || [[ $KEY == *"KEY"* ]]; then
        if [[ $VALUE == *"REPLACE"* ]]; then
            echo "❌ $KEY=*** (NEEDS TO BE SET!)"
        else
            echo "✅ $KEY=*** (configured)"
        fi
    else
        echo "✅ $KEY=$VALUE"
    fi
done
echo ""

# Warn about missing values
if grep -q "REPLACE_WITH_YOUR_KEY" .env.production; then
    echo "⚠️  WARNING: Some values still need to be replaced!"
    echo "   Edit .env.production and replace placeholder values."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update both task definitions
echo "🚀 Starting ECS updates..."
echo ""

# Update agricultural-core
update_task_definition "ava-agricultural-task" "ava-agricultural-core"

echo ""

# Update monitoring-dashboards
update_task_definition "ava-monitoring-task" "ava-monitoring-dashboards"

echo ""
echo "=== SUMMARY ==="
echo "✅ Task definitions updated with environment variables"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Go to AWS ECS Console"
echo "2. Check both services are updating"
echo "3. Wait for services to stabilize (2-3 minutes)"
echo "4. Test endpoints:"
echo "   - http://ava-olo-farmers-alb-*.elb.amazonaws.com/api/v1/system/env-check"
echo "   - http://ava-olo-internal-alb-*.elb.amazonaws.com/api/v1/system/env-check"
echo ""
echo "✅ Script complete!"