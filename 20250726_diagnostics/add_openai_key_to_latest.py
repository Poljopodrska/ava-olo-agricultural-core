#!/usr/bin/env python3
"""
Add OpenAI API Key to Latest Task Definition
"""
import json
import subprocess
import sys

def main():
    print("🔧 Adding OpenAI API Key to Latest Task Definition...")
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
    
    print(f"✅ Found OpenAI key: {openai_key[:10]}...")
    
    # Get latest task definition (revision 34)
    print("📥 Fetching latest task definition (revision 34)...")
    result = subprocess.run(
        ["aws", "ecs", "describe-task-definition", "--task-definition", "ava-agricultural-task:34", "--region", "us-east-1"],
        capture_output=True,
        text=True
    )
    
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
    
    # Add OPENAI_API_KEY to environment variables
    container = task_def['containerDefinitions'][0]
    if 'environment' not in container:
        container['environment'] = []
    
    # Check if key already exists
    key_exists = any(env['name'] == 'OPENAI_API_KEY' for env in container['environment'])
    
    if key_exists:
        print("⚠️  Updating existing OPENAI_API_KEY...")
        for env in container['environment']:
            if env['name'] == 'OPENAI_API_KEY':
                env['value'] = openai_key
    else:
        print("➕ Adding OPENAI_API_KEY to environment...")
        container['environment'].append({
            'name': 'OPENAI_API_KEY',
            'value': openai_key
        })
    
    # Save to file
    with open('/tmp/task-def-with-key.json', 'w') as f:
        json.dump(task_def, f, indent=2)
    
    print("📤 Registering new task definition...")
    result = subprocess.run(
        ["aws", "ecs", "register-task-definition", "--cli-input-json", "file:///tmp/task-def-with-key.json", "--region", "us-east-1"],
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
    print("🚀 Updating service to use new task definition...")
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
    print(f"- New task definition: ava-agricultural-task:{new_revision}")
    print(f"- OpenAI key added: {openai_key[:10]}...{openai_key[-4:]}")
    print(f"- Service: agricultural-core")
    print(f"- Deployment: IN PROGRESS")
    print("\n⏳ Wait 2-3 minutes for deployment to complete")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())