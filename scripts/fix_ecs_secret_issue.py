#!/usr/bin/env python3
"""Fix ECS secret issue by reverting to working task definition"""
import subprocess
import json
import time

def fix_secret_issue():
    print("🔧 FIXING ECS SECRET ISSUE")
    print("=" * 60)
    
    # Update service to use task definition 5 which was working
    print("\n1️⃣ Reverting to working task definition 5...")
    cmd = """aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --task-definition ava-agricultural-task:5 \
        --force-new-deployment \
        --desired-count 1 \
        --region us-east-1"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Service updated to use task definition 5")
    else:
        print(f"   ❌ Error: {result.stderr}")
        return False
    
    # Wait for deployment
    print("\n2️⃣ Waiting for deployment...")
    for i in range(6):  # Check for 1 minute
        time.sleep(10)
        
        cmd = "aws ecs describe-services --cluster ava-olo-production --services agricultural-core --region us-east-1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            for service in services.get('services', []):
                running = service.get('runningCount', 0)
                desired = service.get('desiredCount', 0)
                print(f"   Check {i+1}/6: Running {running}/{desired} tasks")
                
                if running >= desired and running > 0:
                    print("\n   ✅ Tasks are running!")
                    return True
    
    return False

def check_version_after_fix():
    """Check if the service is running after fix"""
    print("\n3️⃣ Checking service version...")
    time.sleep(5)
    
    endpoints = [
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com",
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version"
    ]
    
    for endpoint in endpoints:
        print(f"\nChecking: {endpoint}")
        cmd = f"curl -s {endpoint} | head -10"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            if "502 Bad Gateway" not in result.stdout:
                print("   ✅ Service is responding!")
                if "3.3.20" in result.stdout:
                    print("   📌 Running v3.3.20 (old version but working)")
                elif "UNICORN" in result.stdout or "🦄" in result.stdout:
                    print("   🦄 UNICORN TEST FOUND! (unexpected but good!)")
            else:
                print("   ⏳ Still getting 502...")

def main():
    if fix_secret_issue():
        check_version_after_fix()
        
        print("\n\n📋 NEXT STEPS:")
        print("=" * 60)
        print("1. Service is now running with task definition 5 (v3.3.20)")
        print("2. To deploy v3.3.24 with unicorn test:")
        print("   - Fix the secret issue in task definition")
        print("   - Or create a new task definition without secrets")
        print("3. The code changes are ready, just need working task definition")
    else:
        print("\n❌ Failed to fix the issue")

if __name__ == "__main__":
    main()