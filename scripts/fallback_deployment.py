#!/usr/bin/env python3
"""
Fallback deployment strategy
Use working task definition 5 but force new deployment to get latest image
"""
import subprocess
import time
import json

def fallback_deployment():
    """Use task def 5 but force pull latest image"""
    
    print("🔄 FALLBACK DEPLOYMENT STRATEGY")
    print("=" * 40)
    print("Using task definition 5 (known working) but forcing latest image")
    
    # Update service to use task def 5 with force new deployment
    cmd = """aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --task-definition ava-agricultural-task:5 \
        --force-new-deployment \
        --desired-count 1 \
        --region us-east-1"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Fallback deployment initiated with task definition 5")
        return True
    else:
        print(f"❌ Fallback deployment failed: {result.stderr}")
        return False

def monitor_fallback():
    """Monitor fallback deployment"""
    print("\n🔍 Monitoring fallback deployment...")
    
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    while time.time() - start_time < timeout:
        cmd = """aws ecs describe-services \
            --cluster ava-olo-production \
            --services agricultural-core \
            --region us-east-1 \
            --query 'services[0].{running:runningCount,desired:desiredCount}' \
            --output json"""
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            running = data['running']
            desired = data['desired']
            
            print(f"\r⏳ Tasks: {running}/{desired}", end='', flush=True)
            
            if running >= desired and running > 0:
                print("\n✅ Service is running!")
                return True
        
        time.sleep(10)
    
    print(f"\n⏰ Timeout after {timeout//60} minutes")
    return False

def test_version():
    """Test if the version changed"""
    print("\n🧪 Testing version...")
    
    # Wait a bit for ALB to update
    time.sleep(30)
    
    test_cmd = "curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version"
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Version response: {result.stdout}")
        
        if '3.3.26' in result.stdout:
            print("🎉 v3.3.26 DEPLOYED! The latest image contained the new version!")
            return True
        elif '3.3.25' in result.stdout:
            print("⚠️ Still v3.3.25 - The ECR image may not contain v3.3.26")
            return False
        else:
            print("❓ Unexpected version response")
            return False
    else:
        print("❌ Could not test version endpoint")
        return False

def main():
    print("🚀 FALLBACK DEPLOYMENT - Use working task def with latest image")
    print("=" * 60)
    
    if fallback_deployment():
        if monitor_fallback():
            return test_version()
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ v3.3.26 IS DEPLOYED!")
        print("The new features should be available:")
        print("- Ljubljana weather with coordinates")
        print("- Fixed AI connection warning")
        print("- Debug endpoint: /api/v1/debug/services")
    else:
        print("\n❌ v3.3.26 deployment failed")
        print("The ECR image may not contain the latest code")