#!/usr/bin/env python3
"""
Monitor deployment until version v2.1.3 is visible on production
"""

import requests
import time
import json
from datetime import datetime

def check_version_deployment():
    """Check if version v2.1.3 is deployed and visible"""
    
    url = "https://6pmgrirjre.us-east-1.awsapprunner.com/"
    expected_version = "v2.1.3"
    
    print("🔍 MONITORING VERSION DEPLOYMENT")
    print("=" * 40)
    print(f"Expected Version: {expected_version}")
    print(f"Checking URL: {url}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 40)
    
    attempt = 0
    max_attempts = 30  # 10 minutes max
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            print(f"[{attempt:2d}] {datetime.now().strftime('%H:%M:%S')} - Checking deployment...")
            
            # Check main page for version
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for version in HTML
                if expected_version in content:
                    print(f"✅ SUCCESS! Version {expected_version} found in page content!")
                    
                    # Try to extract version display location
                    if 'constitutional-version' in content:
                        print("✅ Version display element found!")
                    else:
                        print("⚠️  Version found but display element not detected")
                    
                    return True
                
                # Check for template variables (debugging)
                if 'current_version' in content:
                    print("⚠️  Template variable 'current_version' found but not rendered")
                elif '{{ current_version }}' in content:
                    print("❌ Template variable not being processed - template engine issue")
                else:
                    print("❌ No version-related content found")
                
                # Check for recent changes
                if 'constitutional' in content.lower():
                    print("✅ Constitutional design CSS is loading")
                else:
                    print("❌ Constitutional design CSS not found - old version")
                    
            else:
                print(f"❌ HTTP {response.status_code} - Service not accessible")
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
        
        if attempt < max_attempts:
            print("   Waiting 20 seconds for next check...")
            time.sleep(20)
        
    print(f"\n❌ TIMEOUT: Version {expected_version} not deployed after {max_attempts} attempts")
    print("This indicates the deployment is still in progress or failed.")
    return False

def check_template_engine_debug():
    """Debug template engine issues"""
    
    print("\n🔧 TEMPLATE ENGINE DEBUG")
    print("=" * 40)
    
    url = "https://6pmgrirjre.us-east-1.awsapprunner.com/"
    
    try:
        response = requests.get(url, timeout=10)
        content = response.text
        
        # Check for template rendering issues
        debug_checks = {
            "Jinja2 variables not rendered": "{{" in content and "}}" in content,
            "Template extends working": "<!DOCTYPE html>" in content,
            "CSS loading": "constitutional-design.css" in content,
            "Base template": "AVA OLO" in content,
            "Version variable": "current_version" in content
        }
        
        for check_name, has_issue in debug_checks.items():
            status = "❌" if has_issue else "✅"
            print(f"{status} {check_name}")
        
        return not any(debug_checks.values())
        
    except Exception as e:
        print(f"❌ Debug check failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting version deployment monitoring...")
    
    # First check current status
    success = check_version_deployment()
    
    if not success:
        # If version not found, debug template issues
        template_ok = check_template_engine_debug()
        
        if not template_ok:
            print("\n🚨 TEMPLATE ENGINE ISSUES DETECTED")
            print("Recommended actions:")
            print("1. Check if FastAPI template engine is properly initialized")
            print("2. Verify version injection function is working")
            print("3. Check if deployment included latest changes")
    
    print(f"\nMonitoring completed at {datetime.now().strftime('%H:%M:%S')}")