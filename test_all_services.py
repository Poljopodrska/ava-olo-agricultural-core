#!/usr/bin/env python3
"""
Test all AVA OLO services to ensure they're running and accessible
"""
import httpx
import asyncio
import sys
from datetime import datetime

# Service definitions with their main pages
SERVICES = [
    {
        "name": "API Gateway",
        "port": 8000,
        "endpoints": [
            {"path": "/api/v1/health", "expected_status": 200},
            {"path": "/api/v1/farmers", "expected_status": 200}
        ]
    },
    {
        "name": "Mock WhatsApp",
        "port": 8006,
        "endpoints": [
            {"path": "/health", "expected_status": 200},
            {"path": "/", "expected_status": 200}
        ]
    },
    {
        "name": "Agronomic Dashboard",
        "port": 8007,
        "endpoints": [
            {"path": "/health", "expected_status": 200},
            {"path": "/", "expected_status": 200}
        ]
    },
    {
        "name": "Business Dashboard",
        "port": 8004,
        "endpoints": [
            {"path": "/health", "expected_status": 200},
            {"path": "/", "expected_status": 200}
        ]
    },
    {
        "name": "Database Explorer",
        "port": 8005,
        "endpoints": [
            {"path": "/health", "expected_status": 200},
            {"path": "/", "expected_status": 200}
        ]
    },
    {
        "name": "Health Check Dashboard",
        "port": 8008,
        "endpoints": [
            {"path": "/health", "expected_status": 200},
            {"path": "/", "expected_status": 200},
            {"path": "/api/health", "expected_status": 200}
        ]
    }
]

async def test_endpoint(client: httpx.AsyncClient, service_name: str, port: int, endpoint: dict) -> dict:
    """Test a single endpoint"""
    url = f"http://localhost:{port}{endpoint['path']}"
    try:
        response = await client.get(url)
        success = response.status_code == endpoint['expected_status']
        return {
            "service": service_name,
            "url": url,
            "status_code": response.status_code,
            "expected": endpoint['expected_status'],
            "success": success,
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "service": service_name,
            "url": url,
            "status_code": None,
            "expected": endpoint['expected_status'],
            "success": False,
            "error": str(e)
        }

async def test_all_services():
    """Test all services and their endpoints"""
    print("🔍 AVA OLO Service Health Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test all endpoints
        tasks = []
        for service in SERVICES:
            for endpoint in service['endpoints']:
                tasks.append(test_endpoint(client, service['name'], service['port'], endpoint))
        
        results = await asyncio.gather(*tasks)
        all_results.extend(results)
    
    # Group results by service
    services_status = {}
    for result in all_results:
        service_name = result['service']
        if service_name not in services_status:
            services_status[service_name] = []
        services_status[service_name].append(result)
    
    # Print results
    all_healthy = True
    for service_name, results in services_status.items():
        service_healthy = all(r['success'] for r in results)
        all_healthy = all_healthy and service_healthy
        
        status_icon = "✅" if service_healthy else "❌"
        print(f"\n{status_icon} {service_name}")
        
        for result in results:
            if result['success']:
                print(f"   ✓ {result['url']} - {result['status_code']} ({result['response_time']:.3f}s)")
            else:
                error_msg = result.get('error', f"Expected {result['expected']}, got {result['status_code']}")
                print(f"   ✗ {result['url']} - {error_msg}")
    
    # Summary
    print("\n" + "=" * 70)
    total_endpoints = len(all_results)
    successful_endpoints = sum(1 for r in all_results if r['success'])
    
    if all_healthy:
        print(f"✅ All services are healthy! ({successful_endpoints}/{total_endpoints} endpoints passed)")
        print("\n📌 Service URLs:")
        print("   • API Gateway: http://localhost:8000/api/v1/farmers")
        print("   • Mock WhatsApp: http://localhost:8006/")
        print("   • Agronomic Dashboard: http://localhost:8007/")
        print("   • Business Dashboard: http://localhost:8004/")
        print("   • Database Explorer: http://localhost:8005/")
        print("   • Health Check Dashboard: http://localhost:8008/")
    else:
        print(f"⚠️  Some services have issues! ({successful_endpoints}/{total_endpoints} endpoints passed)")
        print("\nPlease check the failed endpoints above.")
    
    return all_healthy

if __name__ == "__main__":
    success = asyncio.run(test_all_services())
    sys.exit(0 if success else 1)