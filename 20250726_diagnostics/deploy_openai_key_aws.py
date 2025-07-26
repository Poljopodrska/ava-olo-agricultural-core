#!/usr/bin/env python3
"""
Deploy OpenAI API Key to ECS Task Definition
This script updates the ECS task definition with the OpenAI API key
"""
import json
import subprocess
import sys
import os

def run_aws_command(cmd):
    """Run AWS CLI command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🔧 Updating ECS Task Definition with OpenAI API Key...")
    print("=" * 50)
    
    # Get OpenAI key from .env.production
    openai_key = None
    try:
        with open('.env.production', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    openai_key = line.strip().split('=', 1)[1]
                    break
    except Exception as e:
        print(f"❌ Error reading .env.production: {e}")
        return 1
    
    if not openai_key:
        print("❌ OpenAI API key not found in .env.production")
        return 1
    
    print(f"✅ Found OpenAI key (first 10 chars): {openai_key[:10]}...")
    
    # Get current task definition
    print("📥 Fetching current task definition...")
    task_def_json = run_aws_command(
        "aws ecs describe-task-definition --task-definition ava-agricultural-task --region us-east-1"
    )
    
    if not task_def_json:
        print("❌ Failed to fetch task definition")
        return 1
    
    try:
        task_def = json.loads(task_def_json)
        new_task_def = task_def['taskDefinition']
        
        # Remove fields that shouldn't be in the new definition
        fields_to_remove = ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 
                           'compatibilities', 'registeredAt', 'registeredBy']
        for field in fields_to_remove:
            new_task_def.pop(field, None)
        
        # Check if OPENAI_API_KEY already exists
        env_vars = new_task_def['containerDefinitions'][0].get('environment', [])
        openai_exists = False
        
        for i, env_var in enumerate(env_vars):
            if env_var['name'] == 'OPENAI_API_KEY':
                env_vars[i]['value'] = openai_key
                openai_exists = True
                print("⚠️  OPENAI_API_KEY already exists, updating value...")
                break
        
        if not openai_exists:
            print("➕ Adding OPENAI_API_KEY to environment variables...")
            env_vars.append({
                'name': 'OPENAI_API_KEY',
                'value': openai_key
            })
        
        new_task_def['containerDefinitions'][0]['environment'] = env_vars
        
        # Save to temp file
        with open('/tmp/new-task-def.json', 'w') as f:
            json.dump(new_task_def, f, indent=2)
        
        print("✅ Prepared new task definition")
        
    except Exception as e:
        print(f"❌ Error processing task definition: {e}")
        return 1
    
    # Register new task definition
    print("📤 Registering new task definition...")
    register_output = run_aws_command(
        "aws ecs register-task-definition --cli-input-json file:///tmp/new-task-def.json --region us-east-1"
    )
    
    if not register_output:
        print("❌ Failed to register task definition")
        return 1
    
    try:
        register_result = json.loads(register_output)
        new_revision = register_result['taskDefinition']['revision']
        print(f"✅ New task definition registered: ava-agricultural-task:{new_revision}")
    except Exception as e:
        print(f"❌ Error parsing registration result: {e}")
        return 1
    
    # Update the service
    print("🚀 Updating ECS service...")
    update_output = run_aws_command(
        f"aws ecs update-service --cluster ava-olo-cluster --service ava-olo-agricultural-core "
        f"--task-definition ava-agricultural-task:{new_revision} --force-new-deployment --region us-east-1"
    )
    
    if not update_output:
        print("❌ Failed to update service")
        return 1
    
    print("✅ Service update initiated successfully!")
    print()
    print("📊 Deployment Status:")
    print(f"- Cluster: ava-olo-cluster")
    print(f"- Service: ava-olo-agricultural-core")
    print(f"- New Task Definition: ava-agricultural-task:{new_revision}")
    print(f"- Deployment: STARTED")
    print()
    print("⏳ Deployment will take 2-3 minutes to complete.")
    print()
    print("🧪 To verify after deployment:")
    print("curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/registration/llm-status")
    print()
    print("Should show: \"openai_key_exists\": true")
    print()
    print("🎉 OpenAI API Key deployment initiated!")
    
    # Clean up
    try:
        os.remove('/tmp/new-task-def.json')
    except:
        pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())