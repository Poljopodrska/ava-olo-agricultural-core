#!/usr/bin/env python3
"""Verify restoration to normal version without unicorn"""
import subprocess
import time
from datetime import datetime

def check_restoration():
    """Check if service is restored to normal"""
    print(f"\n🔍 CHECKING RESTORATION - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    endpoints = [
        ("Landing Page", "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"),
        ("Version API", "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version")
    ]
    
    for name, url in endpoints:
        print(f"\n{name}: {url}")
        cmd = f"curl -s {url}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            # Check for unicorn remnants
            if "UNICORN" in result.stdout or "🦄" in result.stdout:
                print("❌ Still showing unicorn test!")
                return False
            elif "pink" in result.stdout:
                print("❌ Still showing pink background!")
                return False
            elif "3.3.25" in result.stdout:
                print("✅ Shows v3.3.25 - restoration in progress!")
                if name == "Landing Page" and "Portal del Agricultor" in result.stdout:
                    print("✅ Normal landing page restored!")
                    return True
            elif "3.3.24" in result.stdout:
                print("⏳ Still showing v3.3.24, waiting for deployment...")
            else:
                print("✅ No unicorn elements found")
    
    return False

def main():
    print("🔄 MONITORING RESTORATION TO NORMAL VERSION")
    print("Target: v3.3.25-stable without unicorn test")
    
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    while time.time() - start_time < timeout:
        if check_restoration():
            print("\n\n✅ SUCCESS! Service restored to normal!")
            print("No more unicorns, back to business!")
            
            # Final verification
            print("\n📋 Final Check:")
            cmd = "curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/version"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"Version endpoint: {result.stdout}")
            break
        
        print("\n⏳ Waiting 30 seconds before next check...")
        time.sleep(30)
    else:
        print("\n\n⏱️ Monitoring period ended")
        print("Check deployment status manually")

if __name__ == "__main__":
    main()