# AVA OLO Monitoring Dashboards - Deployment Instructions

## 🚨 CRITICAL: OpenAI API Key Required

**CHAT SERVICE WILL BE UNAVAILABLE** without proper OpenAI configuration. This is the **primary cause** of "unavailable" errors.

## Environment Variables Required

Set these environment variables in AWS ECS:

```bash
# OpenAI Configuration (CRITICAL for chat service)
OPENAI_API_KEY=sk-your-actual-openai-key-here  # REQUIRED for chat functionality

# Database Configuration
DB_HOST=farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
DB_NAME=farmer_crm
DB_USER=postgres
DB_PASSWORD=<ACTUAL_RDS_PASSWORD_HERE>  # IMPORTANT: Use the actual RDS password!
DB_PORT=5432

# NOTE: The password shown in debug output (%3C~Xzntr2r~m6-7%29~4%2AMO%2...) 
# decodes to something like: <~Xzntr2r~m6-7)~4*MO*...
# This appears to be different from what was documented previously

# Google Maps API
GOOGLE_MAPS_API_KEY=AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo  # CORRECT WORKING KEY!
```

## 🔑 CRITICAL: Adding OpenAI API Key to ECS

**MANDATORY STEP** - The chat service will show "unavailable" without this:

### Via AWS Console:
1. Go to AWS ECS Console: https://console.aws.amazon.com/ecs/
2. Find your task definition (e.g., `ava-agricultural-task`)
3. Click "Create new revision"
4. In "Environment variables" section, add:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-proj-your-actual-key-here` (starts with `sk-`)
5. Save and update your ECS service to use the new revision

### Via AWS CLI:
```bash
# Update ECS task definition with OpenAI key
aws ecs describe-task-definition --task-definition ava-agricultural-task --query 'taskDefinition' > task-def.json
# Edit task-def.json to add OPENAI_API_KEY environment variable
aws ecs register-task-definition --cli-input-json file://task-def.json
aws ecs update-service --cluster your-cluster --service your-service --task-definition ava-agricultural-task:NEW_REVISION
```

## Pre-Deployment Checklist

1. **🔑 OpenAI API Key**: MUST be added to ECS environment variables (see above)
2. **Environment Variables**: Ensure all environment variables above are set in AWS ECS
3. **RDS Security Group**: Verify the RDS security group allows connections from ECS IP range (172.31.96.0/24)
4. **SSL Mode**: The application is configured to use SSL for RDS connections automatically

## Deployment Steps

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **AWS ECS**: The service should automatically deploy from the GitHub repository

3. **Verify Deployment**:
   - Check `/` - Home page should load
   - Check `/database-dashboard` - Should show farmers list
   - Check `/farmer-registration` - Should show registration form with working Google Maps
   - Check `/debug/database-connection` - Should show successful connection
   - **🔑 NEW: Check `/chat-debug-audit`** - Should show "Chat Service Available" not "Unavailable"
   - **🧠 NEW: Run behavioral audit** - Should achieve >80% score (especially Bulgarian Mango Test)

## Known Issues and Solutions

### Issue: Database Authentication Failed
**Solution**: 
1. The password contains special characters that need URL encoding. The application handles this automatically.
2. **IMPORTANT**: If you see `%3C` in the password (which is `<`), the password might be getting HTML-encoded by AWS. 
   - Make sure to enter the password in AWS ECS exactly as: `2hpzvrg_xP~qNbz1[_NppSK$e*O1`
   - Do NOT use quotes around the password in AWS ECS environment variables
   - If the password still fails, try using the debug endpoint `/debug/test-password-encoding` to see what's being received

### Issue: Google Maps Not Loading
**Solution**: 
1. Verify GOOGLE_MAPS_API_KEY is set in environment
2. Check that the API key has Maps JavaScript API enabled in Google Cloud Console
3. The application will show a fallback message if the key is missing

### Issue: Connection Timeout to RDS
**Solution**:
1. Check RDS security group has inbound rule for ECS IP range
2. Verify RDS instance is publicly accessible if connecting from outside VPC
3. Ensure SSL mode is set to 'require' (handled automatically)

## Debug Endpoints

Once deployed, you can check these endpoints:

- `/debug/database-connection` - Shows database connection status
- `/api/debug/status` - Shows application status
- `/health/database` - Database health check

## Local Development

For local development, you cannot connect to AWS RDS from outside the VPC. Options:
1. Use SSH tunnel through a bastion host
2. Use VPN connection to AWS VPC
3. Use a local PostgreSQL instance for development

## Running Locally (with proper network access)

```bash
# Use the provided script
bash run_with_env.sh

# Or set environment variables manually
export DB_HOST="farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
export DB_NAME="farmer_crm"
export DB_USER="postgres"
export DB_PASSWORD='2hpzvrg_xP~qNbz1[_NppSK$e*O1'
export DB_PORT="5432"
export GOOGLE_MAPS_API_KEY="AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo"

python3 main.py
```

## Post-Deployment Testing

Run `test_deployment.py` from within the AWS environment to verify all connections:

```bash
python3 test_deployment.py
```

This will test:
- Environment variable configuration
- Database connectivity
- Google Maps API configuration

## Important Security Notes

1. Never commit credentials to version control
2. Use AWS Secrets Manager for production credentials
3. Rotate database passwords regularly
4. Monitor access logs for suspicious activity