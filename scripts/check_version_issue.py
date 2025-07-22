#!/usr/bin/env python3
"""
Check why version v20 is showing instead of v23
"""
import subprocess
import json
import time
from datetime import datetime

def check_version_in_code():
    """Check VERSION constant in the codebase"""
    print("🔍 CHECKING VERSION IN CODE...")
    print("=" * 60)
    
    # Check config.py
    config_path = "../modules/core/config.py"
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'VERSION' in line and '=' in line:
                    print(f"Found: {line.strip()}")
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
    
    print("\n✅ Code shows VERSION = v3.3.23-deployment-fixed")
    print("❌ But production shows v3.3.20")
    print("🚨 This means ECS is running an old container image!")

def check_ecs_status():
    """Check what ECS is actually running"""
    print("\n\n🔍 CHECKING ECS STATUS...")
    print("=" * 60)
    
    try:
        # List running tasks
        cmd = "aws ecs list-tasks --cluster ava-olo-production --service-name agricultural-core --region us-east-1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            tasks = json.loads(result.stdout)
            print(f"Running tasks: {len(tasks.get('taskArns', []))}")
            
            # Describe each task
            for task_arn in tasks.get('taskArns', []):
                cmd = f"aws ecs describe-tasks --cluster ava-olo-production --tasks {task_arn} --region us-east-1"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    task_details = json.loads(result.stdout)
                    for task in task_details.get('tasks', []):
                        print(f"\nTask: {task_arn.split('/')[-1]}")
                        print(f"  Task Definition: {task.get('taskDefinitionArn', 'N/A').split('/')[-1]}")
                        print(f"  Status: {task.get('lastStatus', 'N/A')}")
                        print(f"  Started: {task.get('startedAt', 'N/A')}")
        
        # Check service configuration
        cmd = "aws ecs describe-services --cluster ava-olo-production --services agricultural-core --region us-east-1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            for service in services.get('services', []):
                print(f"\nService Configuration:")
                print(f"  Task Definition: {service.get('taskDefinition', 'N/A').split('/')[-1]}")
                print(f"  Desired Count: {service.get('desiredCount', 'N/A')}")
                print(f"  Running Count: {service.get('runningCount', 'N/A')}")
                print(f"  Pending Count: {service.get('pendingCount', 'N/A')}")
                
                # Check deployments
                print("\n  Deployments:")
                for deployment in service.get('deployments', []):
                    print(f"    - Status: {deployment.get('status')}")
                    print(f"      Task Definition: {deployment.get('taskDefinition', '').split('/')[-1]}")
                    print(f"      Desired: {deployment.get('desiredCount')}")
                    print(f"      Running: {deployment.get('runningCount')}")
                    print(f"      Created: {deployment.get('createdAt')}")
    
    except Exception as e:
        print(f"Error checking ECS: {e}")

def check_ecr_images():
    """Check ECR for available images"""
    print("\n\n🔍 CHECKING ECR IMAGES...")
    print("=" * 60)
    
    try:
        # List images in ECR
        cmd = "aws ecr list-images --repository-name ava-olo/agricultural-core --region us-east-1 --max-items 10"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            images = json.loads(result.stdout)
            print("Recent images in ECR:")
            for image in images.get('imageIds', []):
                tag = image.get('imageTag', 'untagged')
                if tag != 'untagged':
                    print(f"  - {tag}")
            
            # Check what 'latest' points to
            cmd = "aws ecr describe-images --repository-name ava-olo/agricultural-core --image-ids imageTag=latest --region us-east-1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                image_details = json.loads(result.stdout)
                for image in image_details.get('imageDetails', []):
                    print(f"\n'latest' tag details:")
                    print(f"  Pushed at: {image.get('imagePushedAt', 'N/A')}")
                    print(f"  Digest: {image.get('imageDigest', 'N/A')[:20]}...")
    
    except Exception as e:
        print(f"Error checking ECR: {e}")

def test_live_endpoint():
    """Test the live endpoint to see what version is running"""
    print("\n\n🔍 TESTING LIVE ENDPOINTS...")
    print("=" * 60)
    
    endpoints = [
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health",
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check",
        "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/debug/services"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        cmd = f"curl -s {endpoint} | jq -r '.version // .service_version // .agricultural_core.version // \"No version found\"'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  Version: {result.stdout.strip()}")
        else:
            print("  Failed to get version")

def main():
    print("🚨 VERSION MISMATCH INVESTIGATION")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    print("Problem: Code shows v23 but production shows v20")
    
    check_version_in_code()
    check_ecs_status()
    check_ecr_images()
    test_live_endpoint()
    
    print("\n\n📋 DIAGNOSIS:")
    print("=" * 60)
    print("The code has been updated to v3.3.23, but ECS is still running")
    print("an old container image with v3.3.20. This means either:")
    print("1. The deployment didn't actually push a new image to ECR")
    print("2. ECS is using an old task definition")
    print("3. The new image wasn't built with the updated code")
    print("\nNext step: Force ECS to use the new version!")

if __name__ == "__main__":
    main()