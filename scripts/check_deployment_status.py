#!/usr/bin/env python3
"""Check current deployment status"""
import subprocess
import json
import time

# Check ECS service status
print("🔍 CHECKING DEPLOYMENT STATUS...")
cmd = "aws ecs describe-services --cluster ava-olo-production --services agricultural-core --region us-east-1"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

if result.returncode == 0:
    services = json.loads(result.stdout)
    for service in services.get('services', []):
        print(f"\nService: {service['serviceName']}")
        print(f"Desired Count: {service.get('desiredCount')}")
        print(f"Running Count: {service.get('runningCount')}")
        
        print("\nDeployments:")
        for deployment in service.get('deployments', []):
            td = deployment.get('taskDefinition', '').split('/')[-1]
            print(f"  {deployment.get('status')}: {td} - Running: {deployment.get('runningCount')}/{deployment.get('desiredCount')}")

# Test endpoints
print("\n\n🔍 TESTING ENDPOINTS...")
endpoints = [
    "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com",
    "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health"
]

for endpoint in endpoints:
    print(f"\nChecking: {endpoint}")
    cmd = f"curl -s {endpoint} | grep -o 'v[0-9]\\.[0-9]\\.[0-9][^\"<]*' | head -1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"Version found: {result.stdout.strip()}")
    else:
        # Try alternative check
        cmd = f"curl -s {endpoint}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "3.3.20" in result.stdout:
            print("❌ Still showing v3.3.20!")
        elif "3.3.23" in result.stdout or "3.3.24" in result.stdout:
            print("✅ Updated to v3.3.23+!")
        else:
            print("No version info found")