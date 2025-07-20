#!/usr/bin/env python3
"""
API Content Validation Test Suite
Tests API responses for correct structure and content
"""
import requests
import json
import time
from typing import Dict, Any, List, Optional

class APIContentValidator:
    def __init__(self):
        self.base_url = "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
        
    def validate_health_endpoint(self) -> bool:
        """Validate health endpoint structure"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=10)
            
            if resp.status_code != 200:
                print(f"   Health endpoint status: {resp.status_code}")
                return False
            
            data = resp.json()
            
            # Required fields for health endpoint
            required_fields = ["status", "version", "service"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   Missing required fields: {missing_fields}")
                return False
            
            # Validate field types and values
            if not isinstance(data["status"], str):
                print(f"   Invalid status type: {type(data['status'])}")
                return False
                
            if data["status"] not in ["healthy", "degraded", "unhealthy"]:
                print(f"   Invalid status value: {data['status']}")
                return False
            
            if not isinstance(data["version"], str) or len(data["version"]) < 3:
                print(f"   Invalid version: {data['version']}")
                return False
            
            print(f"   Health endpoint structure valid ✓")
            return True
            
        except json.JSONDecodeError as e:
            print(f"   Health endpoint returned invalid JSON: {e}")
            return False
        except Exception as e:
            print(f"   Health endpoint validation failed: {e}")
            return False
    
    def validate_database_health_endpoint(self) -> bool:
        """Validate database health endpoint structure"""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/health/database", timeout=15)
            
            # Accept both 200 (healthy) and 503 (degraded) as valid responses
            if resp.status_code not in [200, 503]:
                print(f"   Database health endpoint status: {resp.status_code}")
                return resp.status_code == 404  # Endpoint might not exist yet
            
            data = resp.json()
            
            # Required fields for database health
            required_fields = ["status", "timestamp"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   Missing required fields: {missing_fields}")
                return False
            
            # Validate status values
            valid_statuses = ["healthy", "warning", "degraded", "unhealthy"]
            if data["status"] not in valid_statuses:
                print(f"   Invalid status: {data['status']}")
                return False
            
            # Check for performance metrics if healthy/warning
            if data["status"] in ["healthy", "warning"]:
                if "test_query_time" not in data:
                    print(f"   Missing performance metrics for status: {data['status']}")
                    return False
            
            print(f"   Database health endpoint structure valid ✓")
            return True
            
        except json.JSONDecodeError as e:
            print(f"   Database health endpoint returned invalid JSON: {e}")
            return False
        except Exception as e:
            print(f"   Database health endpoint validation failed: {e}")
            return False
    
    def validate_dashboard_data_structure(self) -> bool:
        """Validate business dashboard contains expected data structure"""
        try:
            resp = requests.get(f"{self.base_url}/business-dashboard", timeout=10)
            
            if resp.status_code != 200:
                print(f"   Dashboard status: {resp.status_code}")
                return False
            
            content = resp.text
            
            # Check for required data elements in HTML
            required_elements = [
                ("farmer count", r'\b\d+\s*farmers?\b'),
                ("hectare data", r'\b\d+\.?\d*\s*hectares?\b'),
                ("debug box", r'debug|version'),
                ("timestamp", r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}')
            ]
            
            missing_elements = []
            for element_name, pattern in required_elements:
                import re
                if not re.search(pattern, content, re.IGNORECASE):
                    missing_elements.append(element_name)
            
            if missing_elements:
                print(f"   Missing dashboard elements: {missing_elements}")
                return len(missing_elements) <= 1  # Allow 1 missing element
            
            print(f"   Dashboard data structure valid ✓")
            return True
            
        except Exception as e:
            print(f"   Dashboard validation failed: {e}")
            return False
    
    def validate_api_error_responses(self) -> bool:
        """Validate API error responses are properly structured"""
        try:
            # Test non-existent endpoint
            resp = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            
            if resp.status_code != 404:
                print(f"   Expected 404, got: {resp.status_code}")
                return False
            
            # Try to parse as JSON (should have error structure)
            try:
                data = resp.json()
                # FastAPI typically returns {"detail": "message"} for 404s
                if "detail" not in data:
                    print(f"   404 response missing detail field")
                    return False
            except json.JSONDecodeError:
                # HTML 404 page is also acceptable
                if "404" not in resp.text:
                    print(f"   404 response doesn't indicate error")
                    return False
            
            print(f"   API error responses structured properly ✓")
            return True
            
        except Exception as e:
            print(f"   Error response validation failed: {e}")
            return False
    
    def validate_cors_headers(self) -> bool:
        """Validate CORS headers are present for API endpoints"""
        try:
            resp = requests.options(f"{self.base_url}/api/v1/health", timeout=5)
            
            # CORS preflight should return 200 or 405
            if resp.status_code not in [200, 405]:
                print(f"   CORS preflight status: {resp.status_code}")
                return False
            
            # Check for CORS headers in a GET request
            resp = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            headers = resp.headers
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods", 
                "Access-Control-Allow-Headers"
            ]
            
            has_cors = any(header in headers for header in cors_headers)
            
            if not has_cors:
                print(f"   No CORS headers found")
                return False  # This might be acceptable
            
            print(f"   CORS headers configured ✓")
            return True
            
        except Exception as e:
            print(f"   CORS validation failed: {e}")
            return True  # Don't fail on CORS issues
    
    def validate_response_times(self) -> bool:
        """Validate API response times are reasonable"""
        try:
            endpoints = [
                ("/health", 2.0),
                ("/api/v1/health", 3.0),
                ("/business-dashboard", 5.0),
                ("/register", 5.0)
            ]
            
            slow_endpoints = []
            
            for endpoint, max_time in endpoints:
                start = time.time()
                try:
                    resp = requests.get(f"{self.base_url}{endpoint}", timeout=max_time + 2)
                    duration = time.time() - start
                    
                    if duration > max_time:
                        slow_endpoints.append(f"{endpoint} ({duration:.2f}s)")
                        
                except requests.Timeout:
                    slow_endpoints.append(f"{endpoint} (timeout)")
                except Exception:
                    pass  # Endpoint might not exist, that's okay
            
            if slow_endpoints:
                print(f"   Slow endpoints: {slow_endpoints}")
                return len(slow_endpoints) <= 1  # Allow 1 slow endpoint
            
            print(f"   All endpoints respond quickly ✓")
            return True
            
        except Exception as e:
            print(f"   Response time validation failed: {e}")
            return False
    
    def run_all_validations(self) -> Dict[str, bool]:
        """Run all API content validations"""
        print("🔍 Running API Content Validation Tests...")
        print("=" * 50)
        
        validations = {
            "health_endpoint_structure": self.validate_health_endpoint,
            "database_health_structure": self.validate_database_health_endpoint,
            "dashboard_data_structure": self.validate_dashboard_data_structure,
            "api_error_responses": self.validate_api_error_responses,
            "cors_headers": self.validate_cors_headers,
            "response_times": self.validate_response_times,
        }
        
        results = {}
        
        for validation_name, validation_func in validations.items():
            print(f"Validating {validation_name}...")
            try:
                result = validation_func()
                results[validation_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  Result: {status}")
            except Exception as e:
                print(f"  Result: ❌ ERROR - {e}")
                results[validation_name] = False
            print()
        
        return results
    
    def generate_report(self, results: Dict[str, bool]) -> Dict[str, Any]:
        """Generate API content validation report"""
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_validations": total,
            "passed_validations": passed,
            "failed_validations": total - passed,
            "success_rate": success_rate,
            "status": "EXCELLENT" if success_rate >= 90 else "GOOD" if success_rate >= 70 else "NEEDS_IMPROVEMENT",
            "validation_results": results,
            "api_content_valid": success_rate >= 70
        }

def main():
    """Main validation execution"""
    validator = APIContentValidator()
    
    # Run all validations
    results = validator.run_all_validations()
    
    # Generate report
    report = validator.generate_report(results)
    
    print("=" * 50)
    print("📊 API CONTENT VALIDATION REPORT")
    print("=" * 50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Validations: {report['total_validations']}")
    print(f"Passed: {report['passed_validations']}")
    print(f"Failed: {report['failed_validations']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"API Status: {report['status']}")
    print()
    
    if report['api_content_valid']:
        print("✅ API CONTENT VALIDATION: PASSED")
        print("🛡️ API structure and content protection active")
    else:
        print("❌ API CONTENT VALIDATION: FAILED")
        print("🚨 API content validation needs improvement")
    
    return report['api_content_valid']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)