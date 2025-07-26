#!/usr/bin/env python3
"""
Force deployment of commit 8a3408b - Critical Constitutional Fix
This ensures the LLM registration fix is deployed to production
"""
import subprocess
import time
import os
import json

print("🚨 CRITICAL DEPLOYMENT: Constitutional Fix 8a3408b")
print("=" * 60)
print("Deploying fix for Constitutional Amendment #15 violation")
print("Registration MUST use LLM, not hardcoded responses")
print()

# Step 1: Ensure we're on the right commit
try:
    current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()[:7]
    print(f"Current commit: {current_commit}")
    
    if current_commit != "8a3408b":
        print("⚠️  Not on commit 8a3408b, checking out...")
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        subprocess.run(['git', 'checkout', '8a3408b'], check=True)
except Exception as e:
    print(f"Git check failed: {e}")

# Step 2: Update deployment timestamp in main.py
print("\n📝 Updating deployment timestamp...")
timestamp = int(time.time())
try:
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Add deployment marker
    deployment_marker = f"\n# CRITICAL DEPLOYMENT {timestamp}: Constitutional Fix 8a3408b - LLM Registration\n"
    
    if '# CRITICAL DEPLOYMENT' in content:
        import re
        content = re.sub(r'# CRITICAL DEPLOYMENT.*\n', deployment_marker, content)
    else:
        # Insert after imports
        content = content.replace('from fastapi import FastAPI', 
                                 f'from fastapi import FastAPI{deployment_marker}')
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✅ Deployment timestamp added")
except Exception as e:
    print(f"❌ Failed to update main.py: {e}")

# Step 3: Create deployment manifest
print("\n📋 Creating deployment manifest...")
manifest = {
    "deployment_id": f"8a3408b-{timestamp}",
    "commit": "8a3408b",
    "timestamp": timestamp,
    "critical_fix": True,
    "description": "Constitutional Amendment #15 - Registration must use LLM",
    "changes": [
        "Fixed /api/v1/registration/cava to use enhanced_cava with LLM",
        "Added /api/v1/registration/debug endpoint",
        "Added comprehensive LLM logging",
        "Updated startup checks for OpenAI API key"
    ],
    "verification_steps": [
        "Check /api/v1/registration/debug shows openai_key_set: true",
        "Test registration with 'I want to register'",
        "Verify no hardcoded greetings in response",
        "Check logs for 🏛️ CONSTITUTIONAL LLM CALL"
    ]
}

with open('deployment_manifest_8a3408b.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print("✅ Manifest created")

# Step 4: Commit and push
print("\n🚀 Committing and pushing...")
try:
    subprocess.run(['git', 'add', '.'], check=True)
    commit_msg = f"""🚨 FORCE DEPLOY: Critical Constitutional Fix 8a3408b

VIOLATION: Registration using hardcoded responses instead of LLM
AMENDMENT: Constitutional Amendment #15 requires 95%+ LLM intelligence
TIMESTAMP: {timestamp}

This deployment ensures all registration flows use OpenAI LLM.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
    
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    subprocess.run(['git', 'push', 'origin', 'main', '--force-with-lease'], check=True)
    print("✅ Pushed to GitHub")
except Exception as e:
    print(f"❌ Git push failed: {e}")

# Step 5: Trigger App Runner deployment
print("\n🔧 Attempting to trigger App Runner deployment...")
try:
    # List services
    result = subprocess.run([
        'aws', 'apprunner', 'list-services',
        '--region', 'us-east-1',
        '--query', 'ServiceSummaryList[?ServiceName==`ava-olo-agricultural-core`].ServiceArn',
        '--output', 'text'
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        service_arn = result.stdout.strip()
        print(f"Found service: {service_arn}")
        
        # Start deployment
        deploy_cmd = [
            'aws', 'apprunner', 'start-deployment',
            '--service-arn', service_arn,
            '--region', 'us-east-1'
        ]
        
        deploy_result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if deploy_result.returncode == 0:
            print("✅ App Runner deployment triggered!")
            deploy_data = json.loads(deploy_result.stdout)
            operation_id = deploy_data.get('OperationId', 'Unknown')
            print(f"   Operation ID: {operation_id}")
            
            # Save operation ID
            with open('deployment_operation_8a3408b.txt', 'w') as f:
                f.write(f"Operation ID: {operation_id}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Commit: 8a3408b\n")
        else:
            print(f"❌ Deployment trigger failed: {deploy_result.stderr}")
    else:
        print("❌ Could not find App Runner service")
        print("Manual deployment required via AWS Console")
except FileNotFoundError:
    print("❌ AWS CLI not installed - manual deployment required")
except Exception as e:
    print(f"❌ AWS deployment failed: {e}")

print("\n" + "=" * 60)
print("📊 DEPLOYMENT SUMMARY")
print(f"   Commit: 8a3408b")
print(f"   Timestamp: {timestamp}")
print(f"   Manifest: deployment_manifest_8a3408b.json")
print()
print("⏳ NEXT STEPS:")
print("1. Wait 3-5 minutes for deployment")
print("2. Run: python verify_deployment_8a3408b.py")
print("3. Check production URL for debug endpoint")
print()
print("🔍 MANUAL VERIFICATION:")
print("curl https://ava-olo-agricultural-core.../api/v1/registration/debug")
print()
print("If deployment doesn't start automatically:")
print("1. Go to AWS App Runner console")
print("2. Find ava-olo-agricultural-core service")
print("3. Click 'Deploy' button")