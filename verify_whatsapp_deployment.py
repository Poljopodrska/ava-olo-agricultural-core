#!/usr/bin/env python3
"""
Verify WhatsApp integration deployment
Tests all WhatsApp endpoints and functionality
"""
import asyncio
import aiohttp
import json
import sys
from datetime import datetime

class WhatsAppDeploymentVerifier:
    def __init__(self):
        self.base_url = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "details": {}
        }
    
    async def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        endpoints = [
            "/health",
            "/api/v1/health"
        ]
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}{endpoint}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"✅ {endpoint}: OK - {data.get('status', 'unknown')}")
                            self.results["tests_passed"] += 1
                            self.results["details"][endpoint] = "passed"
                        else:
                            print(f"❌ {endpoint}: Failed - HTTP {resp.status}")
                            self.results["tests_failed"] += 1
                            self.results["details"][endpoint] = f"failed - HTTP {resp.status}"
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)}")
                self.results["tests_failed"] += 1
                self.results["details"][endpoint] = f"error - {str(e)}"
    
    async def test_whatsapp_endpoints(self):
        """Test WhatsApp specific endpoints"""
        print("\n🔍 Testing WhatsApp Endpoints...")
        
        endpoints = [
            ("/api/v1/whatsapp/health", "GET"),
            ("/api/v1/whatsapp/config", "GET"),
            ("/api/v1/whatsapp/webhook", "GET"),
            ("/api/v1/whatsapp/diagnostic", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    if method == "GET":
                        async with session.get(f"{self.base_url}{endpoint}") as resp:
                            if resp.status in [200, 201]:
                                data = await resp.json()
                                print(f"✅ {endpoint}: OK")
                                
                                # Special handling for config endpoint
                                if endpoint == "/api/v1/whatsapp/config":
                                    enabled = data.get("enabled", False)
                                    print(f"   WhatsApp Enabled: {'✅' if enabled else '❌'}")
                                    if data.get("configuration_status"):
                                        for key, value in data["configuration_status"].items():
                                            status = '✅' if value else '❌'
                                            print(f"   {key}: {status}")
                                
                                self.results["tests_passed"] += 1
                                self.results["details"][endpoint] = "passed"
                            else:
                                print(f"❌ {endpoint}: Failed - HTTP {resp.status}")
                                self.results["tests_failed"] += 1
                                self.results["details"][endpoint] = f"failed - HTTP {resp.status}"
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)}")
                self.results["tests_failed"] += 1
                self.results["details"][endpoint] = f"error - {str(e)}"
    
    async def test_webhook_post(self):
        """Test WhatsApp webhook POST endpoint"""
        print("\n🔍 Testing WhatsApp Webhook (POST)...")
        
        test_payload = {
            "MessageSid": "TEST_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "From": "whatsapp:+359885123456",
            "Body": "Test message from deployment verifier",
            "To": "whatsapp:+38591857451"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/whatsapp/webhook",
                    data=test_payload
                ) as resp:
                    if resp.status in [200, 201]:
                        print("✅ Webhook POST: OK - Message accepted")
                        self.results["tests_passed"] += 1
                        self.results["details"]["webhook_post"] = "passed"
                    else:
                        print(f"❌ Webhook POST: Failed - HTTP {resp.status}")
                        response_text = await resp.text()
                        print(f"   Response: {response_text[:200]}")
                        self.results["tests_failed"] += 1
                        self.results["details"]["webhook_post"] = f"failed - HTTP {resp.status}"
        except Exception as e:
            print(f"❌ Webhook POST: Error - {str(e)}")
            self.results["tests_failed"] += 1
            self.results["details"]["webhook_post"] = f"error - {str(e)}"
    
    async def test_payment_endpoint(self):
        """Test payment endpoint with Stripe"""
        print("\n🔍 Testing Payment Endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v1/payment/subscribe?farmer_id=1"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "checkout_url" in data and "checkout.stripe.com" in data["checkout_url"]:
                            print("✅ Payment endpoint: OK - Stripe integration working")
                            self.results["tests_passed"] += 1
                            self.results["details"]["payment_endpoint"] = "passed"
                        else:
                            print("⚠️  Payment endpoint: Unexpected response format")
                            self.results["tests_failed"] += 1
                            self.results["details"]["payment_endpoint"] = "unexpected response"
                    elif resp.status == 302 or resp.status == 303:
                        location = resp.headers.get("Location", "")
                        if "checkout.stripe.com" in location:
                            print("✅ Payment endpoint: OK - Redirecting to Stripe")
                            self.results["tests_passed"] += 1
                            self.results["details"]["payment_endpoint"] = "passed"
                        else:
                            print("⚠️  Payment endpoint: Redirect but not to Stripe")
                            self.results["tests_failed"] += 1
                            self.results["details"]["payment_endpoint"] = "wrong redirect"
                    else:
                        print(f"❌ Payment endpoint: Failed - HTTP {resp.status}")
                        self.results["tests_failed"] += 1
                        self.results["details"]["payment_endpoint"] = f"failed - HTTP {resp.status}"
        except Exception as e:
            print(f"❌ Payment endpoint: Error - {str(e)}")
            self.results["tests_failed"] += 1
            self.results["details"]["payment_endpoint"] = f"error - {str(e)}"
    
    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "="*60)
        print("📊 WHATSAPP DEPLOYMENT VERIFICATION REPORT")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print(f"Success Rate: {(self.results['tests_passed'] / (self.results['tests_passed'] + self.results['tests_failed']) * 100):.1f}%")
        
        print("\nDetailed Results:")
        for test, result in self.results["details"].items():
            status = "✅" if result == "passed" else "❌"
            print(f"{status} {test}: {result}")
        
        print("\n" + "="*60)
        
        if self.results["tests_failed"] == 0:
            print("🎉 ALL TESTS PASSED! WhatsApp integration is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the logs and configuration.")
            return False
    
    async def run_verification(self):
        """Run all verification tests"""
        print("🚀 Starting WhatsApp Deployment Verification...")
        print(f"Target: {self.base_url}")
        
        await self.test_health_endpoints()
        await self.test_whatsapp_endpoints()
        await self.test_webhook_post()
        await self.test_payment_endpoint()
        
        return self.generate_report()


async def main():
    verifier = WhatsAppDeploymentVerifier()
    success = await verifier.run_verification()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"whatsapp_verification_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(verifier.results, f, indent=2)
    print(f"\nResults saved to: {filename}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))