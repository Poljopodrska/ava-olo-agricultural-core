#!/usr/bin/env python3
"""
ECS-First Configuration for AVA OLO
Provides ECS endpoints as primary with App Runner fallback
"""

import os
import time
import requests
from typing import Dict, Optional

class AVAOLOEndpoints:
    """
    Manages AVA OLO service endpoints with ECS-first approach
    """
    
    # ECS Primary Endpoints (from SYSTEM_CHANGELOG.md)
    ECS_PRIMARY = {
        "monitoring": "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com",
        "agricultural": "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
    }
    
    # App Runner Fallback Endpoints (for safety during transition)
    APPRUNNER_FALLBACK = {
        "monitoring": "https://bcibj8ws3x.us-east-1.awsapprunner.com",
        "agricultural": "https://ujvej9snpp.us-east-1.awsapprunner.com"
    }
    
    def __init__(self, prefer_ecs: bool = True, timeout: int = 5):
        """
        Initialize endpoint manager
        
        Args:
            prefer_ecs: Whether to prefer ECS endpoints (default True)
            timeout: Timeout for health checks in seconds
        """
        self.prefer_ecs = prefer_ecs
        self.timeout = timeout
        self._health_cache = {}
    
    def get_endpoint(self, service: str) -> str:
        """
        Get the best available endpoint for a service
        
        Args:
            service: Service name ('monitoring' or 'agricultural')
            
        Returns:
            Best available endpoint URL
        """
        if service not in self.ECS_PRIMARY:
            raise ValueError(f"Unknown service: {service}. Available: {list(self.ECS_PRIMARY.keys())}")
        
        # If explicitly preferring ECS, try ECS first
        if self.prefer_ecs:
            ecs_url = self.ECS_PRIMARY[service]
            if self._is_healthy(ecs_url):
                return ecs_url
            
            # Fallback to App Runner if ECS is down
            apprunner_url = self.APPRUNNER_FALLBACK[service]
            if self._is_healthy(apprunner_url):
                print(f"⚠️  ECS down, using App Runner fallback for {service}")
                return apprunner_url
        else:
            # Use App Runner if explicitly requested
            apprunner_url = self.APPRUNNER_FALLBACK[service]
            if self._is_healthy(apprunner_url):
                return apprunner_url
            
            # Fallback to ECS
            ecs_url = self.ECS_PRIMARY[service]
            if self._is_healthy(ecs_url):
                print(f"⚠️  App Runner down, using ECS fallback for {service}")
                return ecs_url
        
        # If both are down, return ECS (primary) anyway
        print(f"⚠️  Both endpoints down for {service}, returning ECS primary")
        return self.ECS_PRIMARY[service]
    
    def _is_healthy(self, url: str) -> bool:
        """
        Check if an endpoint is healthy (with caching)
        
        Args:
            url: URL to check
            
        Returns:
            True if endpoint is healthy
        """
        # Check cache first (simple 30-second cache)
        cache_key = url
        if cache_key in self._health_cache:
            cached_time, cached_result = self._health_cache[cache_key]
            if (time.time() - cached_time) < 30:  # 30 second cache
                return cached_result
        
        try:
            # Try health check endpoint first
            health_url = f"{url}/health"
            response = requests.get(health_url, timeout=self.timeout)
            is_healthy = response.status_code == 200
        except:
            try:
                # Fallback to root endpoint
                response = requests.get(url, timeout=self.timeout)
                is_healthy = response.status_code in [200, 405]  # 405 is OK for some endpoints
            except:
                is_healthy = False
        
        # Cache result
        self._health_cache[cache_key] = (time.time(), is_healthy)
        return is_healthy
    
    def get_monitoring_url(self) -> str:
        """Get monitoring service URL"""
        return self.get_endpoint("monitoring")
    
    def get_agricultural_url(self) -> str:
        """Get agricultural service URL"""
        return self.get_endpoint("agricultural")
    
    def get_dev_db_url(self) -> str:
        """Get development database API URL (monitoring service)"""
        return self.get_monitoring_url()
    
    def status_report(self) -> Dict[str, Dict[str, str]]:
        """
        Get status report of all endpoints
        
        Returns:
            Status dictionary with health information
        """
        report = {}
        
        for service in ["monitoring", "agricultural"]:
            ecs_url = self.ECS_PRIMARY[service]
            apprunner_url = self.APPRUNNER_FALLBACK[service]
            
            report[service] = {
                "ecs_primary": ecs_url,
                "ecs_healthy": "✅" if self._is_healthy(ecs_url) else "❌",
                "apprunner_fallback": apprunner_url,
                "apprunner_healthy": "✅" if self._is_healthy(apprunner_url) else "❌",
                "active_endpoint": self.get_endpoint(service)
            }
        
        return report

# Global instance for easy import
endpoints = AVAOLOEndpoints()

def get_monitoring_url() -> str:
    """Convenience function to get monitoring URL"""
    return endpoints.get_monitoring_url()

def get_agricultural_url() -> str:
    """Convenience function to get agricultural URL"""
    return endpoints.get_agricultural_url()

def get_dev_db_url() -> str:
    """Convenience function to get development database URL"""
    return endpoints.get_dev_db_url()

if __name__ == "__main__":
    import time
    
    print("=== AVA OLO ECS-First Endpoint Configuration ===\n")
    
    # Show status report
    status = endpoints.status_report()
    
    for service, info in status.items():
        print(f"🔧 {service.title()} Service:")
        print(f"   ECS Primary: {info['ecs_primary']} {info['ecs_healthy']}")
        print(f"   App Runner:  {info['apprunner_fallback']} {info['apprunner_healthy']}")
        print(f"   Active:      {info['active_endpoint']}")
        print()
    
    print("📋 Quick Access Functions:")
    print(f"   Monitoring:  {get_monitoring_url()}")
    print(f"   Agricultural: {get_agricultural_url()}")
    print(f"   Dev DB API:   {get_dev_db_url()}")
    
    print("\n✅ ECS-first configuration ready!")