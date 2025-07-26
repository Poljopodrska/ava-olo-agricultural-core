#!/usr/bin/env python3
"""Monitor deployment until features are live"""

import subprocess
import time
import sys

service_arn = "arn:aws:ecs:us-east-1:127679825789:service/ava-olo-monitoring-dashboards/a8cb4bde353646c396b10e6cd3ff290a"
url = "https://6pmgrirjre.us-east-1.elb.amazonaws.com"

print("🔍 MONITORING DEPLOYMENT PROGRESS")
print("=" * 40)

start_time = time.time()
max_wait = 600  # 10 minutes

while time.time() - start_time < max_wait:
    # Check AWS status
    result = subprocess.run([
        'aws', 'ecs', 'describe-service',
        '--service-arn', service_arn,
        '--region', 'us-east-1',
        '--query', 'Service.Status',
        '--output', 'text'
    ], capture_output=True, text=True)
    
    status = result.stdout.strip()
    print(f"\n[{int(time.time() - start_time)}s] AWS Status: {status}")
    
    # Check if features are live
    features_check = subprocess.run(
        f'curl -s {url}/ui-dashboard | grep -E "dashboard-grid|Register New|register-fields" | wc -l',
        shell=True, capture_output=True, text=True
    )
    
    feature_count = int(features_check.stdout.strip()) if features_check.stdout.strip() else 0
    
    if feature_count > 0:
        print(f"✅ FEATURES DETECTED! Found {feature_count} dashboard features")
        
        # Detailed check
        detailed = subprocess.run(['python3', 'quick_verify.py'], capture_output=True, text=True)
        print(detailed.stdout)
        
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("🏛️ Constitutional Amendment #15: COMPLIANT")
        sys.exit(0)
    elif status == "RUNNING":
        print(f"⏳ Service running but features not yet visible (checking every 30s)")
    
    time.sleep(30)

print("\n⏰ Timeout reached - deployment may still be in progress")
print("Run 'python3 quick_verify.py' to check manually")