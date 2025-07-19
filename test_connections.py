#!/usr/bin/env python3
"""Test multiple connection methods to find working approach"""

import subprocess
import sys
import time

def try_connection_method(method_name, command):
    print(f'🔍 Trying {method_name}...')
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f'✅ {method_name}: SUCCESS')
            print(result.stdout[:200])
            return True
        else:
            print(f'❌ {method_name}: FAILED - {result.stderr[:100]}')
            return False
    except subprocess.TimeoutExpired:
        print(f'⏰ {method_name}: TIMEOUT')
        return False
    except Exception as e:
        print(f'❌ {method_name}: ERROR - {str(e)}')
        return False

# Test different URLs found in the codebase
urls = [
    'https://6pmgiripe.us-east-1.awsapprunner.com/',
    'https://6pmgrirjre.us-east-1.awsapprunner.com/',
    'https://6pmgrirjre.us-east-1.awsapprunner.com/ui-dashboard'
]

for url in urls:
    print(f'\n🌐 Testing URL: {url}')
    
    # Method 1: Direct curl
    success1 = try_connection_method(
        f'Direct cURL to {url}',
        f'curl -s -o /dev/null -w "%{{http_code}}" {url}'
    )

# Method 2: AWS CLI (if credentials available)
success2 = try_connection_method(
    'AWS CLI App Runner',
    'aws apprunner list-services --region us-east-1 2>/dev/null || echo "AWS CLI not configured"'
)

# Method 3: DNS resolution check
for url in urls:
    hostname = url.split('//')[1].split('/')[0]
    success3 = try_connection_method(
        f'DNS Resolution for {hostname}',
        f'nslookup {hostname}'
    )

# Method 4: Alternative HTTP libraries
try:
    import urllib.request
    for url in urls:
        try:
            print(f'🔍 Trying urllib with {url}...')
            response = urllib.request.urlopen(url, timeout=10)
            print(f'✅ urllib: SUCCESS - Status {response.status} for {url}')
            # Try to read content
            content = response.read().decode('utf-8')
            if 'dashboard' in content.lower() or 'navigation' in content.lower():
                print(f'✅ FOUND DASHBOARD CONTENT at {url}!')
                print(f'Working URL: {url}')
            break
        except Exception as e:
            print(f'❌ urllib failed for {url}: {str(e)}')
except Exception as e:
    print(f'❌ urllib import failed: {str(e)}')

# Method 5: Try with curl and check content
for url in urls:
    print(f'\n📋 Checking content at {url}')
    try:
        result = subprocess.run(
            f'curl -s {url} | head -20',
            shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout:
            print(f'✅ Got content from {url}:')
            print(result.stdout[:200])
    except:
        pass