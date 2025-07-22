#!/bin/bash

echo "🚀 Manually triggering CodeBuild for agricultural-core..."

# Start a build
BUILD_ID=$(aws codebuild start-build \
  --project-name ava-olo-agricultural-core \
  --region us-east-1 \
  --query 'build.id' \
  --output text)

if [ $? -eq 0 ]; then
    echo "✅ Build started: $BUILD_ID"
    echo ""
    echo "Monitor build progress:"
    echo "https://console.aws.amazon.com/codesuite/codebuild/projects/ava-olo-agricultural-core/build/$BUILD_ID"
    echo ""
    echo "Or watch logs:"
    echo "aws logs tail /aws/codebuild/ava-olo-agricultural-core --follow"
else
    echo "❌ Failed to start build"
    echo "Checking if project exists..."
    aws codebuild list-projects --region us-east-1 | grep agricultural
fi