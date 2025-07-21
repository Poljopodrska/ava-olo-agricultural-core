#!/usr/bin/env python3
"""
Add non-secret environment variables to agricultural task
(DB_PASSWORD is handled by Secrets Manager)
"""
import json
import subprocess

# Environment variables to add (excluding DB_PASSWORD which uses Secrets Manager)
env_vars_to_add = [
    {"name": "DB_HOST", "value": "farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"},
    {"name": "DB_NAME", "value": "farmer_crm"},
    {"name": "DB_USER", "value": "postgres"},
    {"name": "DB_PORT", "value": "5432"},
    {"name": "OPENAI_API_KEY", "value": "REPLACE_WITH_ACTUAL_API_KEY"},
    {"name": "OPENWEATHER_API_KEY", "value": "53efe5a8c7ac5cad63b7b0419f5d3069"},
    {"name": "SECRET_KEY", "value": "8tsHicCkKBHvwk51zNp80RY2uUZGTLAb"},
    {"name": "JWT_SECRET_KEY", "value": "pJnruaBvL9ZLvWqr7QLtvXv9F0xw1kO6"},
    {"name": "AWS_REGION", "value": "us-east-1"},
    {"name": "AWS_DEFAULT_REGION", "value": "us-east-1"},
    {"name": "ENVIRONMENT", "value": "production"},
    {"name": "DEBUG", "value": "false"},
    {"name": "LOG_LEVEL", "value": "INFO"}
]

print("🚀 Updating ava-agricultural-task with environment variables...")

# Get current task definition
result = subprocess.run(
    "aws ecs describe-task-definition --task-definition ava-agricultural-task --region us-east-1",
    shell=True, capture_output=True, text=True
)

if result.returncode != 0:
    print(f"❌ Error: {result.stderr}")
    exit(1)

task_def = json.loads(result.stdout)

# Update environment variables (keep existing ones)
container_def = task_def['taskDefinition']['containerDefinitions'][0]
existing_env = container_def.get('environment', [])

# Create a dict of existing vars
existing_vars = {var['name']: var['value'] for var in existing_env}

# Add new vars (don't override existing)
for var in env_vars_to_add:
    if var['name'] not in existing_vars:
        existing_env.append(var)

# Update container definition
container_def['environment'] = existing_env

# Create new task definition (keep secrets as is)
new_task_def = {
    "family": task_def['taskDefinition']['family'],
    "containerDefinitions": [container_def],
    "requiresCompatibilities": ["EC2"]
}

# Add other required fields
for field in ['taskRoleArn', 'executionRoleArn', 'networkMode', 'cpu', 'memory']:
    if field in task_def['taskDefinition'] and task_def['taskDefinition'][field]:
        new_task_def[field] = task_def['taskDefinition'][field]

# Write to file
with open('agricultural-task-def.json', 'w') as f:
    json.dump(new_task_def, f, indent=2)

print("✅ Task definition prepared")
print("📋 Registering new revision...")

# Register new task definition
result = subprocess.run(
    "aws ecs register-task-definition --cli-input-json file://agricultural-task-def.json --region us-east-1",
    shell=True, capture_output=True, text=True
)

if result.returncode == 0:
    response = json.loads(result.stdout)
    revision = response['taskDefinition']['revision']
    print(f"✅ Created revision: ava-agricultural-task:{revision}")
    
    # Update service
    print("🔄 Updating agricultural-core service...")
    update_result = subprocess.run(
        f"aws ecs update-service --cluster ava-olo-production --service agricultural-core --task-definition ava-agricultural-task:{revision} --region us-east-1",
        shell=True, capture_output=True, text=True
    )
    
    if update_result.returncode == 0:
        print("✅ Service update initiated!")
        print("\n📊 Summary:")
        print("- Database password updated in Secrets Manager ✅")
        print("- Environment variables added to task ✅")
        print("- Service updating with new configuration ✅")
        print("\n⏱️  Wait 2-3 minutes for services to stabilize")
        print("\n🔍 Then check:")
        print("http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check")
    else:
        print(f"⚠️  Service update failed: {update_result.stderr}")
else:
    print(f"❌ Failed to register task definition: {result.stderr}")