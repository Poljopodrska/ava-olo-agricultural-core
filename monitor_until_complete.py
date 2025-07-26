#!/usr/bin/env python3
"""Monitor deployment until complete"""

import subprocess
import time
import sys
from datetime import datetime

service_arn = "arn:aws:ecs:us-east-1:127679825789:service/ava-olo-monitoring-dashboards/a8cb4bde353646c396b10e6cd3ff290a"
start_time = datetime.now()

print("🔄 MONITORING DEPLOYMENT STATUS")
print("=" * 40)
print(f"Started: {start_time.strftime('%H:%M:%S')}")
print("Checking every 30 seconds...\n")

previous_status = None
check_count = 0

while True:
    check_count += 1
    
    # Check AWS status
    result = subprocess.run([
        'aws', 'ecs', 'describe-service',
        '--service-arn', service_arn,
        '--region', 'us-east-1',
        '--query', 'Service.Status',
        '--output', 'text'
    ], capture_output=True, text=True)
    
    current_status = result.stdout.strip()
    current_time = datetime.now()
    elapsed = current_time - start_time
    
    # Only print if status changed or every 5 checks
    if current_status != previous_status or check_count % 5 == 0:
        print(f"[{current_time.strftime('%H:%M:%S')}] Status: {current_status} (elapsed: {str(elapsed).split('.')[0]})")
    
    if current_status == "RUNNING":
        print("\n✅ DEPLOYMENT COMPLETE!")
        print(f"Total time: {str(elapsed).split('.')[0]}")
        
        # Quick feature check
        import requests
        try:
            resp = requests.get("https://6pmgrirjre.us-east-1.elb.amazonaws.com/ui-dashboard", timeout=5)
            if resp.status_code == 200 and "dashboard-grid" in resp.text:
                print("✅ Dashboard features verified!")
            else:
                print("⚠️  Dashboard accessible but features need verification")
        except:
            print("⚠️  Could not verify features")
            
        break
    elif current_status == "OPERATION_IN_PROGRESS":
        previous_status = current_status
        time.sleep(30)
    else:
        print(f"\n❌ Unexpected status: {current_status}")
        break

print("\nDeployment monitoring complete.")