#!/usr/bin/env python3
"""
Run comprehensive registration tests via API endpoint
"""
import asyncio
import aiohttp
import json
import sys

async def run_comprehensive_tests():
    """Run comprehensive registration tests"""
    
    print("🧪 Running Comprehensive Registration Tests")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Calling {base_url}/api/v1/self-test/registration/comprehensive")
            
            async with session.post(f"{base_url}/api/v1/self-test/registration/comprehensive") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Response received")
                    print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
                    print(f"="*60)
                    print(f"✅ PASSED: {data.get('passed', 0)}")
                    print(f"❌ FAILED: {data.get('total', 0) - data.get('passed', 0)}")
                    print(f"📈 SUCCESS RATE: {data.get('success_rate', 0):.1%}")
                    
                    if data.get('failure_categories'):
                        print(f"\n🔍 FAILURE ANALYSIS:")
                        for category, count in data['failure_categories'].items():
                            print(f"  • {category}: {count} failures")
                    
                    recommendation = data.get('recommendation', 'UNKNOWN')
                    if recommendation == 'DEPLOY':
                        print(f"\n🎯 RECOMMENDATION: DEPLOY")
                        print("✅ Registration system is ready for production!")
                    else:
                        print(f"\n⚠️  RECOMMENDATION: FIX_ISSUES")
                        print("❌ Registration system needs improvements")
                        
                        if data.get('failures'):
                            print(f"\n🚨 DETAILED FAILURES:")
                            for failure in data['failures'][:5]:  # Show first 5
                                print(f"  • {failure.get('test', 'Unknown test')}")
                                print(f"    Step {failure.get('step', '?')}: '{failure.get('input', '')}'")
                                print(f"    Expected: {failure.get('expected', [])}")
                                print(f"    Got: {failure.get('actual', '')[:100]}...")
                                print()
                    
                    critical = data.get('critical_failures', False)
                    if critical:
                        print("🚨 CRITICAL: More than 3 failures detected")
                        
                    return data.get('success_rate', 0) >= 0.85
                        
                else:
                    print(f"❌ HTTP {response.status}: {await response.text()}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Make sure the server is running on localhost:8080")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_tests())
    sys.exit(0 if success else 1)