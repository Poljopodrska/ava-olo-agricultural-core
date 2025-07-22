#!/usr/bin/env python3
"""
Create a new task definition without secrets
Based on task definition 5 but using latest image
"""
import subprocess
import json

def create_task_definition():
    print("📋 Creating new task definition without secrets...")
    
    # Get task definition 5 as template
    cmd = "aws ecs describe-task-definition --task-definition ava-agricultural-task:5 --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error getting task definition: {result.stderr}")
        return False
    
    task_def = json.loads(result.stdout)['taskDefinition']
    
    # Remove fields that shouldn't be in registration
    fields_to_remove = [
        'taskDefinitionArn', 'revision', 'status', 'requiresAttributes',
        'registeredAt', 'registeredBy', 'compatibilities'
    ]
    for field in fields_to_remove:
        task_def.pop(field, None)
    
    # Update image to use latest
    task_def['containerDefinitions'][0]['image'] = '127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest'
    
    # Remove secrets if any
    if 'secrets' in task_def['containerDefinitions'][0]:
        print("Removing secrets from container definition...")
        del task_def['containerDefinitions'][0]['secrets']
    
    # Save to file
    with open('task-definition.json', 'w') as f:
        json.dump(task_def, f, indent=2)
    
    print("✅ Task definition prepared (without secrets)")
    
    # Register new task definition
    print("\n📝 Registering new task definition...")
    cmd = "aws ecs register-task-definition --cli-input-json file://task-definition.json --region us-east-1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        response = json.loads(result.stdout)
        new_revision = response['taskDefinition']['revision']
        print(f"✅ Created task definition revision: {new_revision}")
        
        # Update service to use new task definition
        print(f"\n🚀 Updating service to use revision {new_revision}...")
        cmd = f"""aws ecs update-service \
            --cluster ava-olo-production \
            --service agricultural-core \
            --task-definition ava-agricultural-task:{new_revision} \
            --force-new-deployment \
            --region us-east-1"""
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Service updated successfully!")
            return True
        else:
            print(f"Error updating service: {result.stderr}")
    else:
        print(f"Error registering task definition: {result.stderr}")
    
    return False

if __name__ == "__main__":
    if create_task_definition():
        print("\n🎉 SUCCESS! New task definition created and service updated.")
        print("Wait 2-3 minutes for deployment to complete.")
        print("Then check: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version")
    else:
        print("\n❌ Failed to create task definition")