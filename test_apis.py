#!/usr/bin/env python3
"""
AVA OLO Dashboard System - API Test Suite
Comprehensive testing for monitoring and explorer APIs
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APITester:
    """Comprehensive API testing suite"""
    
    def __init__(self):
        self.monitoring_base = 'http://localhost:8000/api'
        self.explorer_base = 'http://localhost:8001/api'
        self.dashboard_base = 'http://localhost:8080'
        
        self.test_results = {
            'monitoring_api': {},
            'explorer_api': {},
            'dashboard_static': {},
            'database_connection': {},
            'websocket': {},
            'export': {}
        }
        
        self.total_tests = 0
        self.passed_tests = 0

    async def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 AVA OLO Dashboard System - API Test Suite")
        print("=" * 60)
        
        try:
            # Import requests here to check if it's available
            import requests
            self.requests = requests
        except ImportError:
            print("❌ requests library not found. Installing...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
            self.requests = requests

        # Run test categories
        await self.test_database_connection()
        await self.test_monitoring_api()
        await self.test_explorer_api()
        await self.test_dashboard_static_files()
        await self.test_websocket_connection()
        await self.test_export_functionality()
        
        # Display results
        self.display_test_summary()

    async def test_database_connection(self):
        """Test database connectivity"""
        print("\n🗄️  Testing Database Connection...")
        
        try:
            from config import DATABASE_URL, validate_config
            
            # Test config validation
            self.run_test(
                "Config Validation",
                lambda: validate_config(),
                "database_connection"
            )
            
            # Test database URL format
            self.run_test(
                "Database URL Format",
                lambda: DATABASE_URL.startswith("postgresql://"),
                "database_connection"
            )
            
            # Test database connection (if possible)
            try:
                from core.database_operations import DatabaseOperations
                db_ops = DatabaseOperations()
                
                self.run_test(
                    "Database Connection",
                    lambda: asyncio.run(db_ops.health_check()),
                    "database_connection"
                )
            except Exception as e:
                self.test_results["database_connection"]["Database Connection"] = f"Skip: {e}"
                print(f"   ⚠️  Database Connection: Skipped ({e})")
            
        except Exception as e:
            self.test_results["database_connection"]["Database Setup"] = f"Failed: {e}"
            print(f"   ❌ Database Setup: {e}")

    async def test_monitoring_api(self):
        """Test monitoring API endpoints"""
        print("\n📊 Testing Monitoring API...")
        
        endpoints = [
            ('/stats/overview', 'Overview Statistics'),
            ('/stats/growth-trends', 'Growth Trends'),
            ('/stats/activity-today', 'Today Activity'),
            ('/stats/growth-chart?period=7', 'Growth Chart'),
            ('/stats/churn-chart?period=7', 'Churn Chart'),
            ('/activity/live-feed', 'Live Activity Feed'),
            ('/activity/recent-entries', 'Recent Entries'),
            ('/health', 'Health Check')
        ]
        
        for endpoint, name in endpoints:
            self.test_api_endpoint(
                f"{self.monitoring_base}{endpoint}",
                name,
                "monitoring_api"
            )

    async def test_explorer_api(self):
        """Test database explorer API endpoints"""
        print("\n🔍 Testing Explorer API...")
        
        endpoints = [
            ('/schema/tables', 'Schema Tables'),
            ('/schema/relationships', 'Table Relationships'),
            ('/health', 'Health Check')
        ]
        
        for endpoint, name in endpoints:
            self.test_api_endpoint(
                f"{self.explorer_base}{endpoint}",
                name,
                "explorer_api"
            )
        
        # Test table data endpoint (dynamic based on available tables)
        try:
            tables_response = self.requests.get(f"{self.explorer_base}/schema/tables", timeout=5)
            if tables_response.status_code == 200:
                tables_data = tables_response.json()
                if tables_data and len(tables_data) > 0:
                    first_table = tables_data[0]['name']
                    self.test_api_endpoint(
                        f"{self.explorer_base}/data/{first_table}?limit=5",
                        f"Table Data ({first_table})",
                        "explorer_api"
                    )
        except Exception as e:
            self.test_results["explorer_api"]["Dynamic Table Test"] = f"Failed: {e}"

    async def test_dashboard_static_files(self):
        """Test dashboard HTML files accessibility"""
        print("\n🌐 Testing Dashboard Static Files...")
        
        files = [
            ('/monitoring_dashboard.html', 'Monitoring Dashboard'),
            ('/database_explorer.html', 'Database Explorer')
        ]
        
        for file_path, name in files:
            self.test_static_file(
                f"{self.dashboard_base}{file_path}",
                name,
                "dashboard_static"
            )

    async def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        print("\n🔌 Testing WebSocket Connection...")
        
        try:
            import websockets
            
            async def test_ws():
                try:
                    uri = "ws://localhost:8000/ws"
                    async with websockets.connect(uri, timeout=5) as websocket:
                        # Wait briefly for connection
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    return False
            
            result = await test_ws()
            self.run_test(
                "WebSocket Connection",
                lambda: result,
                "websocket"
            )
            
        except ImportError:
            self.test_results["websocket"]["WebSocket Connection"] = "Skip: websockets not installed"
            print("   ⚠️  WebSocket Connection: Skipped (websockets not installed)")
        except Exception as e:
            self.test_results["websocket"]["WebSocket Connection"] = f"Failed: {e}"
            print(f"   ❌ WebSocket Connection: {e}")

    async def test_export_functionality(self):
        """Test Excel/CSV export functionality"""
        print("\n📤 Testing Export Functionality...")
        
        try:
            # Test if we can get table list first
            tables_response = self.requests.get(f"{self.explorer_base}/schema/tables", timeout=5)
            if tables_response.status_code == 200:
                tables_data = tables_response.json()
                if tables_data and len(tables_data) > 0:
                    first_table = tables_data[0]['name']
                    
                    # Test Excel export endpoint (don't download, just check if endpoint responds)
                    excel_url = f"{self.explorer_base}/data/{first_table}/export?format=excel&limit=10"
                    self.test_api_endpoint(
                        excel_url,
                        f"Excel Export ({first_table})",
                        "export",
                        expected_content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Test CSV export endpoint
                    csv_url = f"{self.explorer_base}/data/{first_table}/export?format=csv&limit=10"
                    self.test_api_endpoint(
                        csv_url,
                        f"CSV Export ({first_table})",
                        "export",
                        expected_content_type="text/csv"
                    )
            else:
                self.test_results["export"]["Export Tests"] = "Skip: No tables available"
                print("   ⚠️  Export Tests: Skipped (No tables available)")
                
        except Exception as e:
            self.test_results["export"]["Export Tests"] = f"Failed: {e}"
            print(f"   ❌ Export Tests: {e}")

    def test_api_endpoint(self, url: str, name: str, category: str, expected_content_type: str = None):
        """Test a single API endpoint"""
        try:
            response = self.requests.get(url, timeout=10)
            
            # Check status code
            if response.status_code == 200:
                # Check content type if specified
                if expected_content_type:
                    content_type = response.headers.get('content-type', '')
                    if expected_content_type in content_type:
                        self.test_results[category][name] = "Pass"
                        print(f"   ✅ {name}")
                        self.passed_tests += 1
                    else:
                        self.test_results[category][name] = f"Fail: Wrong content type ({content_type})"
                        print(f"   ❌ {name}: Wrong content type")
                else:
                    # Try to parse JSON for API endpoints
                    try:
                        data = response.json()
                        self.test_results[category][name] = "Pass"
                        print(f"   ✅ {name}")
                        self.passed_tests += 1
                    except json.JSONDecodeError:
                        self.test_results[category][name] = "Pass (Non-JSON response)"
                        print(f"   ✅ {name} (Non-JSON)")
                        self.passed_tests += 1
            else:
                self.test_results[category][name] = f"Fail: HTTP {response.status_code}"
                print(f"   ❌ {name}: HTTP {response.status_code}")
            
            self.total_tests += 1
            
        except Exception as e:
            self.test_results[category][name] = f"Error: {str(e)}"
            print(f"   ❌ {name}: {str(e)}")
            self.total_tests += 1

    def test_static_file(self, url: str, name: str, category: str):
        """Test static file accessibility"""
        try:
            response = self.requests.get(url, timeout=10)
            
            if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                # Check if it's actually HTML content
                if '<html' in response.text.lower():
                    self.test_results[category][name] = "Pass"
                    print(f"   ✅ {name}")
                    self.passed_tests += 1
                else:
                    self.test_results[category][name] = "Fail: Not valid HTML"
                    print(f"   ❌ {name}: Not valid HTML")
            else:
                self.test_results[category][name] = f"Fail: HTTP {response.status_code}"
                print(f"   ❌ {name}: HTTP {response.status_code}")
            
            self.total_tests += 1
            
        except Exception as e:
            self.test_results[category][name] = f"Error: {str(e)}"
            print(f"   ❌ {name}: {str(e)}")
            self.total_tests += 1

    def run_test(self, name: str, test_func, category: str):
        """Run a single test function"""
        try:
            result = test_func()
            if result:
                self.test_results[category][name] = "Pass"
                print(f"   ✅ {name}")
                self.passed_tests += 1
            else:
                self.test_results[category][name] = "Fail"
                print(f"   ❌ {name}: Test returned False")
            
            self.total_tests += 1
            
        except Exception as e:
            self.test_results[category][name] = f"Error: {str(e)}"
            print(f"   ❌ {name}: {str(e)}")
            self.total_tests += 1

    def display_test_summary(self):
        """Display comprehensive test results"""
        print("\n" + "=" * 60)
        print("📋 Test Results Summary")
        print("=" * 60)
        
        for category, tests in self.test_results.items():
            if tests:
                print(f"\n{category.replace('_', ' ').title()}:")
                for test_name, result in tests.items():
                    status_icon = "✅" if result == "Pass" else ("⚠️" if result.startswith("Skip") else "❌")
                    print(f"  {status_icon} {test_name}: {result}")
        
        print("\n" + "=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 Overall Results: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 Excellent! Dashboard system is working well.")
        elif success_rate >= 70:
            print("✅ Good! Most features are working correctly.")
        elif success_rate >= 50:
            print("⚠️  Partial success. Some features need attention.")
        else:
            print("❌ Many issues detected. Please check the configuration and ensure all services are running.")
        
        print("\n💡 Troubleshooting Tips:")
        print("   • Ensure PostgreSQL database is running and accessible")
        print("   • Check that all APIs are started with: python run_dashboards.py")
        print("   • Verify .env file configuration matches your database")
        print("   • Install missing dependencies with: pip install -r requirements.txt")
        print("   • Check firewall/port availability for ports 8000, 8001, 8080")
        
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    print("🚀 Starting AVA OLO Dashboard API Tests...")
    print("⚠️  Ensure dashboard system is running (python run_dashboards.py)")
    print("⏳ Waiting 3 seconds for manual confirmation...")
    
    time.sleep(3)
    
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())