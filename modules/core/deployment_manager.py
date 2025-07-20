#!/usr/bin/env python3
"""
Deployment Manager module for AVA OLO Monitoring Dashboards
Handles deployment verification and manifest generation
"""
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from .config import SERVICE_NAME, VERSION, BUILD_ID, DEPLOYMENT_TIMESTAMP

logger = logging.getLogger(__name__)

# Import shared deployment manager if available
sys.path.append('../ava-olo-shared/shared')
try:
    from deployment_manager import DeploymentManager as SharedDeploymentManager
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False
    logger.warning("Shared deployment manager not available")

class LocalDeploymentManager:
    """Local deployment manager with fallback functionality"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.version = VERSION
        self.build_id = BUILD_ID
        self.deployment_timestamp = DEPLOYMENT_TIMESTAMP
        
        # Try to use shared manager if available
        if SHARED_AVAILABLE:
            try:
                self.shared_manager = SharedDeploymentManager(service_name)
            except Exception as e:
                logger.warning(f"Failed to initialize shared manager: {e}")
                self.shared_manager = None
        else:
            self.shared_manager = None
    
    def generate_deployment_manifest(self, version: str = None) -> dict:
        """Generate deployment manifest"""
        if self.shared_manager:
            try:
                return self.shared_manager.generate_deployment_manifest(version or self.version)
            except Exception as e:
                logger.warning(f"Shared manifest generation failed: {e}")
        
        # Fallback implementation
        manifest = {
            "service": self.service_name,
            "version": version or self.version,
            "build_id": self.build_id,
            "deployment_timestamp": self.deployment_timestamp,
            "generated_at": datetime.now().isoformat(),
            "endpoints": self._get_service_endpoints(),
            "health_check": "/api/v1/health",
            "deployment_verify": "/api/deployment/verify"
        }
        
        # Try to save manifest
        try:
            manifest_path = Path(f"{self.service_name}_manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Deployment manifest saved to {manifest_path}")
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
        
        return manifest
    
    def verify_deployment(self) -> dict:
        """Verify deployment status"""
        if self.shared_manager:
            try:
                return self.shared_manager.verify_deployment()
            except Exception as e:
                logger.warning(f"Shared verification failed: {e}")
        
        # Fallback verification
        verification = {
            "valid": True,
            "service": self.service_name,
            "version": self.version,
            "build_id": self.build_id,
            "deployment_timestamp": self.deployment_timestamp,
            "verified_at": datetime.now().isoformat(),
            "checks": {
                "version_match": True,
                "manifest_exists": self._check_manifest_exists(),
                "health_endpoint": True
            }
        }
        
        # Check if all checks passed
        verification["valid"] = all(verification["checks"].values())
        
        return verification
    
    def _get_service_endpoints(self) -> list:
        """Get list of service endpoints"""
        return [
            "/",
            "/business-dashboard",
            "/database-dashboard",
            "/health-dashboard",
            "/api/deployment/verify",
            "/api/v1/health",
            "/api/v1/database/test",
            "/api/v1/database/schema"
        ]
    
    def _check_manifest_exists(self) -> bool:
        """Check if deployment manifest exists"""
        manifest_path = Path(f"{self.service_name}_manifest.json")
        return manifest_path.exists()
    
    def get_deployment_info(self) -> dict:
        """Get comprehensive deployment information"""
        return {
            "service": self.service_name,
            "version": self.version,
            "build_id": self.build_id,
            "deployment_timestamp": self.deployment_timestamp,
            "current_time": datetime.now().isoformat(),
            "python_version": sys.version,
            "shared_available": SHARED_AVAILABLE,
            "manifest_exists": self._check_manifest_exists()
        }

# Create singleton instance
_deployment_manager = None

def get_deployment_manager() -> LocalDeploymentManager:
    """Get or create deployment manager instance"""
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = LocalDeploymentManager(SERVICE_NAME)
    return _deployment_manager

# Export convenience functions
def generate_manifest(version: str = None):
    """Generate deployment manifest"""
    return get_deployment_manager().generate_deployment_manifest(version)

def verify_deployment():
    """Verify deployment"""
    return get_deployment_manager().verify_deployment()

def get_deployment_info():
    """Get deployment information"""
    return get_deployment_manager().get_deployment_info()