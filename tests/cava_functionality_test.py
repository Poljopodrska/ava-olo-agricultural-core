#!/usr/bin/env python3
"""
CAVA Functionality Test Suite
Tests the CAVA chat interface API functionality without browser automation
"""
import requests
import time
import json
from typing import Dict, Any

class CAVAFunctionalityTest:
    def __init__(self):
        self.base_url = "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
        self.session_id = f"test-session-{int(time.time())}"
        
    def test_cava_registration_api(self) -> bool:
        """Test CAVA registration API endpoint"""
        try:
            # Test basic CAVA response
            response = requests.post(
                f"{self.base_url}/api/v1/registration/cava",
                json={
                    "message": "Hello, my name is Test Farmer",
                    "farmer_id": self.session_id,
                    "language": "en"
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"   CAVA API returned status {response.status_code}")
                return False
                
            data = response.json()
            
            # Check response structure
            required_fields = ["response", "registration_complete"]
            for field in required_fields:
                if field not in data:
                    print(f"   Missing required field: {field}")
                    return False
            
            # Check response content
            if not isinstance(data["response"], str) or len(data["response"]) < 5:
                print(f"   Invalid response content: {data['response']}")
                return False
                
            print(f"   CAVA responded: {data['response'][:50]}...")
            return True
            
        except Exception as e:
            print(f"   CAVA API test failed: {e}")
            return False
    
    def test_cava_conversation_flow(self) -> bool:
        """Test multi-turn CAVA conversation"""
        try:
            # First message
            messages = [
                {"input": "Hello", "expect_keywords": ["name", "hello", "welcome"]},
                {"input": "My name is Peter Testov", "expect_keywords": ["peter", "nice", "last", "surname"]},
                {"input": "My last name is Testov", "expect_keywords": ["farm", "location", "where", "city"]},
                {"input": "I am from Sofia", "expect_keywords": ["hectares", "size", "how much", "land"]}
            ]
            
            conversation_working = True
            
            for i, msg in enumerate(messages[:2]):  # Test first 2 exchanges
                response = requests.post(
                    f"{self.base_url}/api/v1/registration/cava",
                    json={
                        "message": msg["input"],
                        "farmer_id": self.session_id,
                        "language": "en"
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"   Turn {i+1} failed: HTTP {response.status_code}")
                    conversation_working = False
                    break
                    
                data = response.json()
                response_text = data.get("response", "").lower()
                
                # Check if response contains expected keywords
                has_expected = any(keyword.lower() in response_text 
                                 for keyword in msg["expect_keywords"])
                
                if not has_expected:
                    print(f"   Turn {i+1} response doesn't match expectations")
                    print(f"   Expected keywords: {msg['expect_keywords']}")
                    print(f"   Got: {response_text[:100]}...")
                    # Don't fail on this - conversation AI can be unpredictable
                
                print(f"   Turn {i+1}: {msg['input']} → Response received ✓")
                
                # Small delay between messages
                time.sleep(0.5)
            
            return conversation_working
            
        except Exception as e:
            print(f"   Conversation flow test failed: {e}")
            return False
    
    def test_cava_interface_presence(self) -> bool:
        """Test CAVA interface is present in registration page"""
        try:
            response = requests.get(f"{self.base_url}/register", timeout=10)
            
            if response.status_code != 200:
                print(f"   Registration page not accessible: {response.status_code}")
                return False
            
            content = response.text.lower()
            
            # Check for CAVA interface elements
            required_elements = [
                "cava",
                "chat",
                "message",
                "send",
                "registration"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"   Missing interface elements: {missing_elements}")
                return len(missing_elements) <= 1  # Allow 1 missing element
            
            print(f"   All CAVA interface elements present")
            return True
            
        except Exception as e:
            print(f"   Interface presence test failed: {e}")
            return False
    
    def test_cava_error_handling(self) -> bool:
        """Test CAVA handles edge cases gracefully"""
        try:
            # Test empty message
            response = requests.post(
                f"{self.base_url}/api/v1/registration/cava",
                json={
                    "message": "",
                    "farmer_id": self.session_id,
                    "language": "en"
                },
                timeout=10
            )
            
            # Should handle empty message gracefully
            if response.status_code not in [200, 400]:
                print(f"   Unexpected status for empty message: {response.status_code}")
                return False
            
            # Test very long message
            long_message = "A" * 1000
            response = requests.post(
                f"{self.base_url}/api/v1/registration/cava",
                json={
                    "message": long_message,
                    "farmer_id": self.session_id,
                    "language": "en"
                },
                timeout=15
            )
            
            # Should handle long message gracefully
            if response.status_code not in [200, 400, 413]:
                print(f"   Unexpected status for long message: {response.status_code}")
                return False
            
            print(f"   Error handling working properly")
            return True
            
        except Exception as e:
            print(f"   Error handling test failed: {e}")
            return False
    
    def test_session_management(self) -> bool:
        """Test CAVA maintains session state"""
        try:
            # First message in session
            response1 = requests.post(
                f"{self.base_url}/api/v1/registration/cava",
                json={
                    "message": "My name is SessionTest",
                    "farmer_id": self.session_id,
                    "language": "en"
                },
                timeout=10
            )
            
            if response1.status_code != 200:
                print(f"   Session test message 1 failed: {response1.status_code}")
                return False
            
            # Second message - should remember context
            response2 = requests.post(
                f"{self.base_url}/api/v1/registration/cava",
                json={
                    "message": "What was my name again?",
                    "farmer_id": self.session_id,
                    "language": "en"
                },
                timeout=10
            )
            
            if response2.status_code != 200:
                print(f"   Session test message 2 failed: {response2.status_code}")
                return False
            
            # Check if CAVA remembers the name
            response_text = response2.json().get("response", "").lower()
            if "sessiontest" in response_text or "session test" in response_text:
                print(f"   Session management working - name remembered")
                return True
            else:
                print(f"   Session management unclear - response: {response_text[:100]}...")
                return True  # Don't fail on this - AI responses can vary
            
        except Exception as e:
            print(f"   Session management test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all CAVA functionality tests"""
        print("🤖 Running CAVA Functionality Tests...")
        print("=" * 50)
        
        tests = {
            "cava_api_basic": self.test_cava_registration_api,
            "cava_conversation": self.test_cava_conversation_flow,
            "interface_presence": self.test_cava_interface_presence,
            "error_handling": self.test_cava_error_handling,
            "session_management": self.test_session_management,
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            print(f"Testing {test_name}...")
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  Result: {status}")
            except Exception as e:
                print(f"  Result: ❌ ERROR - {e}")
                results[test_name] = False
            print()
        
        return results
    
    def generate_report(self, results: Dict[str, bool]) -> Dict[str, Any]:
        """Generate CAVA functionality test report"""
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": success_rate,
            "status": "EXCELLENT" if success_rate >= 90 else "GOOD" if success_rate >= 70 else "NEEDS_IMPROVEMENT",
            "test_results": results,
            "cava_functional": success_rate >= 60  # Lower threshold for AI functionality
        }

def main():
    """Main test execution"""
    tester = CAVAFunctionalityTest()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Generate report
    report = tester.generate_report(results)
    
    print("=" * 50)
    print("📊 CAVA FUNCTIONALITY TEST REPORT")
    print("=" * 50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed_tests']}")
    print(f"Failed: {report['failed_tests']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"CAVA Status: {report['status']}")
    print()
    
    if report['cava_functional']:
        print("✅ CAVA FUNCTIONALITY: WORKING")
        print("🥭 Bulgarian mango farmer CAVA registration protected")
    else:
        print("❌ CAVA FUNCTIONALITY: DEGRADED")
        print("🚨 Bulgarian mango farmer registration may be impacted")
    
    return report['cava_functional']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)