#!/bin/bash
# Safe Diagnostic Script - Following Safety Protocol

echo "🛡️ SAFE DIAGNOSTIC MODE - Read-Only Operations"
echo "Safety Level: GREEN (Low Risk)"
date

# STEP 1: Validation - Check if our local code has the fix
echo -e "\n📋 Checking local code status..."
if grep -q "import json" database_operations.py; then
    echo "✅ Local database_operations.py has json import"
else
    echo "❌ Local database_operations.py missing json import"
fi

# STEP 2: Get deployment information
echo -e "\n📊 AWS Deployment Status:"
aws apprunner describe-service \
  --service-arn $(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='ava-olo-monitoring-dashboards'].ServiceArn" --output text) \
  --query '[ServiceName, Status, SourceConfiguration.CodeRepository.SourceCodeVersion.Value]' \
  --output table

# STEP 3: Check recent logs for the exact error
echo -e "\n🔍 Recent Error Analysis (last 10 minutes):"
aws logs filter-log-events \
  --log-group-name "/aws/apprunner/ava-olo-monitoring-dashboards/a8cb4bde353646c396b10e6cd3ff290a/application" \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --filter-pattern "json referenced before assignment" \
  --query 'events[*].[timestamp, message]' \
  --output text | tail -5

# STEP 4: Test current API status (read-only)
echo -e "\n🧪 API Health Check (non-destructive):"
curl -s "https://6pmgrirjre.us-east-1.awsapprunner.com/health/database" | jq '.' 2>/dev/null || echo "Database health check failed"

# STEP 5: Provide safe recommendation
echo -e "\n📋 SAFETY ASSESSMENT:"
echo "Risk Level: GREEN - Only diagnostic operations performed"
echo "No changes made to any systems"
echo -e "\n🎯 RECOMMENDATION:"
echo "The json import fix has been committed to GitHub but may not be deployed."
echo "Options:"
echo "1. Wait for automatic deployment to complete"
echo "2. Manually trigger deployment in AWS App Runner console"
echo "3. Check if deployment is configured to auto-deploy from GitHub"

echo -e "\n✅ Safe diagnostic complete - no changes made"