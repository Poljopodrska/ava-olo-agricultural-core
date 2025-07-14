#\!/bin/bash
# Copy environment variables from one AWS App Runner service to another

SOURCE_SERVICE="ava-olo-monitoring-dashboards"  # Service with working env vars
TARGET_SERVICE="ava-olo-agricultural-core"      # Service needing env vars

echo "📋 Copying environment variables from $SOURCE_SERVICE to $TARGET_SERVICE"

# Get the current configuration
SOURCE_ARN=$(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$SOURCE_SERVICE'].ServiceArn" --output text)
TARGET_ARN=$(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$TARGET_SERVICE'].ServiceArn" --output text)

echo "Source ARN: $SOURCE_ARN"
echo "Target ARN: $TARGET_ARN"

# Describe the source service to get env vars
aws apprunner describe-service --service-arn $SOURCE_ARN --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' > env_vars.json

echo "✅ Environment variables exported to env_vars.json"
echo "Now update the target service with these variables"

# Update target service (requires proper JSON formatting)
# aws apprunner update-service --service-arn $TARGET_ARN --source-configuration ...
