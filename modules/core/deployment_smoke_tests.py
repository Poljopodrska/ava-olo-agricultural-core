#!/usr/bin/env python3
"""
Deployment Smoke Tests
Post-deployment verification to catch silent failures
"""
import asyncio
import httpx
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DeploymentSmokeTests:
    """Run smoke tests after deployment to verify features work"""
    
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=15.0)
        self.results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests for the service"""
        start_time = datetime.utcnow()
        
        # Agricultural Core specific tests
        if self.service_name == "agricultural-core":
            await self.test_constitutional_design_loads()
            await self.test_english_language_present()
            await self.test_no_fallback_ui()
            await self.test_farmer_ui_responsive()
            await self.test_api_endpoints_respond()
        
        # Monitoring Dashboards specific tests
        elif self.service_name == "monitoring-dashboards":
            await self.test_dashboard_hub_accessible()
            await self.test_all_dashboards_load()
            await self.test_feature_verification_endpoint()
            await self.test_deployment_status_includes_features()
        
        # Common tests for all services
        await self.test_health_endpoint()
        await self.test_version_endpoint()
        await self.test_no_500_errors()
        
        # Calculate results
        passed_tests = [r for r in self.results if r['passed']]
        failed_tests = [r for r in self.results if not r['passed']]
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "all_tests_passed": len(failed_tests) == 0,
            "total_tests": len(self.results),
            "passed_tests": len(passed_tests),
            "failed_tests": len(failed_tests),
            "duration_seconds": duration,
            "results": self.results,
            "failed_test_names": [t['test_name'] for t in failed_tests]
        }
    
    async def test_constitutional_design_loads(self):
        """Test that constitutional design actually renders"""
        test_name = "constitutional_design_loads"
        try:
            response = await self.client.get(f"{self.base_url}/")
            content = response.text
            
            # Check for constitutional markers
            has_brown = "#8B4513" in content or "spanish-brown" in content
            has_olive = "#808000" in content or "olive-green" in content
            has_english = "Farmer Portal" in content
            has_18px = "font-size: 18px" in content or "font-size-base: 18px" in content
            
            passed = all([has_brown, has_olive, has_english, has_18px])
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "message": "Constitutional design loaded" if passed else "Constitutional design missing",
                "details": {
                    "has_brown": has_brown,
                    "has_olive": has_olive,
                    "has_english": has_english,
                    "has_18px_fonts": has_18px
                }
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_english_language_present(self):
        """Test English language elements are present"""
        test_name = "english_language_present"
        try:
            response = await self.client.get(f"{self.base_url}/")
            content = response.text
            
            english_elements = [
                "Farmer Portal",
                "Bulgarian Mango Cooperative",
                "agricultural question"
            ]
            
            found_elements = [elem for elem in english_elements if elem in content]
            passed = len(found_elements) >= 2
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "message": f"Found {len(found_elements)}/3 English elements",
                "found_elements": found_elements
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_no_fallback_ui(self):
        """Test that fallback UI is not showing"""
        test_name = "no_fallback_ui"
        try:
            response = await self.client.get(f"{self.base_url}/")
            content = response.text
            
            # Check for absence of fallback indicators
            fallback_markers = [
                "linear-gradient(135deg, #1e3c72",
                "AVA OLO - Agricultural Assistant",
                "Basic HTML fallback"
            ]
            
            has_fallback = any(marker in content for marker in fallback_markers)
            
            self.results.append({
                "test_name": test_name,
                "passed": not has_fallback,
                "message": "No fallback UI detected" if not has_fallback else "Fallback UI is showing!"
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_farmer_ui_responsive(self):
        """Test farmer UI is loading and responsive"""
        test_name = "farmer_ui_responsive"
        try:
            response = await self.client.get(f"{self.base_url}/")
            
            self.results.append({
                "test_name": test_name,
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_dashboard_hub_accessible(self):
        """Test dashboard hub shows all dashboards"""
        test_name = "dashboard_hub_accessible"
        try:
            response = await self.client.get(f"{self.base_url}/dashboards/")
            content = response.text
            
            # Check for all dashboards
            dashboards = [
                "Agronomic Dashboard",
                "Business Dashboard",
                "Health Dashboard",
                "Database Dashboard",
                "Deployment Dashboard",
                "Feature Status"
            ]
            
            found_dashboards = [d for d in dashboards if d in content]
            passed = len(found_dashboards) >= 5
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "message": f"Found {len(found_dashboards)}/{len(dashboards)} dashboards",
                "found_dashboards": found_dashboards
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_all_dashboards_load(self):
        """Test that each dashboard loads without error"""
        test_name = "all_dashboards_load"
        dashboard_paths = [
            "/dashboards/agronomic/",
            "/dashboards/business/",
            "/dashboards/health/",
            "/dashboards/database/",
            "/dashboards/deployment/",
            "/dashboards/features/"
        ]
        
        results = {}
        for path in dashboard_paths:
            try:
                response = await self.client.get(f"{self.base_url}{path}")
                results[path] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
            except Exception as e:
                results[path] = {
                    "error": str(e),
                    "success": False
                }
        
        all_success = all(r["success"] for r in results.values())
        
        self.results.append({
            "test_name": test_name,
            "passed": all_success,
            "dashboard_results": results
        })
    
    async def test_feature_verification_endpoint(self):
        """Test feature verification API works"""
        test_name = "feature_verification_endpoint"
        try:
            response = await self.client.get(f"{self.base_url}/dashboards/features/api/verify-all")
            
            if response.status_code == 200:
                data = response.json()
                passed = "all_services_healthy" in data
            else:
                passed = False
                data = None
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "status_code": response.status_code,
                "has_feature_data": data is not None
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_deployment_status_includes_features(self):
        """Test deployment status includes feature verification"""
        test_name = "deployment_status_includes_features"
        try:
            response = await self.client.get(f"{self.base_url}/api/deployment/status")
            
            if response.status_code == 200:
                data = response.json()
                has_features = "features" in data
                has_feature_verification = any(
                    "feature_verification" in service 
                    for service in data.get("services", {}).values()
                )
                passed = has_features and has_feature_verification
            else:
                passed = False
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "message": "Deployment status includes features" if passed else "Feature data missing from deployment status"
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        test_name = "health_endpoint"
        try:
            response = await self.client.get(f"{self.base_url}/health")
            self.results.append({
                "test_name": test_name,
                "passed": response.status_code == 200,
                "status_code": response.status_code
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_version_endpoint(self):
        """Test version endpoint returns version info"""
        test_name = "version_endpoint"
        try:
            response = await self.client.get(f"{self.base_url}/version")
            
            if response.status_code == 200:
                data = response.json()
                has_version = "version" in data
                passed = has_version
            else:
                passed = response.status_code == 404  # Some services may not have version endpoint
            
            self.results.append({
                "test_name": test_name,
                "passed": passed,
                "status_code": response.status_code
            })
        except Exception as e:
            self.results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    async def test_api_endpoints_respond(self):
        """Test critical API endpoints respond"""
        test_name = "api_endpoints_respond"
        endpoints = [
            "/api/v1/health",
            "/api/v1/farmers",
            "/api/v1/fields"
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                results[endpoint] = response.status_code in [200, 401, 404]  # Auth or not found is OK
            except:
                results[endpoint] = False
        
        passed = sum(results.values()) >= 2  # At least 2/3 should respond
        
        self.results.append({
            "test_name": test_name,
            "passed": passed,
            "endpoint_results": results
        })
    
    async def test_no_500_errors(self):
        """Test that no endpoints return 500 errors"""
        test_name = "no_500_errors"
        test_endpoints = [
            "/",
            "/health",
            "/version",
            "/api/deployment/status" if self.service_name == "monitoring-dashboards" else "/api/v1/health"
        ]
        
        errors_found = []
        for endpoint in test_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code >= 500:
                    errors_found.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code
                    })
            except:
                pass  # Connection errors are different from 500s
        
        self.results.append({
            "test_name": test_name,
            "passed": len(errors_found) == 0,
            "errors_found": errors_found
        })
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()


# Convenience function to run smoke tests
async def run_deployment_smoke_tests(service_name: str, base_url: str) -> Dict[str, Any]:
    """Run smoke tests for a deployed service"""
    tester = DeploymentSmokeTests(service_name, base_url)
    try:
        results = await tester.run_all_tests()
        
        # Log results
        if results["all_tests_passed"]:
            logger.info(f"✅ All smoke tests passed for {service_name}")
        else:
            logger.error(f"❌ Smoke test failures for {service_name}: {results['failed_test_names']}")
        
        return results
    finally:
        await tester.close()


# Add to deployment verification webhook
async def verify_deployment_with_smoke_tests(
    service_name: str, 
    version: str, 
    base_url: str
) -> Dict[str, Any]:
    """Comprehensive deployment verification including smoke tests"""
    
    # Wait for service to stabilize
    await asyncio.sleep(15)
    
    # Run feature verification
    from .feature_verification import get_feature_verification_report
    feature_report = await get_feature_verification_report(service_name, base_url)
    
    # Run smoke tests
    smoke_test_results = await run_deployment_smoke_tests(service_name, base_url)
    
    # Combine results
    deployment_verified = (
        feature_report.get("all_features_working", False) and
        smoke_test_results.get("all_tests_passed", False)
    )
    
    return {
        "service": service_name,
        "version": version,
        "deployment_verified": deployment_verified,
        "feature_verification": feature_report,
        "smoke_test_results": smoke_test_results,
        "timestamp": datetime.utcnow().isoformat()
    }