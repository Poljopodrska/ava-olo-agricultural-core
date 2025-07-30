#!/usr/bin/env python3
"""
Fix Current Task Definition Revision with OpenAI Key
Add OPENAI_API_KEY to the currently used revision (36)
"""
import json
import subprocess
import sys

def main():
    print("🔧 Adding OpenAI API Key to Current Task Definition...")
    print("=" * 60)
    
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
    
    print(f"✅ Found OpenAI key: {openai_key[:10]}...")
    
    # Check which revision is currently running
    print("🔍 Checking currently running task definition...")
    result = subprocess.run([
        "aws", "ecs", "describe-services", 
        "--cluster", "ava-olo-production",
        "--services", "agricultural-core",
        "--region", "us-east-1",
        "--query", "services[0].taskDefinition",
        "--output", "text"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get current task definition: {result.stderr}")
        return 1
    
    current_task_def = result.stdout.strip().split('/')[-1]  # Get just the name:revision
    print(f"📋 Currently running: {current_task_def}")
    
    # Get the task definition
    print(f"📥 Fetching task definition {current_task_def}...")
    result = subprocess.run([
        "aws", "ecs", "describe-task-definition", 
        "--task-definition", current_task_def,
        "--region", "us-east-1"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to fetch task definition: {result.stderr}")
        return 1
    
    task_def_data = json.loads(result.stdout)
    task_def = task_def_data['taskDefinition']
    
    # Remove fields that shouldn't be in new definition
    fields_to_remove = ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 
                       'compatibilities', 'registeredAt', 'registeredBy']
    for field in fields_to_remove:
        task_def.pop(field, None)
    
    # Check if OpenAI key exists
    container = task_def['containerDefinitions'][0]
    if 'environment' not in container:
        container['environment'] = []
    
    key_exists = any(env['name'] == 'OPENAI_API_KEY' for env in container['environment'])
    
    if key_exists:
        print("⚠️  OPENAI_API_KEY already exists, updating value...")
        for env in container['environment']:
            if env['name'] == 'OPENAI_API_KEY':
                env['value'] = openai_key
                break
    else:
        print("➕ Adding OPENAI_API_KEY to environment...")
        container['environment'].append({
            'name': 'OPENAI_API_KEY',
            'value': openai_key
        })
    
    # Save to file
    with open('/tmp/task-def-fixed.json', 'w') as f:
        json.dump(task_def, f, indent=2)
    
    print("📤 Registering new task definition...")
    result = subprocess.run([
        "aws", "ecs", "register-task-definition", 
        "--cli-input-json", "file:///tmp/task-def-fixed.json",
        "--region", "us-east-1"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to register task definition: {result.stderr}")
        return 1
    
    register_data = json.loads(result.stdout)
    new_revision = register_data['taskDefinition']['revision']
    task_family = register_data['taskDefinition']['family']
    print(f"✅ New task definition registered: {task_family}:{new_revision}")
    
    # Force complete deployment
    print("🚀 Forcing complete deployment...")
    
    # Step 1: Scale down to 0
    print("   Scaling down to 0...")
    result = subprocess.run([
        "aws", "ecs", "update-service",
        "--cluster", "ava-olo-production",
        "--service", "agricultural-core",
        "--desired-count", "0",
        "--region", "us-east-1"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to scale down: {result.stderr}")
        return 1
    
    print("   Waiting 30 seconds for tasks to stop...")
    import time
    time.sleep(30)
    
    # Step 2: Scale back up with new task definition
    print(f"   Scaling up with new task definition {task_family}:{new_revision}...")
    result = subprocess.run([
        "aws", "ecs", "update-service",
        "--cluster", "ava-olo-production",
        "--service", "agricultural-core",
        "--desired-count", "2",
        "--task-definition", f"{task_family}:{new_revision}",
        "--force-new-deployment",
        "--region", "us-east-1"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to scale up: {result.stderr}")
        return 1
    
    print("✅ Deployment initiated!")
    print()
    print("📊 Summary:")
    print(f"- Fixed task definition: {task_family}:{new_revision}")
    print(f"- OpenAI key added: {openai_key[:10]}...{openai_key[-4:]}")
    print(f"- Forced complete deployment: YES")
    print(f"- Service: agricultural-core")
    print()
    print("⏳ Wait 2-3 minutes for new tasks to start")
    print("🧪 Then test with:")
    print("curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/chat/env-check")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())