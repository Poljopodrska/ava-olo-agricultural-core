#!/usr/bin/env python3
"""Quick verification of deployment status"""

import subprocess
import urllib.request

url = "https://6pmgrirjre.us-east-1.elb.amazonaws.com"

print("🔍 QUICK DEPLOYMENT VERIFICATION")
print("=" * 40)

# Check main page
try:
    with urllib.request.urlopen(f"{url}/", timeout=10) as response:
        if response.status == 200:
            content = response.read().decode('utf-8')
            print(f"✅ Main page: Accessible")
            if 'UI Dashboard' in content:
                print("   Found: UI Dashboard link")
        else:
            print(f"❌ Main page: HTTP {response.status}")
except Exception as e:
    print(f"❌ Main page: {str(e)}")

# Check UI dashboard
try:
    result = subprocess.run(
        f'curl -s {url}/ui-dashboard | grep -E "dashboard-grid|Register New|pagination|navigation" | wc -l',
        shell=True, capture_output=True, text=True
    )
    feature_count = int(result.stdout.strip()) if result.stdout.strip() else 0
    
    if feature_count > 0:
        print(f"✅ UI Dashboard: Found {feature_count} new features!")
        
        # Get specific features
        features_check = subprocess.run(
            f'curl -s {url}/ui-dashboard',
            shell=True, capture_output=True, text=True
        )
        
        content = features_check.stdout.lower()
        features = {
            'Dashboard Grid': 'dashboard-grid' in content,
            'Register Fields': 'register new fields' in content or 'register-fields' in content,
            'Register Tasks': 'register new task' in content or 'register-task' in content,
            'Register Machinery': 'register machinery' in content or 'register-machinery' in content,
            'Navigation': 'navigation' in content or 'back' in content,
            'Pagination': 'pagination' in content or 'results per page' in content
        }
        
        print("\n📊 Feature Status:")
        for name, found in features.items():
            status = "✅" if found else "❌"
            print(f"   {status} {name}")
            
        if sum(features.values()) >= 4:
            print("\n🎉 DEPLOYMENT SUCCESSFUL - Dashboard enhancements are live!")
        else:
            print(f"\n⚠️  Only {sum(features.values())}/6 features found")
    else:
        print("❌ UI Dashboard: No new features detected")
        
        # Check if old version
        old_check = subprocess.run(
            f'curl -s {url}/ui-dashboard | grep -i "test ui\\|api gateway" | wc -l',
            shell=True, capture_output=True, text=True
        )
        if int(old_check.stdout.strip()) > 0:
            print("   ⚠️  Old dashboard version still deployed")
            
except Exception as e:
    print(f"❌ UI Dashboard check failed: {str(e)}")

# Check new endpoints
print("\n🔍 Checking new endpoints:")
endpoints = ['/register-fields', '/register-task', '/register-machinery']
for endpoint in endpoints:
    try:
        result = subprocess.run(
            f'curl -s -o /dev/null -w "%{{http_code}}" {url}{endpoint}',
            shell=True, capture_output=True, text=True
        )
        status_code = result.stdout.strip()
        if status_code == "200":
            print(f"   ✅ {endpoint}: Accessible")
        else:
            print(f"   ❌ {endpoint}: HTTP {status_code}")
    except:
        print(f"   ❌ {endpoint}: Failed")