#!/usr/bin/env python3
"""
Test the self-test endpoint
"""
import asyncio
import aiohttp
import json

async def test_self_test_endpoint():
    """Test the self-test endpoint"""
    
    print("🧪 Testing Self-Test Endpoint")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Calling {base_url}/api/v1/self-test/registration")
            
            async with session.post(f"{base_url}/api/v1/self-test/registration") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Response received")
                    print(f"📊 Results:")
                    print(f"   Status: {data.get('status', 'Unknown')}")
                    print(f"   Success Rate: {data.get('success_rate', 0):.1%}")
                    print(f"   Passed: {data.get('passed', 0)}/{data.get('total', 0)}")
                    
                    if data.get('failures'):
                        print(f"❌ Failures:")
                        for failure in data['failures']:
                            print(f"   - {failure.get('test', 'Unknown test')}")
                    
                    if data.get('status') == 'PASSED':
                        print("🎉 ALL TESTS PASSED!")
                    else:
                        print("⚠️  Some tests failed")
                        
                else:
                    print(f"❌ HTTP {response.status}: {await response.text()}")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Make sure the server is running on localhost:8080")

if __name__ == "__main__":
    asyncio.run(test_self_test_endpoint())