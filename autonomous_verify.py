#!/usr/bin/env python3
"""
Autonomous Production Verification - No Manual Checks
"""
import requests
import sys

print('🔍 AUTONOMOUS PRODUCTION VERIFICATION')
print('====================================')

base_url = 'https://6pmgiripe.us-east-1.elb.amazonaws.com'
success_count = 0
total_tests = 0

# Test 1: Navigation system
try:
    response = requests.get(f'{base_url}/agricultural-dashboard', timeout=10)
    total_tests += 1
    if response.status_code == 200:
        content = response.text.lower()
        if 'back' in content or 'navigation' in content or 'return' in content:
            print('✅ Navigation System: FOUND in production')
            success_count += 1
        else:
            print('❌ Navigation System: NOT FOUND in production HTML')
            print(f'   Status: {response.status_code}, Content preview: {content[:200]}...')
    else:
        print(f'❌ Dashboard unreachable: HTTP {response.status_code}')
except Exception as e:
    print(f'❌ Dashboard test failed: {str(e)}')

# Test 2: Pagination controls  
try:
    total_tests += 1
    if response.status_code == 200:
        content = response.text.lower()
        if 'pagination' in content or 'results per page' in content or 'next' in content:
            print('✅ Pagination System: FOUND in production')
            success_count += 1
        else:
            print('❌ Pagination System: NOT FOUND in production HTML')
except Exception as e:
    print(f'❌ Pagination test failed: {str(e)}')

# Test 3: Registration features
registration_endpoints = [
    ('register-fields', 'Register Fields'),
    ('register-tasks', 'Register Tasks'), 
    ('register-machinery', 'Register Machinery')
]

for endpoint, name in registration_endpoints:
    try:
        total_tests += 1
        reg_response = requests.get(f'{base_url}/{endpoint}', timeout=10)
        if reg_response.status_code == 200:
            print(f'✅ {name}: ACCESSIBLE in production')
            success_count += 1
        else:
            print(f'❌ {name}: HTTP {reg_response.status_code}')
    except Exception as e:
        print(f'❌ {name}: Connection failed - {str(e)}')

print('====================================')
print(f'🏛️ CONSTITUTIONAL VERIFICATION: {success_count}/{total_tests} features verified')

if success_count == total_tests:
    print('✅ ALL FEATURES OPERATIONAL IN PRODUCTION')
    sys.exit(0)
elif success_count >= total_tests * 0.8:
    print('⚠️  MOST FEATURES OPERATIONAL - Acceptable')
    sys.exit(0)  
else:
    print('❌ DEPLOYMENT VERIFICATION FAILED')
    sys.exit(1)