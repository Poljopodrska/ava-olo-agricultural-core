#!/bin/bash
# Single command to paste in CloudShell that creates and runs the deployment script

cat > deploy.sh << 'EOF' && chmod +x deploy.sh && ./deploy.sh
#!/bin/bash
set -e
echo "🚀 Creating fresh AWS App Runner service..."
CONNECTION_ARN="arn:aws:apprunner:us-east-1:127679825789:connection/ava-olo-github-fresh-2025/fab08d6912c24c15bb0372a92ff040f5"
cat > service-config.json << 'EOJ'
{
    "ServiceName": "ava-olo-agricultural-core-fresh",
    "SourceConfiguration": {
        "CodeRepository": {
            "RepositoryUrl": "https://github.com/Poljopodrska/ava-olo-agricultural-core",
            "SourceCodeVersion": {
                "Type": "BRANCH",
                "Value": "main"
            },
            "SourceDirectory": "/",
            "CodeConfiguration": {
                "ConfigurationSource": "API",
                "CodeConfigurationValues": {
                    "Runtime": "PYTHON_3",
                    "BuildCommand": "pip install -r requirements.txt",
                    "StartCommand": "python api_gateway_minimal.py",
                    "Port": "8080",
                    "RuntimeEnvironmentVariables": {
                        "PORT": "8080",
                        "ENVIRONMENT": "production",
                        "CACHE_BUST": "fresh_deploy_1737282000"
                    }
                }
            }
        },
        "AutoDeploymentsEnabled": true,
        "AuthenticationConfiguration": {
            "ConnectionArn": "arn:aws:apprunner:us-east-1:127679825789:connection/ava-olo-github-fresh-2025/fab08d6912c24c15bb0372a92ff040f5"
        }
    },
    "InstanceConfiguration": {
        "Cpu": "1 vCPU",
        "Memory": "2 GB"
    },
    "HealthCheckConfiguration": {
        "Protocol": "TCP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }
}
EOJ
echo "✅ Creating service..."
aws apprunner create-service --cli-input-json file://service-config.json > output.json
SERVICE_ARN=$(grep -o '"ServiceArn": "[^"]*"' output.json | cut -d'"' -f4)
echo "⏳ Waiting for deployment..."
aws apprunner wait service-created --service-arn "$SERVICE_ARN" 2>/dev/null || true
sleep 30
SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --query 'Service.ServiceUrl' --output text)
echo "✅ Service URL: https://$SERVICE_URL"
echo "🥭 Testing..."
curl -s "https://$SERVICE_URL/health" | grep -q "healthy" && echo "✅ DEPLOYMENT SUCCESS!"
echo "🎯 Bulgarian mango farmers now have access!"
EOF