#!/bin/bash
# scripts/verify_ecr_image_version.sh

echo "🔍 Verifying ECR Image Version"
echo "=============================="

# 1. Check when the latest image was pushed
echo "Latest ECR image details:"
aws ecr describe-images \
  --repository-name ava-olo/agricultural-core \
  --image-ids imageTag=latest \
  --region us-east-1 \
  --query 'imageDetails[0].{pushedAt:imagePushedAt,digest:imageDigest}' \
  --output table

# 2. Get the image manifest to see what was built
echo -e "\nChecking image manifest..."
IMAGE_MANIFEST=$(aws ecr batch-get-image \
  --repository-name ava-olo/agricultural-core \
  --image-ids imageTag=latest \
  --region us-east-1 \
  --query 'images[0].imageManifest' \
  --output text)

echo "Image digest: $(echo $IMAGE_MANIFEST | grep -o '"digest":"[^"]*"' | head -1)"

# 3. Check if we can run the image locally to verify version
echo -e "\n🔐 Logging into ECR..."
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 127679825789.dkr.ecr.us-east-1.amazonaws.com

if [ $? -eq 0 ]; then
  echo "✅ ECR login successful"
  
  echo -e "\n📥 Pulling latest image..."
  docker pull 127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest
  
  if [ $? -eq 0 ]; then
    echo "✅ Image pulled successfully"
    
    echo -e "\n🔍 Checking version in image..."
    # Try to check the version file directly
    docker run --rm \
      127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest \
      python -c "
try:
    from modules.core.config import VERSION
    print(f'VERSION IN ECR IMAGE: {VERSION}')
except Exception as e:
    print(f'Error getting version: {e}')
    # Try alternative method
    try:
        import subprocess
        result = subprocess.run(['grep', '-r', 'VERSION.*3.3.26', '/app'], capture_output=True, text=True)
        if result.stdout:
            print('Found v3.3.26 references in image')
        else:
            print('No v3.3.26 references found in image')
    except:
        print('Could not verify version')
"
  else
    echo "❌ Failed to pull image"
  fi
else
  echo "❌ ECR login failed"
fi

echo -e "\n📋 Summary:"
echo "If the image shows v3.3.25 or errors, we need to rebuild"
echo "If the image shows v3.3.26, the issue is in task definition deployment"