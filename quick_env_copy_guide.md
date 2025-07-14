# 🚀 Quick Environment Variable Copy Guide

## Method 1: AWS Console (Easiest - 2 minutes)

1. **Open both services in separate browser tabs:**
   - Tab 1: https://console.aws.amazon.com/apprunner → `ava-olo-monitoring-dashboards` → Configuration
   - Tab 2: https://console.aws.amazon.com/apprunner → `ava-olo-agricultural-core` → Configuration

2. **In Tab 1 (monitoring-dashboards):**
   - Click "Edit" next to Environment Variables
   - Select all text in the environment variables section
   - Copy (Ctrl+C)

3. **In Tab 2 (agricultural-core):**
   - Click "Edit" next to Environment Variables  
   - Paste (Ctrl+V)
   - Click "Save and deploy"

## Method 2: Export/Import via .env file

1. **Export from working service:**
```bash
# If you have access to the running monitoring-dashboards container
docker exec -it <container-id> env > exported.env

# Or manually create from AWS Console
cat > exported.env << 'EOF'
DB_HOST=farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=farmer_crm
DB_USER=farmer_admin
DB_PASSWORD=<your-password>
OPENAI_API_KEY=sk-proj-VvvP2QQi47mwoPv6...
ENABLE_LLM_FIRST=true
ENABLE_COUNTRY_LOCALIZATION=true
EOF
```

2. **Format for AWS App Runner:**
```bash
# Convert .env to JSON format
python3 -c "
import json
env_vars = {}
with open('exported.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            env_vars[key] = value
print(json.dumps(env_vars, indent=2))
" > env_vars.json
```

## Method 3: AWS CLI (Automated)

```bash
# Install AWS CLI if not present
pip install awscli

# Configure AWS credentials
aws configure

# List services to get ARNs
aws apprunner list-services

# Get env vars from source service
SOURCE_ARN="arn:aws:apprunner:region:account:service/ava-olo-monitoring-dashboards/xxxxx"
aws apprunner describe-service --service-arn $SOURCE_ARN \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  > source_env.json

# Update target service (check AWS docs for exact format)
TARGET_ARN="arn:aws:apprunner:region:account:service/ava-olo-agricultural-core/xxxxx"
```

## Method 4: Create Shared Configuration

Create a shared environment configuration that both services can use:

```bash
# shared_env_config.json
{
  "RuntimeEnvironmentVariables": {
    "DB_HOST": "farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com",
    "DB_PORT": "5432",
    "DB_NAME": "farmer_crm",
    "DB_USER": "farmer_admin",
    "DB_PASSWORD": "<your-password>",
    "OPENAI_API_KEY": "sk-proj-VvvP2QQi47mwoPv6...",
    "ENABLE_LLM_FIRST": "true",
    "ENABLE_COUNTRY_LOCALIZATION": "true",
    "ENABLE_CONSTITUTIONAL_CHECKS": "true"
  }
}
```

## 🎯 Quickest Method: Browser Copy-Paste

**Time: 2 minutes**

1. Open AWS Console
2. Navigate to App Runner
3. Open `ava-olo-monitoring-dashboards` → Configuration → Environment Variables
4. Click "Edit"
5. Select all environment variables text
6. Copy
7. Open `ava-olo-agricultural-core` → Configuration → Environment Variables  
8. Click "Edit"
9. Paste
10. Save and deploy

The service will automatically redeploy with the new environment variables! 🚀