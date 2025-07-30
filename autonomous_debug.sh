#!/bin/bash
echo "🤖 AUTONOMOUS DEBUGGING STARTED"
date

# Test farmer registration API
echo -e "\n1. Testing farmer registration API..."
api_response=$(curl -s -X POST "https://6pmgrirjre.us-east-1.awsapprunner.com/api/register-farmer" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","manager_name":"Test","manager_last_name":"Farmer","wa_phone_number":"+1234567890","farm_name":"Test Farm","city":"Test City","country":"Test Country","fields":[{"name":"Test Field","size":1,"location":"45.815, 15.981"}]}')

echo "API Response: $api_response"

# Check if API returned error
if echo "$api_response" | grep -qE "500|error|json.*referenced.*before.*assignment|generator.*didn.*t.*stop"; then
    echo -e "\n❌ API failed - fetching AWS logs automatically..."
    
    # Get the latest log stream for monitoring-dashboards
    log_stream=$(aws logs describe-log-streams \
      --log-group-name "/aws/apprunner/ava-olo-monitoring-dashboards/a8cb4bde353646c396b10e6cd3ff290a/application" \
      --order-by LastEventTime \
      --descending \
      --limit 1 \
      --query 'logStreams[0].logStreamName' \
      --output text)
    
    echo "Latest log stream: $log_stream"
    
    # Get recent logs (last 5 minutes)
    aws logs filter-log-events \
      --log-group-name "/aws/apprunner/ava-olo-monitoring-dashboards/a8cb4bde353646c396b10e6cd3ff290a/application" \
      --log-stream-names "$log_stream" \
      --start-time $(date -d '5 minutes ago' +%s)000 \
      --output text > recent_logs.txt
    
    echo -e "\n📋 Recent logs retrieved. Analyzing..."
    
    # Show relevant error logs
    echo -e "\n🔍 Error logs found:"
    grep -E "ERROR|Exception|Traceback|json.*referenced|generator.*didn.*t.*stop|NameError.*logger" recent_logs.txt | tail -20
    
    # Check for specific errors
    if grep -q "json referenced before assignment" recent_logs.txt; then
        echo -e "\n🔧 JSON import error detected!"
        echo "The json import is already added to database_operations.py"
        echo "This might be a deployment delay issue."
    fi
    
    if grep -q "NameError.*logger.*not.*defined" recent_logs.txt; then
        echo -e "\n🔧 Logger import error detected!"
        echo "The logger import is already added to main.py"
        echo "This might be a deployment delay issue."
    fi
    
    if grep -q "generator didn't stop after throw()" recent_logs.txt; then
        echo -e "\n🔧 Generator error detected!"
        echo "The async/await fixes have been applied"
        echo "This might be a deployment delay issue."
    fi
    
    # Get deployment status
    echo -e "\n📊 Checking deployment status..."
    aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='ava-olo-monitoring-dashboards']" --output table
    
else
    echo -e "\n✅ API working correctly!"
    echo "Response indicates success: $api_response"
fi

# Test database connection separately
echo -e "\n2. Testing database health endpoint..."
db_health=$(curl -s "https://6pmgrirjre.us-east-1.awsapprunner.com/health/database")
echo "Database health: $db_health"

# Test Google Maps configuration
echo -e "\n3. Testing Google Maps health endpoint..."
maps_health=$(curl -s "https://6pmgrirjre.us-east-1.awsapprunner.com/health/google-maps")
echo "Google Maps health: $maps_health"

echo -e "\n🤖 AUTONOMOUS DEBUGGING COMPLETED"