#!/usr/bin/env python3
"""
Security Fixes Verification Test
Tests all implemented security measures
"""

import requests
import json
import time
import os
from urllib3.exceptions import InsecureRequestWarning
from utils.password_security import PasswordSecurity

# Suppress SSL warnings for testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class SecurityTester:
    def __init__(self):
        self.test_results = []
        self.base_urls = [
            "http://localhost:8080",  # Agricultural Core
            "http://localhost:8000",  # Monitoring API
            "http://localhost:8004",  # Business Dashboard
        ]
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_dashboard_authentication(self):
        """Test that dashboards require authentication"""
        print("\n🔐 Testing Dashboard Authentication")
        print("-" * 40)
        
        for base_url in self.base_urls:
            try:
                # Test 1: Unauthenticated access should redirect to login
                response = requests.get(f"{base_url}/", allow_redirects=False, timeout=5)
                
                if response.status_code in [401, 302]:
                    self.log_test(f"Auth required - {base_url}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"Auth required - {base_url}", False, f"Unexpected status: {response.status_code}")
                
                # Test 2: Login page should be accessible
                login_response = requests.get(f"{base_url}/login", timeout=5)
                
                if login_response.status_code == 200 and "login" in login_response.text.lower():
                    self.log_test(f"Login page - {base_url}", True, "Login page accessible")
                else:
                    self.log_test(f"Login page - {base_url}", False, f"Status: {login_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"Connection - {base_url}", False, f"Service not running: {str(e)[:50]}")
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        print("\n🔒 Testing Password Hashing")
        print("-" * 40)
        
        test_password = "TestPassword123!"
        
        # Test bcrypt hashing
        try:
            bcrypt_hash = PasswordSecurity.hash_password(test_password, use_bcrypt=True)
            bcrypt_verify = PasswordSecurity.verify_password(test_password, bcrypt_hash)
            
            self.log_test("bcrypt hashing", bcrypt_verify and bcrypt_hash.startswith("bcrypt:"), 
                         f"Hash format: {bcrypt_hash[:20]}...")
            
            # Test wrong password
            wrong_verify = PasswordSecurity.verify_password("WrongPassword", bcrypt_hash)
            self.log_test("bcrypt wrong password rejection", not wrong_verify, "Correctly rejected wrong password")
            
        except Exception as e:
            self.log_test("bcrypt hashing", False, f"Error: {e}")
        
        # Test SHA256 hashing
        try:
            sha256_hash = PasswordSecurity.hash_password(test_password, use_bcrypt=False)
            sha256_verify = PasswordSecurity.verify_password(test_password, sha256_hash)
            
            self.log_test("SHA256 hashing", sha256_verify and sha256_hash.startswith("sha256:"),
                         f"Hash format: {sha256_hash[:20]}...")
            
        except Exception as e:
            self.log_test("SHA256 hashing", False, f"Error: {e}")
    
    def test_environment_security(self):
        """Test environment security"""
        print("\n🔧 Testing Environment Security")
        print("-" * 40)
        
        # Check .env file security
        env_file = "/mnt/c/Users/HP/ava_olo_project/.env"
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Check for weak passwords
            weak_indicators = ['password=password', 'DB_PASSWORD=password']
            has_weak = any(indicator in env_content for indicator in weak_indicators)
            
            self.log_test("No weak passwords in .env", not has_weak, 
                         "Checked for default passwords" if not has_weak else "Found weak passwords")
            
            # Check for CHANGE_THIS indicators
            has_placeholders = 'CHANGE_THIS' in env_content
            self.log_test("Password placeholders present", has_placeholders,
                         "Found CHANGE_THIS placeholders" if has_placeholders else "No placeholders found")
            
        except FileNotFoundError:
            self.log_test("Environment file check", False, ".env file not found")
    
    def test_task_definition_security(self):
        """Test task definition security"""
        print("\n☁️ Testing Task Definition Security")
        print("-" * 40)
        
        task_files = [
            "/mnt/c/Users/HP/ava_olo_project/task-definition-agricultural-constitutional.json",
            "/mnt/c/Users/HP/ava_olo_project/task-definition-monitoring-constitutional.json"
        ]
        
        for task_file in task_files:
            try:
                with open(task_file, 'r') as f:
                    task_def = json.load(f)
                
                # Check for secrets configuration
                container = task_def['containerDefinitions'][0]
                has_secrets = 'secrets' in container
                
                # Check for hardcoded passwords in environment
                env_vars = container.get('environment', [])
                has_hardcoded_password = any(
                    env['name'] == 'DB_PASSWORD' for env in env_vars
                )
                
                filename = task_file.split('/')[-1]
                self.log_test(f"Secrets Manager config - {filename}", has_secrets,
                             "Uses AWS Secrets Manager" if has_secrets else "No secrets config found")
                
                self.log_test(f"No hardcoded passwords - {filename}", not has_hardcoded_password,
                             "No hardcoded DB_PASSWORD" if not has_hardcoded_password else "Found hardcoded password")
                
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.log_test(f"Task definition check - {task_file}", False, f"Error: {e}")
    
    def test_security_headers(self):
        """Test security headers implementation"""
        print("\n🛡️ Testing Security Headers")
        print("-" * 40)
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Content-Security-Policy'
        ]
        
        for base_url in self.base_urls:
            try:
                response = requests.get(f"{base_url}/health", timeout=5, verify=False)
                
                headers_present = []
                for header in required_headers:
                    if header in response.headers:
                        headers_present.append(header)
                
                all_present = len(headers_present) == len(required_headers)
                self.log_test(f"Security headers - {base_url}", all_present,
                             f"Present: {len(headers_present)}/{len(required_headers)}")
                
            except requests.exceptions.RequestException:
                self.log_test(f"Security headers - {base_url}", False, "Service not accessible")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 AVA OLO Security Fixes Verification")
        print("=" * 50)
        
        self.test_dashboard_authentication()
        self.test_password_hashing()
        self.test_environment_security()
        self.test_task_definition_security()
        self.test_security_headers()
        
        # Generate summary
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if failed_tests == 0 else '⚠️ SOME TESTS FAILED'}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = SecurityTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)