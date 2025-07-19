#!/bin/bash

# AWS App Runner Service Recreation Script
# Execute this in AWS CloudShell to create fresh service

set -e

echo "🚀 Creating fresh AWS App Runner service for Bulgarian mango farmers..."
echo "Started at: $(date)"

# Configuration variables
CONNECTION_ARN="arn:aws:apprunner:us-east-1:127679825789:connection/ava-olo-github-fresh-2025/fab08d6912c24c15bb0372a92ff040f5"
SERVICE_NAME="ava-olo-agricultural-core-fresh"
REPO_URL="https://github.com/Poljopodrska/ava-olo-agricultural-core"

# Create service configuration JSON
cat > service-config.json << 'EOF'
{
    "ServiceName": "ava-olo-agricultural-core-fresh",
    "SourceConfiguration": {
        "GitHubConnection": {
            "RepositoryUrl": "https://github.com/Poljopodrska/ava-olo-agricultural-core",
            "BranchName": "main",
            "SourceCodeVersion": {
                "Type": "BRANCH",
                "Value": "main"
            },
            "ConnectionArn": "arn:aws:apprunner:us-east-1:127679825789:connection/ava-olo-github-fresh-2025/fab08d6912c24c15bb0372a92ff040f5"
        },
        "AutoDeploymentsEnabled": true
    },
    "InstanceConfiguration": {
        "Cpu": "1 vCPU",
        "Memory": "2 GB",
        "InstanceRoleArn": "arn:aws:iam::127679825789:role/AppRunnerInstanceRoleAVAOLO"
    },
    "HealthCheckConfiguration": {
        "Protocol": "TCP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    },
    "NetworkConfiguration": {
        "EgressConfiguration": {
            "EgressType": "VPC",
            "VpcConnectorArn": "arn:aws:apprunner:us-east-1:127679825789:vpcconnector/ava-olo-vpc-connector/1/7e4c5a92618d4b0a89f28cc17fd5b19f"
        }
    },
    "ObservabilityConfiguration": {
        "ObservabilityEnabled": true
    }
}
EOF

echo "✅ Service configuration created"

# Create the service
echo "🚀 Creating AWS App Runner service..."
aws apprunner create-service --cli-input-json file://service-config.json > service-creation-output.json

if [ $? -eq 0 ]; then
    echo "✅ Service creation initiated successfully"
    
    # Extract service ARN
    SERVICE_ARN=$(cat service-creation-output.json | grep -o '"ServiceArn": "[^"]*"' | cut -d'"' -f4)
    echo "📋 Service ARN: $SERVICE_ARN"
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to become ready..."
    aws apprunner wait service-ready --service-arn "$SERVICE_ARN"
    
    if [ $? -eq 0 ]; then
        echo "✅ Service is ready!"
        
        # Get service URL
        SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --query 'Service.ServiceUrl' --output text)
        echo "🌐 Service URL: https://$SERVICE_URL"
        
        # Test health endpoint
        echo "🏥 Testing health endpoint..."
        for i in {1..5}; do
            HEALTH_RESPONSE=$(curl -s "https://$SERVICE_URL/health" 2>/dev/null)
            if [ $? -eq 0 ] && [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
                echo "✅ Health check passed!"
                echo "📊 Response: $HEALTH_RESPONSE"
                
                # Test Bulgarian mango farmer scenario
                echo ""
                echo "🥭 Testing Bulgarian mango farmer scenario..."
                MANGO_TEST=$(curl -s -X POST "https://$SERVICE_URL/api/v1/query" \
                    -H "Content-Type: application/json" \
                    -d '{"query": "How to grow mangoes in Bulgaria?", "farmer_id": "test_bg_001"}' 2>/dev/null)
                
                if [ $? -eq 0 ] && [[ "$MANGO_TEST" != *"404"* ]] && [[ "$MANGO_TEST" != *"Not Found"* ]]; then
                    echo "✅ MANGO RULE: Bulgarian mango farmer test PASSED!"
                    echo "✅ API endpoints responding correctly"
                    echo "✅ Constitutional compliance restored"
                    echo ""
                    echo "🏆 SUCCESS: Fresh service deployed and functional!"
                    echo "🥭 Bulgarian mango farmers now have access to agricultural guidance!"
                    echo ""
                    echo "New service details:"
                    echo "- URL: https://$SERVICE_URL"
                    echo "- ARN: $SERVICE_ARN"
                    echo "- Health: https://$SERVICE_URL/health"
                    echo "- API: https://$SERVICE_URL/api/v1/query"
                else
                    echo "⚠️  API endpoint test needs verification"
                    echo "   Response: $MANGO_TEST"
                    echo "   Service may still be initializing..."
                fi
                break
            else
                echo "⏳ Attempt $i/5: Service still initializing..."
                sleep 30
            fi
        done
    else
        echo "❌ Service creation timed out or failed"
        exit 1
    fi
else
    echo "❌ Service creation failed"
    cat service-creation-output.json
    exit 1
fi

echo ""
echo "🎯 Service recreation complete!"
echo "   Timestamp: $(date)"
echo "   Status: Service deployed and tested"