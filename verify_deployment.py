#!/usr/bin/env python3
"""
Final Constitutional Verification Script
Checks if dashboard enhancements are deployed to AWS
"""

import requests
import sys
import time

def verify_deployment():
    base_url = 'https://6pmgiripe.us-east-1.awsapprunner.com'
    
    print('🔍 FINAL CONSTITUTIONAL VERIFICATION:')
    print('=====================================')
    
    verification_results = []
    
    # Test main dashboard
    try:
        response = requests.get(f'{base_url}/ui-dashboard', timeout=10)
        if response.status_code == 200:
            # Check for new dashboard features
            content = response.text.lower()
            if 'dashboard-grid' in content or 'register new fields' in content:
                print('✅ Enhanced Dashboard: VERIFIED')
                verification_results.append(True)
            else:
                print('❌ Enhanced Dashboard: OLD VERSION STILL DEPLOYED')
                verification_results.append(False)
        else:
            print(f'❌ Dashboard: HTTP {response.status_code}')
            verification_results.append(False)
    except Exception as e:
        print(f'❌ Dashboard: ERROR - {str(e)}')
        verification_results.append(False)
    
    # Test navigation system
    try:
        if 'back' in content or 'navigation' in content:
            print('✅ Navigation System: VERIFIED')
            verification_results.append(True)
        else:
            print('❌ Navigation System: MISSING')
            verification_results.append(False)
    except:
        print('❌ Navigation System: ERROR')
        verification_results.append(False)
    
    # Test new registration features
    registration_features = [
        ('register-fields', 'Register Fields'),
        ('register-task', 'Register Tasks'), 
        ('register-machinery', 'Register Machinery')
    ]
    
    for endpoint, name in registration_features:
        try:
            test_response = requests.get(f'{base_url}/{endpoint}', timeout=10)
            if test_response.status_code == 200:
                print(f'✅ {name}: ACCESSIBLE')
                verification_results.append(True)
            else:
                print(f'❌ {name}: HTTP {test_response.status_code}')
                verification_results.append(False)
        except Exception as e:
            print(f'❌ {name}: ERROR - {str(e)}')
            verification_results.append(False)
    
    # Test database explorer pagination
    try:
        db_response = requests.get(f'{base_url}/database-explorer', timeout=10)
        if db_response.status_code == 200:
            if 'pagination' in db_response.text.lower() or 'results per page' in db_response.text.lower():
                print('✅ Pagination System: VERIFIED')
                verification_results.append(True)
            else:
                print('❌ Pagination System: MISSING')
                verification_results.append(False)
        else:
            print(f'❌ Database Explorer: HTTP {db_response.status_code}')
            verification_results.append(False)
    except Exception as e:
        print(f'❌ Database Explorer: ERROR - {str(e)}')
        verification_results.append(False)
    
    print('=====================================')
    print('🏛️ Constitutional Amendment #15: Applied')
    print('📋 All future deployments now require AWS verification')
    print('=====================================')
    
    # Summary
    success_count = sum(verification_results)
    total_count = len(verification_results)
    
    if all(verification_results):
        print(f'✅ DEPLOYMENT VERIFICATION: PASSED ({success_count}/{total_count})')
        print('🏛️ CONSTITUTIONAL COMPLIANCE: ACHIEVED')
        return True
    else:
        print(f'❌ DEPLOYMENT VERIFICATION: FAILED ({success_count}/{total_count})')
        print('🚨 CONSTITUTIONAL VIOLATION: Features not fully deployed')
        print('\n🔧 REQUIRED ACTIONS:')
        print('1. Check AWS App Runner console for deployment status')
        print('2. Verify GitHub webhook is configured correctly')
        print('3. Force manual deployment if needed')
        print('4. Clear CloudFront/CDN cache if applicable')
        return False

if __name__ == "__main__":
    # Wait for deployment to propagate
    print("⏳ Waiting 60 seconds for deployment to propagate...")
    time.sleep(60)
    
    success = verify_deployment()
    sys.exit(0 if success else 1)