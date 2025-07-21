#!/usr/bin/env python3
"""
Update ECS Task Definitions with Environment Variables using Python
No jq dependency required
"""
import json
import subprocess
import sys

def run_aws_command(cmd):
    """Run AWS CLI command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return None
        return json.loads(result.stdout) if result.stdout else None
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None

def update_task_definition(task_name, service_name):
    """Update a single task definition with new environment variables"""
    print(f"\n📋 Updating {task_name}...")
    
    # Get current task definition
    print("  - Fetching current task definition...")
    task_def = run_aws_command(f"aws ecs describe-task-definition --task-definition {task_name} --region us-east-1")
    
    if not task_def:
        print(f"  ❌ Failed to fetch task definition for {task_name}")
        return False
    
    # Load new environment variables
    with open('ecs-env-vars.json', 'r') as f:
        new_env_vars = json.load(f)
    
    # Update container definitions with new environment variables
    container_defs = task_def['taskDefinition']['containerDefinitions']
    container_defs[0]['environment'] = new_env_vars
    
    # Create new task definition
    new_task_def = {
        "family": task_def['taskDefinition']['family'],
        "containerDefinitions": container_defs,
        "requiresCompatibilities": ["EC2"]
    }
    
    # Add optional fields if they exist
    optional_fields = ['taskRoleArn', 'executionRoleArn', 'networkMode', 'cpu', 'memory']
    for field in optional_fields:
        if field in task_def['taskDefinition'] and task_def['taskDefinition'][field]:
            new_task_def[field] = task_def['taskDefinition'][field]
    
    # Write to temporary file
    with open('temp-task-def.json', 'w') as f:
        json.dump(new_task_def, f)
    
    # Register new task definition
    print("  - Registering new task definition revision...")
    result = run_aws_command("aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region us-east-1")
    
    if result:
        new_revision = result['taskDefinition']['revision']
        family = result['taskDefinition']['family']
        print(f"  ✅ Created new revision: {family}:{new_revision}")
        
        # Update service if provided
        if service_name:
            print(f"  - Updating service {service_name}...")
            update_cmd = f"aws ecs update-service --cluster ava-olo-cluster --service {service_name} --task-definition {family}:{new_revision} --region us-east-1"
            service_result = run_aws_command(update_cmd)
            
            if service_result:
                print("  ✅ Service updated to use new task definition")
            else:
                print("  ⚠️  Failed to update service. Update manually in AWS console.")
        
        return True
    else:
        print("  ❌ Failed to register new task definition")
        return False

def main():
    print("=== ECS Environment Variables Update Script (Python) ===")
    print("This script will update both ECS task definitions with environment variables\n")
    
    # Check if environment files exist
    if not all([os.path.exists(f) for f in ['.env.production', 'ecs-env-vars.json']]):
        print("❌ Required files not found!")
        print("   Run: python3 scripts/recover_env_vars.py")
        return 1
    
    # Show current environment variables
    print("📊 Current environment variables:")
    print("---------------------------------------------------")
    
    with open('.env.production', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                if 'PASSWORD' in key or 'KEY' in key:
                    if 'REPLACE' in value:
                        print(f"❌ {key}=*** (NEEDS TO BE SET!)")
                    else:
                        print(f"✅ {key}=*** (configured)")
                else:
                    print(f"✅ {key}={value}")
    
    print("\n🚀 Starting ECS updates...\n")
    
    # Update both task definitions
    success = True
    success &= update_task_definition("ava-agricultural-task", "ava-agricultural-core")
    success &= update_task_definition("ava-monitoring-task", "ava-monitoring-dashboards")
    
    # Clean up
    if os.path.exists('temp-task-def.json'):
        os.remove('temp-task-def.json')
    
    if success:
        print("\n=== SUMMARY ===")
        print("✅ Task definitions updated with environment variables")
        print("\n📋 NEXT STEPS:")
        print("1. Go to AWS ECS Console")
        print("2. Check both services are updating")
        print("3. Wait for services to stabilize (2-3 minutes)")
        print("4. Test endpoints:")
        print("   - http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check")
        print("   - http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/api/v1/system/env-check")
        print("\n✅ Script complete!")
    else:
        print("\n❌ Some updates failed. Check AWS console for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    import os
    sys.exit(main())