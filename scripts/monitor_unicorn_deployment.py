#!/usr/bin/env python3
"""Monitor the unicorn deployment"""
import subprocess
import json
import time
from datetime import datetime

def check_deployment():
    """Check if unicorn deployment is working"""
    print(f"\n🦄 UNICORN DEPLOYMENT MONITOR - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Check ECS status
    cmd = "aws ecs describe-services --cluster ava-olo-production --services agricultural-core --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        services = json.loads(result.stdout)
        for service in services.get('services', []):
            print(f"Tasks Running: {service.get('runningCount')}/{service.get('desiredCount')}")
            
            for deployment in service.get('deployments', []):
                if deployment.get('status') == 'PRIMARY':
                    td = deployment.get('taskDefinition', '').split('/')[-1]
                    print(f"Primary Deployment: {td}")
    
    # Check endpoints
    print("\n🔍 Checking endpoints for unicorn...")
    
    endpoints = [
        ("Root", "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"),
        ("Version", "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version")
    ]
    
    for name, url in endpoints:
        print(f"\n{name}: {url}")
        cmd = f"curl -s {url} | head -20"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "UNICORN" in result.stdout or "🦄" in result.stdout:
            print("🦄 ✅ UNICORN FOUND! Deployment successful!")
            print("First 200 chars:", result.stdout[:200])
            return True
        elif "3.3.20" in result.stdout:
            print("❌ Still showing v3.3.20")
        elif "3.3.24" in result.stdout:
            print("✅ Shows v3.3.24 but no unicorn yet")
        else:
            print("⏳ No version info yet")
    
    return False

def main():
    print("🦄 MONITORING UNICORN DEPLOYMENT")
    print("Will check every 30 seconds for 5 minutes")
    print("If you see a unicorn, deployment worked!")
    
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    while time.time() - start_time < timeout:
        if check_deployment():
            print("\n\n🎉 SUCCESS! UNICORN DEPLOYMENT COMPLETE!")
            print("Visit: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com")
            break
        
        print("\n⏳ Waiting 30 seconds before next check...")
        time.sleep(30)
    else:
        print("\n\n❌ TIMEOUT: No unicorn found after 5 minutes")
        print("Check deployment logs for issues")

if __name__ == "__main__":
    main()