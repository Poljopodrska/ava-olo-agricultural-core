# 🚀 AWS CloudShell Service Recreation Guide

## Quick Execution in CloudShell

Copy and paste these commands directly into AWS CloudShell:

### Step 1: Copy the Script
```bash
cat > recreate-service.sh << 'EOF'
#!/bin/bash

set -e

echo "🚀 Creating fresh AWS App Runner service for Bulgarian mango farmers..."
echo "Started at: $(date)"

CONNECTION_ARN="arn:aws:apprunner:us-east-1:127679825789:connection/ava-olo-github-fresh-2025/fab08d6912c24c15bb0372a92ff040f5"
SERVICE_NAME="ava-olo-agricultural-core-fresh"

cat > service-config.json << 'EOJ'
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
EOJ

echo "✅ Service configuration created"

echo "🚀 Creating AWS App Runner service..."
aws apprunner create-service --cli-input-json file://service-config.json > service-creation-output.json

if [ $? -eq 0 ]; then
    echo "✅ Service creation initiated successfully"
    
    SERVICE_ARN=$(cat service-creation-output.json | grep -o '"ServiceArn": "[^"]*"' | cut -d'"' -f4)
    echo "📋 Service ARN: $SERVICE_ARN"
    
    echo "⏳ Waiting for service to become ready..."
    aws apprunner wait service-ready --service-arn "$SERVICE_ARN"
    
    if [ $? -eq 0 ]; then
        echo "✅ Service is ready!"
        
        SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --query 'Service.ServiceUrl' --output text)
        echo "🌐 Service URL: https://$SERVICE_URL"
        
        echo "🏥 Testing health endpoint..."
        for i in {1..5}; do
            HEALTH_RESPONSE=$(curl -s "https://$SERVICE_URL/health" 2>/dev/null)
            if [ $? -eq 0 ] && [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
                echo "✅ Health check passed!"
                echo "📊 Response: $HEALTH_RESPONSE"
                
                echo ""
                echo "🥭 Testing Bulgarian mango farmer scenario..."
                MANGO_TEST=$(curl -s -X POST "https://$SERVICE_URL/api/v1/query" \
                    -H "Content-Type: application/json" \
                    -d '{"query": "How to grow mangoes in Bulgaria?", "farmer_id": "test_bg_001"}' 2>/dev/null)
                
                if [ $? -eq 0 ] && [[ "$MANGO_TEST" != *"404"* ]]; then
                    echo "✅ MANGO RULE: Bulgarian mango farmer test PASSED!"
                    echo "🏆 SUCCESS: Fresh service deployed and functional!"
                    echo ""
                    echo "New service details:"
                    echo "- URL: https://$SERVICE_URL"
                    echo "- Health: https://$SERVICE_URL/health"
                else
                    echo "⚠️  API may still be initializing: $MANGO_TEST"
                fi
                break
            else
                echo "⏳ Attempt $i/5: Service initializing..."
                sleep 30
            fi
        done
    fi
fi

echo "🎯 Service recreation complete at $(date)"
EOF
```

### Step 2: Execute the Script
```bash
chmod +x recreate-service.sh && ./recreate-service.sh
```

## Expected Output

You should see:
1. ✅ Service configuration created
2. 🚀 Creating AWS App Runner service...
3. ✅ Service creation initiated successfully
4. ⏳ Waiting for service to become ready... (takes 2-5 minutes)
5. ✅ Service is ready!
6. 🌐 Service URL: https://[new-url].us-east-1.awsapprunner.com
7. ✅ Health check passed!
8. 🥭 Testing Bulgarian mango farmer scenario...
9. ✅ MANGO RULE: Bulgarian mango farmer test PASSED!
10. 🏆 SUCCESS: Fresh service deployed and functional!

## Troubleshooting

### If Service Creation Fails:
- Check that the CONNECTION_ARN is correct
- Verify IAM permissions for App Runner
- Ensure VPC connector ARN is valid

### If Health Check Fails:
- Service may still be starting (wait 2-3 minutes)
- Check AWS Console for deployment logs
- Verify repository has latest code

### If API Test Fails:
- Service may need more time to initialize
- Check if endpoints exist in latest code
- Verify constitutional routes are implemented

## Success Criteria

✅ Service created without errors  
✅ Health endpoint responds  
✅ New service URL generated  
✅ Bulgarian mango farmer test passes  
✅ Constitutional compliance restored  

Once complete, Bulgarian mango farmers will have access to the latest agricultural guidance system!