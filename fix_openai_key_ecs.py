#!/usr/bin/env python3
"""
Fix OpenAI API Key in ECS Task Definition
"""
import json
import subprocess
import sys
import os

def main():
    print("🔧 Fixing OpenAI API Key in ECS Task Definition...")
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
    
    print(f"✅ Found OpenAI key: {openai_key[:10]}...{openai_key[-4:]}")
    
    # Get current task definition
    print("\n📥 Fetching current task definition...")
    result = subprocess.run(
        ["aws", "ecs", "describe-task-definition", 
         "--task-definition", "ava-agricultural-task", 
         "--region", "us-east-1"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to fetch task definition: {result.stderr}")
        return 1
    
    # Parse and check current revision
    data = json.loads(result.stdout)
    current_revision = data['taskDefinition']['revision']
    print(f"📋 Current task definition revision: {current_revision}")
    
    # Check current OPENAI_API_KEY value
    container = data['taskDefinition']['containerDefinitions'][0]
    current_key_value = None
    for env in container.get('environment', []):
        if env['name'] == 'OPENAI_API_KEY':
            current_key_value = env['value']
            break
    
    print(f"\n🔍 Current OPENAI_API_KEY value: {current_key_value[:20] if current_key_value else 'NOT_SET'}...")
    
    if current_key_value == openai_key:
        print("✅ OpenAI key is already correctly set!")
        return 0
    
    if current_key_value and current_key_value.startswith('sk-'):
        print("⚠️  A different OpenAI key is already set")
        print(f"   Current: {current_key_value[:10]}...")
        print(f"   New:     {openai_key[:10]}...")
        response = input("Replace with new key? (y/n): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return 1
    
    # Create new task definition with correct key
    print("\n🔄 Creating new task definition with correct OpenAI key...")
    
    task_def = data['taskDefinition']
    
    # Remove fields that shouldn't be in new definition
    fields_to_remove = ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 
                       'compatibilities', 'registeredAt', 'registeredBy']
    for field in fields_to_remove:
        task_def.pop(field, None)
    
    # Update OPENAI_API_KEY
    key_found = False
    for env in container['environment']:
        if env['name'] == 'OPENAI_API_KEY':
            env['value'] = openai_key
            key_found = True
            break
    
    if not key_found:
        container['environment'].append({
            'name': 'OPENAI_API_KEY',
            'value': openai_key
        })
    
    # Save to temp file
    with open('/tmp/task-def-fixed.json', 'w') as f:
        json.dump(task_def, f, indent=2)
    
    # Register new task definition
    print("📤 Registering new task definition...")
    result = subprocess.run(
        ["aws", "ecs", "register-task-definition", 
         "--cli-input-json", "file:///tmp/task-def-fixed.json", 
         "--region", "us-east-1"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to register task definition: {result.stderr}")
        return 1
    
    register_data = json.loads(result.stdout)
    new_revision = register_data['taskDefinition']['revision']
    print(f"✅ New task definition registered: ava-agricultural-task:{new_revision}")
    
    # Update service
    print("\n🚀 Updating service to use new task definition...")
    result = subprocess.run([
        "aws", "ecs", "update-service",
        "--cluster", "ava-olo-production",
        "--service", "agricultural-core",
        "--task-definition", f"ava-agricultural-task:{new_revision}",
        "--force-new-deployment",
        "--region", "us-east-1"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to update service: {result.stderr}")
        return 1
    
    print("✅ Service update initiated!")
    print(f"\n📊 Summary:")
    print(f"- Previous revision: {current_revision}")
    print(f"- New revision: {new_revision}")
    print(f"- OpenAI key: {openai_key[:10]}...{openai_key[-4:]}")
    print(f"- Service: agricultural-core")
    print(f"- Deployment: IN PROGRESS")
    print("\n⏳ Wait 2-3 minutes for deployment to complete")
    print("🔗 Then test at: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/chat-debug-audit")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())