#!/usr/bin/env python3
"""
Ensure OpenAI API key is set in ECS environment
Critical for Constitutional Amendment #15 compliance
"""
import subprocess
import json
import os

print("🔑 ENSURING OPENAI API KEY IN APP RUNNER")
print("=" * 60)

# Get the OpenAI key from .env.production
openai_key = None
try:
    with open('.env.production', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                openai_key = line.split('=', 1)[1].strip()
                break
    
    if openai_key:
        print(f"✅ Found OpenAI key in .env.production")
        print(f"   Key prefix: {openai_key[:10]}...")
    else:
        print("❌ No OpenAI key found in .env.production")
except Exception as e:
    print(f"❌ Error reading .env.production: {e}")

if not openai_key:
    print("\n⚠️  Cannot proceed without OpenAI API key")
    print("Please ensure OPENAI_API_KEY is set in .env.production")
    exit(1)

print("\n🔍 Checking ECS service...")

try:
    # List services
    result = subprocess.run([
        'aws', 'ecs', 'list-services',
        '--region', 'us-east-1',
        '--query', 'ServiceSummaryList[?ServiceName==`ava-olo-agricultural-core`]',
        '--output', 'json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        services = json.loads(result.stdout)
        if services:
            service = services[0]
            service_arn = service['ServiceArn']
            service_name = service['ServiceName']
            print(f"✅ Found service: {service_name}")
            print(f"   ARN: {service_arn}")
            
            # Get service details
            detail_result = subprocess.run([
                'aws', 'ecs', 'describe-service',
                '--service-arn', service_arn,
                '--region', 'us-east-1',
                '--output', 'json'
            ], capture_output=True, text=True)
            
            if detail_result.returncode == 0:
                service_details = json.loads(detail_result.stdout)
                
                # Check current environment variables
                current_env = service_details.get('Service', {}).get('SourceConfiguration', {}).get('ImageRepository', {}).get('ImageConfiguration', {}).get('RuntimeEnvironmentVariables', {})
                
                print("\n📋 Current environment variables:")
                for key in ['OPENAI_API_KEY', 'DB_HOST', 'DB_NAME']:
                    value = current_env.get(key, 'NOT SET')
                    if key == 'OPENAI_API_KEY' and value != 'NOT SET':
                        print(f"   {key}: {value[:10]}...")
                    else:
                        print(f"   {key}: {value}")
                
                if 'OPENAI_API_KEY' not in current_env:
                    print("\n⚠️  OPENAI_API_KEY not set in ECS!")
                    print("\n📝 To fix this:")
                    print("1. Go to AWS ECS console")
                    print("2. Select ava-olo-agricultural-core service")
                    print("3. Click 'Update service'")
                    print("4. Go to 'Configure service' step")
                    print("5. Add environment variable:")
                    print(f"   Name: OPENAI_API_KEY")
                    print(f"   Value: {openai_key}")
                    print("6. Complete the update")
                else:
                    print("\n✅ OPENAI_API_KEY is already set!")
            else:
                print(f"❌ Failed to get service details: {detail_result.stderr}")
        else:
            print("❌ No ECS service found named 'ava-olo-agricultural-core'")
    else:
        print(f"❌ Failed to list services: {result.stderr}")
        
except FileNotFoundError:
    print("❌ AWS CLI not installed")
    print("\n📝 Manual steps:")
    print("1. Install AWS CLI: pip install awscli")
    print("2. Configure: aws configure")
    print("3. Run this script again")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🔧 ALTERNATIVE: Update via ecs.yaml")
print("The ecs.yaml has been updated with the OpenAI key.")
print("Push the changes to trigger a new deployment:")
print("  git add ecs.yaml")
print("  git commit -m 'Add OpenAI API key to ECS config'")
print("  git push origin main")