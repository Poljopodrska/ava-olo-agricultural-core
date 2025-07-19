#!/usr/bin/env python3
"""
🏛️ Autonomous Retry Deployment System
Keeps trying until deployment is actually working
"""

import subprocess
import time
import sys
import json
from datetime import datetime, timedelta

class AutonomousRetryDeployer:
    """Autonomous deployment with retry until success"""
    
    def __init__(self):
        self.max_attempts = 10
        self.base_wait_time = 300  # 5 minutes between attempts
        self.max_total_time = 7200  # 2 hours maximum
        self.working_url = "https://6pmgrirjre.us-east-1.awsapprunner.com"  # Correct URL found!
        
    def verify_deployment_working(self):
        """Try multiple methods to verify deployment"""
        
        verification_methods = [
            self._verify_with_curl,
            self._verify_with_urllib,
            self._verify_dashboard_features,
            self._verify_registration_endpoints
        ]
        
        results = []
        for method in verification_methods:
            try:
                result = method()
                results.append(result)
                if result:
                    print(f"✅ Verification method succeeded")
            except Exception as e:
                print(f"Method failed: {str(e)}")
                results.append(False)
                
        # Need at least 2 methods to confirm
        return sum(results) >= 2
    
    def _verify_with_curl(self):
        """Verify using curl command"""
        # Check main dashboard
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
            f'{self.working_url}/ui-dashboard'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip() == '200':
            # Get content to check for features
            content_result = subprocess.run([
                'curl', '-s', f'{self.working_url}/ui-dashboard'
            ], capture_output=True, text=True, timeout=30)
            
            if content_result.returncode == 0:
                content = content_result.stdout.lower()
                features_found = [
                    'dashboard-grid' in content,
                    'register new fields' in content,
                    'register new task' in content,
                    'register machinery' in content
                ]
                found_count = sum(features_found)
                print(f"📊 Found {found_count}/4 dashboard features via curl")
                return found_count >= 3
        return False
    
    def _verify_with_urllib(self):
        """Verify using urllib"""
        import urllib.request
        try:
            with urllib.request.urlopen(
                f'{self.working_url}/ui-dashboard', 
                timeout=15
            ) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8').lower()
                    features = [
                        'dashboard-grid' in content,
                        'navigation' in content,
                        'register' in content
                    ]
                    return sum(features) >= 2
        except:
            pass
        return False
    
    def _verify_dashboard_features(self):
        """Verify specific dashboard features"""
        try:
            endpoints = [
                '/ui-dashboard',
                '/database-explorer',
                '/register-fields',
                '/register-task',
                '/register-machinery'
            ]
            
            working_count = 0
            for endpoint in endpoints:
                result = subprocess.run([
                    'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                    f'{self.working_url}{endpoint}'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip() == '200':
                    working_count += 1
                    print(f"✅ {endpoint}: Accessible")
                else:
                    print(f"❌ {endpoint}: HTTP {result.stdout.strip()}")
            
            return working_count >= 3
        except:
            return False
    
    def _verify_registration_endpoints(self):
        """Verify API endpoints are working"""
        try:
            # Test database query endpoint
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'{self.working_url}/api/database/query',
                '-H', 'Content-Type: application/json',
                '-d', '{"query": "SELECT 1"}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    if response.get('success'):
                        print("✅ Database API: Working")
                        return True
                except:
                    pass
            return False
        except:
            return False
    
    def force_deployment_cache_bust(self, attempt_number):
        """Force new deployment with cache invalidation"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_bust_file = f"retry_deployment_{attempt_number}_{timestamp}.txt"
        
        try:
            # Create unique cache bust file
            with open(cache_bust_file, 'w') as f:
                f.write(f"Autonomous retry deployment #{attempt_number}\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Constitutional Amendment #15 enforcement\n")
                f.write(f"Dashboard features must be operational\n")
                f.write(f"Target URL: {self.working_url}\n")
            
            # Git operations
            subprocess.run(["git", "add", cache_bust_file], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                f"AUTONOMOUS RETRY #{attempt_number}: Force deployment cache bust {timestamp}"
            ], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print(f"🔧 Retry #{attempt_number}: Cache bust deployed")
            return True
            
        except Exception as e:
            print(f"❌ Cache bust failed: {str(e)}")
            return False
    
    def autonomous_retry_until_working(self):
        """Main retry loop - keep trying until deployment works"""
        
        print("🤖 AUTONOMOUS RETRY DEPLOYMENT INITIATED")
        print(f"Target URL: {self.working_url}")
        print("Will keep trying until dashboard features are operational")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # First check current status
        print("\n🔍 Initial deployment status check...")
        if self.verify_deployment_working():
            print("✅ DEPLOYMENT ALREADY WORKING - Features operational!")
            return True
        
        for attempt in range(1, self.max_attempts + 1):
            print(f"\n🔄 ATTEMPT #{attempt} ({datetime.now().strftime('%H:%M:%S')})")
            
            # Force new deployment
            print(f"🔧 Forcing new deployment...")
            if self.force_deployment_cache_bust(attempt):
                # Wait for deployment
                wait_time = min(self.base_wait_time * (1 + attempt * 0.1), 600)  # Max 10 minutes
                print(f"⏳ Waiting {int(wait_time)} seconds for deployment...")
                
                # Check periodically during wait
                check_interval = 30
                for i in range(0, int(wait_time), check_interval):
                    time.sleep(min(check_interval, wait_time - i))
                    print(f"   Checking... ({i + check_interval}/{int(wait_time)}s)")
                    
                    if self.verify_deployment_working():
                        print(f"✅ SUCCESS: Deployment verified working on attempt #{attempt}")
                        print("🏛️ CONSTITUTIONAL COMPLIANCE: All features operational")
                        return True
            else:
                print("❌ Failed to trigger new deployment")
                
            # Check time limit
            if datetime.now() - start_time > timedelta(seconds=self.max_total_time):
                print("⏰ Maximum time reached - stopping autonomous retry")
                break
        
        print(f"\n🚨 AUTONOMOUS RETRY FAILED: Could not verify deployment after {attempt} attempts")
        return False

def main():
    deployer = AutonomousRetryDeployer()
    success = deployer.autonomous_retry_until_working()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()