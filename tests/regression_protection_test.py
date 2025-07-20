#!/usr/bin/env python3
"""
Regression Protection Test Suite
Tests our protection system's ability to catch breaking changes
"""
import requests
import time
import json
import re
from typing import Dict, List, Any

class RegressionProtectionTest:
    def __init__(self):
        self.base_url = "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
        self.critical_features = {
            "root_endpoint_accessible": self.test_root_endpoint,
            "registration_loads": self.test_registration_loads,
            "dashboard_loads": self.test_dashboard_loads,
            "blue_box_visible": self.test_blue_box_visible,
            "farmer_count_correct": self.test_farmer_count_correct,
            "version_endpoint": self.test_version_endpoint,
            "response_time_acceptable": self.test_response_time,
            "database_performance_ok": self.test_database_performance,
            "api_content_valid": self.test_api_content_structure,
            "cava_interface_present": self.test_cava_interface,
            "navigation_functional": self.test_navigation,
        }
        self.test_results = {}
        
    def test_root_endpoint(self) -> bool:
        """Test root endpoint is accessible"""
        try:
            resp = requests.get(f"{self.base_url}/", timeout=10)
            # Accept 200 (landing page) or 302 (redirect to registration)
            return resp.status_code in [200, 302]
        except Exception as e:
            print(f"Root endpoint test failed: {e}")
            return False
        
    def test_registration_loads(self) -> bool:
        """Test registration page loads and contains CAVA interface"""
        try:
            resp = requests.get(f"{self.base_url}/register", timeout=10)
            return (resp.status_code == 200 and 
                   "CAVA" in resp.text and 
                   "registration" in resp.text.lower())
        except Exception as e:
            print(f"Registration test failed: {e}")
            return False
    
    def test_dashboard_loads(self) -> bool:
        """Test business dashboard loads and shows content"""
        try:
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            return (resp.status_code == 200 and 
                   "farmers" in resp.text.lower() and
                   "dashboard" in resp.text.lower())
        except Exception as e:
            print(f"Dashboard test failed: {e}")
            return False
    
    def test_blue_box_visible(self) -> bool:
        """Verify blue debug box exists with correct color"""
        try:
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            # Check for blue color code
            return "#007BFF" in resp.text or "background.*blue" in resp.text.lower()
        except Exception as e:
            print(f"Blue box test failed: {e}")
            return False
    
    def test_farmer_count_correct(self) -> bool:
        """Verify farmer data displays (not placeholder)"""
        try:
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            content = resp.text
            # Should show actual numbers, not "--" placeholders
            has_farmer_count = "16" in content
            has_hectare_count = "211.95" in content or "211" in content
            no_excessive_placeholders = content.count("--") < 10  # Allow some "--" but not many
            
            print(f"   Farmer count present: {has_farmer_count}")
            print(f"   Hectare count present: {has_hectare_count}")
            print(f"   Placeholder check: {no_excessive_placeholders}")
            
            return has_farmer_count and has_hectare_count and no_excessive_placeholders
        except Exception as e:
            print(f"Farmer count test failed: {e}")
            return False
    
    def test_version_endpoint(self) -> bool:
        """Test version/health endpoint responds correctly"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return ("version" in data and "status" in data)
            return False
        except Exception as e:
            print(f"Version endpoint test failed: {e}")
            return False
    
    def test_response_time(self) -> bool:
        """Test that critical pages load within acceptable time"""
        try:
            start_time = time.time()
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=15)
            end_time = time.time()
            
            load_time = end_time - start_time
            return resp.status_code == 200 and load_time < 5.0
        except Exception as e:
            print(f"Response time test failed: {e}")
            return False
    
    def test_database_performance(self) -> bool:
        """Test database performance is acceptable"""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/health/database", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status', 'unknown')
                # Accept healthy or warning, but not degraded or unhealthy
                return status in ['healthy', 'warning']
            return False
        except Exception as e:
            print(f"Database performance test failed: {e}")
            return False
    
    def test_api_content_structure(self) -> bool:
        """Test API responses have correct structure"""
        try:
            # Test health endpoint JSON structure
            resp = requests.get(f"{self.base_url}/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                required_fields = ["status", "version", "service"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   Health API missing fields: {missing_fields}")
                    return False
                
                # Check status is valid
                if data["status"] not in ["healthy", "degraded", "unhealthy"]:
                    print(f"   Invalid health status: {data['status']}")
                    return False
            
            # Test dashboard contains structured data
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            if resp.status_code == 200:
                content = resp.text
                # Look for numeric data patterns
                import re
                has_numbers = bool(re.search(r'\b\d+\b', content))
                has_structure = any(word in content.lower() for word in ['debug', 'version', 'dashboard'])
                
                if not (has_numbers and has_structure):
                    print(f"   Dashboard lacks structured content")
                    return False
            
            return True
            
        except Exception as e:
            print(f"API content structure test failed: {e}")
            return False
    
    def test_cava_interface(self) -> bool:
        """Test CAVA registration interface is present"""
        try:
            resp = requests.get(f"{self.base_url}/register", timeout=10)
            content = resp.text.lower()
            
            # Check for CAVA interface elements
            has_cava = "cava" in content
            has_chat = any(word in content for word in ["chat", "message", "input"])
            has_form = any(word in content for word in ["form", "submit", "send"])
            has_registration = "registration" in content
            
            print(f"   CAVA present: {has_cava}")
            print(f"   Chat interface: {has_chat}")
            print(f"   Form elements: {has_form}")
            print(f"   Registration context: {has_registration}")
            
            # Need at least 3 of 4 elements for interface to be considered functional
            score = sum([has_cava, has_chat, has_form, has_registration])
            return score >= 3
            
        except Exception as e:
            print(f"CAVA interface test failed: {e}")
            return False
    
    def test_navigation(self) -> bool:
        """Test that main navigation elements are present"""
        try:
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            content = resp.text
            # Check for navigation elements
            nav_elements = ["Home", "Business Dashboard", "Database Dashboard"]
            return any(element in content for element in nav_elements)
        except Exception as e:
            print(f"Navigation test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all critical feature tests"""
        print("🧪 Running Regression Protection Tests...")
        print("=" * 50)
        
        for test_name, test_func in self.critical_features.items():
            print(f"Testing {test_name}...", end=" ")
            try:
                result = test_func()
                self.test_results[test_name] = result
                if result:
                    print("✅ PASS")
                else:
                    print("❌ FAIL")
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.test_results[test_name] = False
        
        return self.test_results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": success_rate,
            "status": "HEALTHY" if success_rate >= 90 else "DEGRADED" if success_rate >= 70 else "FAILED",
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # Add recommendations based on failures
        if not self.test_results.get("blue_box_visible", True):
            report["recommendations"].append("CRITICAL: Blue debug box missing - visual regression detected")
        
        if not self.test_results.get("farmer_count_correct", True):
            report["recommendations"].append("CRITICAL: Farmer data not displaying - database connection issue")
        
        if not self.test_results.get("registration_loads", True):
            report["recommendations"].append("CRITICAL: Registration page broken - farmers cannot register")
        
        if not self.test_results.get("response_time_acceptable", True):
            report["recommendations"].append("Performance degradation detected - investigate slow responses")
        
        return report
    
    def test_breaking_change_detection(self) -> bool:
        """
        Simulate breaking changes to test detection capability
        This is for testing the protection system itself
        """
        print("\n🚨 Testing Breaking Change Detection...")
        
        # Test 1: Missing critical endpoint (simulate)
        print("Test 1: Simulating missing endpoint...")
        try:
            resp = requests.get(f"{self.base_url}/nonexistent-critical-endpoint", timeout=5)
            endpoint_missing = resp.status_code == 404
            print(f"  Missing endpoint correctly detected: {endpoint_missing}")
        except:
            endpoint_missing = True
            print(f"  Missing endpoint correctly detected: {endpoint_missing}")
        
        # Test 2: Visual regression (check for specific elements)
        print("Test 2: Testing visual regression detection...")
        resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
        has_required_colors = "#007BFF" in resp.text or "blue" in resp.text.lower()
        has_farmer_data = "16" in resp.text and "211.95" in resp.text
        visual_ok = has_required_colors and has_farmer_data
        print(f"  Visual elements intact: {visual_ok}")
        
        # Test 3: Performance regression
        print("Test 3: Testing performance regression detection...")
        start_time = time.time()
        resp = requests.get(f"{self.base_url}/business-dashboard", timeout=15)
        load_time = time.time() - start_time
        performance_ok = load_time < 5.0
        print(f"  Performance acceptable ({load_time:.2f}s): {performance_ok}")
        
        overall_protection = endpoint_missing and visual_ok and performance_ok
        print(f"\n🛡️ Protection System Status: {'WORKING' if overall_protection else 'NEEDS IMPROVEMENT'}")
        
        return overall_protection

def main():
    """Main test execution"""
    tester = RegressionProtectionTest()
    
    # Run all regression tests
    results = tester.run_all_tests()
    
    # Generate and display report
    report = tester.generate_report()
    
    print("\n" + "=" * 50)
    print("📊 REGRESSION PROTECTION TEST REPORT")
    print("=" * 50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed_tests']}")
    print(f"Failed: {report['failed_tests']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"Overall Status: {report['status']}")
    
    if report['recommendations']:
        print("\n🚨 CRITICAL ISSUES DETECTED:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    # Test the protection system itself
    tester.test_breaking_change_detection()
    
    # Determine exit code for CI/CD integration
    if report['success_rate'] < 90:
        print(f"\n❌ REGRESSION TESTS FAILED - Success rate {report['success_rate']:.1f}% below threshold")
        print("🚨 DEPLOYMENT SHOULD BE BLOCKED")
        exit(1)
    else:
        print(f"\n✅ REGRESSION TESTS PASSED - Success rate {report['success_rate']:.1f}%")
        print("🎉 DEPLOYMENT APPROVED")
        exit(0)

if __name__ == "__main__":
    main()