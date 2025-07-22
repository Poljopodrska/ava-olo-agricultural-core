#!/usr/bin/env python3
"""
Force ECS to update to v23 by killing stuck deployment
"""
import subprocess
import json
import time
from datetime import datetime

def force_update_to_v23():
    """Nuclear option to force ECS to v23"""
    print("🚨 FORCING ECS UPDATE TO V23")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    
    # Step 1: Stop all running tasks
    print("\n1️⃣ STOPPING ALL RUNNING TASKS...")
    cmd = "aws ecs list-tasks --cluster ava-olo-production --service-name agricultural-core --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        tasks = json.loads(result.stdout)
        for task_arn in tasks.get('taskArns', []):
            print(f"   Stopping task: {task_arn.split('/')[-1]}")
            stop_cmd = f"aws ecs stop-task --cluster ava-olo-production --task {task_arn} --reason 'FORCE UPDATE TO V23' --region us-east-1"
            subprocess.run(stop_cmd, shell=True)
            time.sleep(2)
    
    print("   ✅ All tasks stopped")
    
    # Step 2: Force new deployment
    print("\n2️⃣ FORCING NEW DEPLOYMENT...")
    cmd = """aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --task-definition ava-agricultural-task:7 \
        --force-new-deployment \
        --desired-count 2 \
        --region us-east-1"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Forced new deployment with task definition 7")
    else:
        print(f"   ❌ Error: {result.stderr}")
    
    # Step 3: Scale down to 0 then back up
    print("\n3️⃣ SCALE DOWN/UP TRICK...")
    
    # Scale to 0
    print("   Scaling to 0...")
    cmd = """aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --desired-count 0 \
        --region us-east-1"""
    subprocess.run(cmd, shell=True)
    
    time.sleep(10)
    
    # Scale back to 2
    print("   Scaling back to 2...")
    cmd = """aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --desired-count 2 \
        --task-definition ava-agricultural-task:7 \
        --region us-east-1"""
    subprocess.run(cmd, shell=True)
    
    print("   ✅ Scale down/up complete")
    
    # Step 4: Monitor deployment
    print("\n4️⃣ MONITORING DEPLOYMENT...")
    for i in range(6):  # Check for 1 minute
        time.sleep(10)
        cmd = "aws ecs describe-services --cluster ava-olo-production --services agricultural-core --region us-east-1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            for service in services.get('services', []):
                print(f"\n   Check {i+1}/6:")
                for deployment in service.get('deployments', []):
                    print(f"   - {deployment.get('status')}: Task {deployment.get('taskDefinition', '').split('/')[-1]} - Running: {deployment.get('runningCount')}/{deployment.get('desiredCount')}")
                
                # Check if new deployment is complete
                primary = next((d for d in service.get('deployments', []) if d.get('status') == 'PRIMARY'), None)
                if primary and primary.get('runningCount') == primary.get('desiredCount'):
                    print("\n   ✅ NEW DEPLOYMENT COMPLETE!")
                    break
    
    # Step 5: Verify version
    print("\n5️⃣ VERIFYING VERSION...")
    time.sleep(5)
    
    endpoints = [
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com",
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health"
    ]
    
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint}")
        cmd = f"curl -s {endpoint} | grep -o 'v[0-9]\\.[0-9]\\.[0-9][^\"<]*' | head -1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            version = result.stdout.strip()
            print(f"   Found version: {version}")
            if "23" in version:
                print("   ✅ SUCCESS! V23 is now running!")
            else:
                print(f"   ❌ Still showing old version: {version}")

def main():
    force_update_to_v23()
    
    print("\n\n📋 NEXT STEPS:")
    print("=" * 60)
    print("1. Check http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com")
    print("2. If still showing v20, wait 2-3 minutes for ALB to update")
    print("3. Clear browser cache and try again")
    print("4. If still failing, run the unicorn test to verify deployment")

if __name__ == "__main__":
    main()