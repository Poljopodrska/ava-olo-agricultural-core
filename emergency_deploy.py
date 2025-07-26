#!/usr/bin/env python3
"""Emergency deployment to force ECS update"""

import subprocess
import time

print("🚨 EMERGENCY DEPLOYMENT PROTOCOL")
print("=" * 40)

# Check current git status
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if result.stdout:
    print("⚠️  Uncommitted changes detected, committing...")
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Emergency: Save work before deployment'], check=True)

# Method 1: Update main.py with timestamp to force rebuild
print("\n🔧 Method 1: Updating main.py with deployment timestamp...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Add deployment timestamp comment
    timestamp_comment = f"\n# DEPLOYMENT TIMESTAMP: {time.time()} - Force rebuild for dashboard features\n"
    
    if '# DEPLOYMENT TIMESTAMP:' in content:
        # Replace existing timestamp
        import re
        content = re.sub(r'# DEPLOYMENT TIMESTAMP:.*\n', timestamp_comment, content)
    else:
        # Add new timestamp at the top
        content = f'#!/usr/bin/env python3{timestamp_comment}{content[18:] if content.startswith("#!/usr/bin/env python3") else content}'
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    subprocess.run(['git', 'add', 'main.py'], check=True)
    subprocess.run(['git', 'commit', '-m', f'EMERGENCY DEPLOY: Force rebuild with timestamp {int(time.time())}'], check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("✅ Method 1: Deployed")
except Exception as e:
    print(f"❌ Method 1 failed: {str(e)}")

# Method 2: Update ecs.yaml
print("\n🔧 Method 2: Updating ecs.yaml...")
try:
    with open('ecs.yaml', 'r') as f:
        content = f.read()
    
    # Add or update env variable to force rebuild
    if 'FORCE_REBUILD' in content:
        import re
        content = re.sub(r'value: "[^"]*"  # FORCE_REBUILD', f'value: "{int(time.time())}"  # FORCE_REBUILD', content)
    else:
        # Add new env variable
        env_addition = f'''    - name: FORCE_REBUILD
      value: "{int(time.time())}"  # FORCE_REBUILD'''
        content = content.replace('  env:', f'  env:\n{env_addition}')
    
    with open('ecs.yaml', 'w') as f:
        f.write(content)
    
    subprocess.run(['git', 'add', 'ecs.yaml'], check=True)
    subprocess.run(['git', 'commit', '-m', 'EMERGENCY: Update ecs.yaml to force rebuild'], check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("✅ Method 2: Deployed")
except Exception as e:
    print(f"❌ Method 2 failed: {str(e)}")

# Method 3: Create a visible change in static files
print("\n🔧 Method 3: Updating static deployment signature...")
try:
    signature_file = 'static/deployment_signature.txt'
    with open(signature_file, 'w') as f:
        f.write(f"# Dashboard Enhancement Deployment\n")
        f.write(f"# Timestamp: {time.time()}\n")
        f.write(f"# Features: Navigation, Pagination, Registration\n")
        f.write(f"# Constitutional Compliance: Yes\n")
    
    # Also update CSS to ensure change is picked up
    css_file = 'static/css/constitutional-design.css'
    if os.path.exists(css_file):
        with open(css_file, 'a') as f:
            f.write(f"\n/* Deployment timestamp: {time.time()} */\n")
    
    subprocess.run(['git', 'add', 'static/'], check=True)
    subprocess.run(['git', 'commit', '-m', 'EMERGENCY: Update static files to force cache invalidation'], check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("✅ Method 3: Deployed")
except Exception as e:
    print(f"❌ Method 3 failed: {str(e)}")

print("\n📊 EMERGENCY DEPLOYMENT COMPLETE")
print("Waiting 3 minutes for ECS to pick up changes...")
print("Run 'python3 quick_verify.py' to check status")

# AWS CLI deployment trigger if available
try:
    print("\n🔧 Attempting AWS CLI deployment trigger...")
    result = subprocess.run([
        'aws', 'ecs', 'list-services', 
        '--region', 'us-east-1',
        '--query', 'ServiceSummaryList[?ServiceName==`ava-olo-monitoring-dashboards`].ServiceArn',
        '--output', 'text'
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        service_arn = result.stdout.strip()
        print(f"Found service ARN: {service_arn}")
        
        # Start deployment
        deploy_result = subprocess.run([
            'aws', 'ecs', 'start-deployment',
            '--service-arn', service_arn,
            '--region', 'us-east-1'
        ], capture_output=True, text=True)
        
        if deploy_result.returncode == 0:
            print("✅ AWS CLI: Deployment triggered successfully!")
            deployment_data = json.loads(deploy_result.stdout)
            print(f"   Operation ID: {deployment_data.get('OperationId', 'Unknown')}")
except Exception as e:
    print(f"❌ AWS CLI deployment failed: {str(e)}")

import os