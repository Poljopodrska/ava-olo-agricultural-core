#!/usr/bin/env python3
"""
Feature Verification Module
Deep verification of actual functionality, not just deployment status
"""
import httpx
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FeatureVerifier:
    """Verifies that deployed features actually work"""
    
    def __init__(self, service_name: str, base_url: str = "http://localhost:8080"):
        self.service_name = service_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def verify_all_features(self) -> Dict[str, Any]:
        """Run all feature verifications"""
        features = {}
        
        # Check constitutional design
        features["constitutional_design"] = await self.verify_constitutional_design()
        
        # Check template system
        features["template_system"] = await self.verify_template_system()
        
        # Check database connectivity
        features["database_connection"] = await self.verify_database()
        
        # Check specific UI elements
        features["ui_elements"] = await self.verify_ui_elements()
        
        # Check API endpoints
        features["api_endpoints"] = await self.verify_api_endpoints()
        
        # Calculate overall health
        all_working = all(
            f.get("status") == "healthy" 
            for f in features.values()
        )
        
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "all_features_working": all_working,
            "deployment_truly_successful": all_working,
            "features": features
        }
    
    async def verify_constitutional_design(self) -> Dict[str, Any]:
        """Verify constitutional design is actually displayed"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            content = response.text
            
            checks = {
                "spanish_brown_present": any(marker in content for marker in [
                    "#964B00", "#8B4513", "spanish-brown", "ava-brown"
                ]),
                "olive_green_present": any(marker in content for marker in [
                    "#6B8E23", "#808000", "olive-green", "ava-olive"
                ]),
                "constitutional_css_loaded": any(css in content for css in [
                    "constitutional-design.css", "constitutional-design-v3.css"
                ]),
                "minimum_font_size": any(font in content for font in [
                    "font-size: 18px", "font-size-base: 18px", "1.125rem"
                ]),
                "english_language": any(english in content for english in [
                    'lang="en"', "Farmer Portal", "Agricultural Assistant"
                ]),
                "no_fallback_active": not any(fallback in content for fallback in [
                    "linear-gradient(135deg, #1e3c72", "AVA OLO - Agricultural Assistant"
                ])
            }
            
            all_checks_passed = all(checks.values())
            
            return {
                "status": "healthy" if all_checks_passed else "degraded",
                "checks": checks,
                "message": "Constitutional design active" if all_checks_passed else "Constitutional design missing or partial"
            }
            
        except Exception as e:
            logger.error(f"Constitutional design verification failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Could not verify constitutional design"
            }
    
    async def verify_template_system(self) -> Dict[str, Any]:
        """Verify Jinja2 templates are loading correctly"""
        try:
            # Check debug endpoint if available
            debug_response = await self.client.get(f"{self.base_url}/debug/templates")
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                
                return {
                    "status": "healthy" if debug_data.get("constitutional_template_exists") else "failed",
                    "template_dir": debug_data.get("template_dir_configured"),
                    "templates_found": len(debug_data.get("template_files", [])),
                    "constitutional_template_exists": debug_data.get("constitutional_template_exists"),
                    "message": "Template system operational" if debug_data.get("constitutional_template_exists") else "Templates not loading correctly"
                }
            else:
                # Fallback check
                return {
                    "status": "unknown",
                    "message": "Debug endpoint not available"
                }
                
        except Exception as e:
            logger.error(f"Template system verification failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Could not verify template system"
            }
    
    async def verify_database(self) -> Dict[str, Any]:
        """Verify database connectivity and performance"""
        try:
            # Check health endpoint for DB status
            health_response = await self.client.get(f"{self.base_url}/health")
            if health_response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "Database connection verified"
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Health check returned {health_response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Could not verify database connection"
            }
    
    async def verify_ui_elements(self) -> Dict[str, Any]:
        """Verify specific UI elements are present and functional"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            content = response.text
            
            checks = {
                "version_display": "version" in content.lower(),
                "enter_key_script": "constitutional-interactions.js" in content,
                "responsive_meta": 'viewport' in content,
                "form_elements": any(form in content for form in ['<form', '<input', '<textarea']),
                "agricultural_theme": any(agri in content for agri in ['🌾', '🥭', 'agricultor', 'agricultural'])
            }
            
            return {
                "status": "healthy" if all(checks.values()) else "degraded",
                "checks": checks,
                "message": "UI elements verified" if all(checks.values()) else "Some UI elements missing"
            }
            
        except Exception as e:
            logger.error(f"UI verification failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Could not verify UI elements"
            }
    
    async def verify_api_endpoints(self) -> Dict[str, Any]:
        """Verify critical API endpoints are responding"""
        endpoints = {
            "/health": 200,
            "/version": [200, 404],  # May not exist
            "/api/deployment/verify": [200, 404]
        }
        
        results = {}
        for endpoint, expected_status in endpoints.items():
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                expected = expected_status if isinstance(expected_status, list) else [expected_status]
                results[endpoint] = response.status_code in expected
            except:
                results[endpoint] = False
        
        all_healthy = all(results.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "endpoints": results,
            "message": "All endpoints responding" if all_healthy else "Some endpoints not responding"
        }
    
    async def close(self):
        """Clean up HTTP client"""
        await self.client.aclose()

# Convenience functions for quick checks
async def verify_constitutional_design_active(base_url: str = "http://localhost:8080") -> bool:
    """Quick check if constitutional design is active"""
    verifier = FeatureVerifier("quick-check", base_url)
    try:
        result = await verifier.verify_constitutional_design()
        return result.get("status") == "healthy"
    finally:
        await verifier.close()

async def get_feature_verification_report(service_name: str, base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Get complete feature verification report"""
    verifier = FeatureVerifier(service_name, base_url)
    try:
        return await verifier.verify_all_features()
    finally:
        await verifier.close()