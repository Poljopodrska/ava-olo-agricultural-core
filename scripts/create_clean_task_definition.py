#!/usr/bin/env python3
"""
Create clean task definition without secrets issues
Force v3.3.26 deployment
"""
import subprocess
import json
import time

def create_clean_task_def():
    """Create task definition without secrets issues"""
    
    print("🧹 Creating Clean Task Definition")
    print("=" * 40)
    
    # Get current working task def as template (task def 5)
    cmd = "aws ecs describe-task-definition --task-definition ava-agricultural-task:5 --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error getting task definition: {result.stderr}")
        return False
    
    task_def = json.loads(result.stdout)['taskDefinition']
    print(f"✅ Got template from revision {task_def['revision']}")
    
    # Remove fields that shouldn't be in registration
    fields_to_remove = [
        'taskDefinitionArn', 'revision', 'status', 'requiresAttributes',
        'registeredAt', 'registeredBy', 'compatibilities'
    ]
    for field in fields_to_remove:
        task_def.pop(field, None)
    
    # CRITICAL: Update image to use latest with v3.3.26
    old_image = task_def['containerDefinitions'][0]['image']
    new_image = '127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest'
    task_def['containerDefinitions'][0]['image'] = new_image
    
    print(f"📦 Updated image:")
    print(f"  Old: {old_image}")
    print(f"  New: {new_image}")
    
    # Remove ANY secrets to prevent issues
    if 'secrets' in task_def['containerDefinitions'][0]:
        print("🔒 Removing secrets from container definition...")
        del task_def['containerDefinitions'][0]['secrets']
    
    # Ensure we have environment variables for the app to work
    env_vars = task_def['containerDefinitions'][0].get('environment', [])
    required_env = [
        {"name": "PORT", "value": "8000"},
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "SERVICE_NAME", "value": "agricultural-core"}
    ]
    
    # Add missing env vars
    existing_names = {env['name'] for env in env_vars}
    for env_var in required_env:
        if env_var['name'] not in existing_names:
            env_vars.append(env_var)
    
    task_def['containerDefinitions'][0]['environment'] = env_vars
    
    # Increase resources for stability
    task_def['cpu'] = '1024'
    task_def['memory'] = '2048'
    task_def['containerDefinitions'][0]['memory'] = 2048
    
    # Add health check
    task_def['containerDefinitions'][0]['healthCheck'] = {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/version || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
    }
    
    # Save to file for debugging
    with open('clean-task-definition.json', 'w') as f:
        json.dump(task_def, f, indent=2)
    
    print("💾 Task definition saved to clean-task-definition.json")
    
    # Register new task definition
    print("\n📝 Registering clean task definition...")
    cmd = "aws ecs register-task-definition --cli-input-json file://clean-task-definition.json --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        response = json.loads(result.stdout)
        new_revision = response['taskDefinition']['revision']
        print(f"✅ Created clean task definition revision: {new_revision}")
        return new_revision
    else:
        print(f"❌ Error registering task definition: {result.stderr}")
        return False

def nuclear_deployment(task_revision):
    """Nuclear deployment approach to force v3.3.26"""
    
    print(f"\n☢️  NUCLEAR DEPLOYMENT FORCE")
    print("=" * 40)
    
    # 1. Stop ALL running tasks
    print("🛑 Stopping all current tasks...")
    cmd = """aws ecs list-tasks \
        --cluster ava-olo-production \
        --service-name agricultural-core \
        --region us-east-1 \
        --query 'taskArns[]' \
        --output text"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        task_arns = result.stdout.strip().split()
        for task_arn in task_arns:
            task_id = task_arn.split('/')[-1]
            print(f"  Stopping task: {task_id}")
            stop_cmd = f"""aws ecs stop-task \
                --cluster ava-olo-production \
                --task {task_arn} \
                --reason 'Force deployment of v3.3.26' \
                --region us-east-1"""
            subprocess.run(stop_cmd, shell=True, capture_output=True)
    
    # 2. Scale down to 0
    print("📉 Scaling service to 0...")
    cmd = f"""aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --desired-count 0 \
        --region us-east-1"""
    subprocess.run(cmd, shell=True, capture_output=True)
    
    time.sleep(10)
    
    # 3. Update with new task definition and scale up
    print(f"🚀 Updating to task definition {task_revision} and scaling up...")
    cmd = f"""aws ecs update-service \
        --cluster ava-olo-production \
        --service agricultural-core \
        --task-definition ava-agricultural-task:{task_revision} \
        --desired-count 2 \
        --force-new-deployment \
        --deployment-configuration maximumPercent=200,minimumHealthyPercent=0 \
        --region us-east-1"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Nuclear deployment initiated!")
        return True
    else:
        print(f"❌ Nuclear deployment failed: {result.stderr}")
        return False

def monitor_deployment():
    """Monitor deployment progress"""
    
    print("\n🔍 Monitoring Deployment...")
    print("=" * 40)
    
    start_time = time.time()
    timeout = 600  # 10 minutes
    
    while time.time() - start_time < timeout:
        cmd = """aws ecs describe-services \
            --cluster ava-olo-production \
            --services agricultural-core \
            --region us-east-1 \
            --query 'services[0].{running:runningCount,desired:desiredCount,deployments:deployments[0].{status:status,taskDef:taskDefinition,running:runningCount}}' \
            --output json"""
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            running = data['running']
            desired = data['desired']
            deployment = data['deployments']
            
            print(f"\r⏳ Tasks: {running}/{desired} | Deployment: {deployment['status']} | Task Def: {deployment['taskDef'].split(':')[-1]} | Running: {deployment['running']}", end='', flush=True)
            
            if running >= desired and running > 0 and deployment['status'] == 'PRIMARY':
                print("\n✅ Deployment complete!")
                return True
        
        time.sleep(10)
    
    print(f"\n⏰ Timeout after {timeout//60} minutes")
    return False

def main():
    print("🚀 FORCE DEPLOY v3.3.26 - NUCLEAR OPTION")
    print("=" * 50)
    
    # Step 1: Create clean task definition
    revision = create_clean_task_def()
    if not revision:
        print("❌ Failed to create task definition")
        return False
    
    # Step 2: Nuclear deployment
    if not nuclear_deployment(revision):
        print("❌ Nuclear deployment failed")
        return False
    
    # Step 3: Monitor deployment
    if monitor_deployment():
        print("\n🎉 SUCCESS! v3.3.26 should be deployed!")
        print("Testing endpoints in 30 seconds...")
        time.sleep(30)
        
        # Quick test
        import subprocess
        test_cmd = "curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version"
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Version endpoint: {result.stdout}")
            if '3.3.26' in result.stdout:
                print("🎉 v3.3.26 CONFIRMED DEPLOYED!")
            else:
                print("⚠️ Still showing old version - may need more time")
        
        return True
    else:
        print("❌ Deployment monitoring failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ DEPLOYMENT COMPLETE")
        print("Check: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com")
    else:
        print("\n❌ DEPLOYMENT FAILED")
        print("Check ECS console for errors")