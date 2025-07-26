#!/usr/bin/env python3
"""
Pre-deployment test runner for CAVA Registration
Ensures 100% Constitutional compliance before deployment
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import the test suite
from tests.test_cava_registration_llm import run_all_tests

def check_environment():
    """Check required environment variables"""
    print("🔍 CHECKING ENVIRONMENT...")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not set!")
        
        # Try to load from .env.production
        try:
            from dotenv import load_dotenv
            if os.path.exists(".env.production"):
                load_dotenv(".env.production")
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    print("✅ Loaded OPENAI_API_KEY from .env.production")
                else:
                    print("❌ .env.production exists but no OPENAI_API_KEY found")
                    return False
            else:
                print("❌ .env.production file not found")
                return False
        except ImportError:
            print("❌ python-dotenv not installed, cannot load .env files")
            return False
    else:
        print(f"✅ OPENAI_API_KEY configured (prefix: {openai_key[:10]}...)")
    
    # Check required packages
    required_packages = ["openai", "langdetect", "httpx"]
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} not installed")
            return False
    
    return True

def create_deployment_report(results: dict, pass_rate: float):
    """Create deployment readiness report"""
    report = {
        "deployment_readiness": {
            "timestamp": datetime.now().isoformat(),
            "constitutional_compliance": pass_rate >= 95,
            "deployment_allowed": pass_rate == 100,
            "pass_rate": pass_rate,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if "PASSED" in r["status"]),
            "constitutional_amendment": "Amendment #15 - 95%+ LLM intelligence required"
        },
        "test_results": results,
        "environmental_check": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "required_packages": ["openai", "langdetect", "httpx"]
        }
    }
    
    # Save report
    with open("deployment_readiness_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

async def main():
    """Main test runner"""
    print("🏛️ CAVA REGISTRATION - CONSTITUTIONAL COMPLIANCE TEST")
    print("=" * 70)
    print("Amendment #15: System must demonstrate 95%+ LLM intelligence")
    print("Deployment BLOCKED unless ALL tests pass (100%)")
    print()
    
    # Check environment first
    if not check_environment():
        print("\n🚨 ENVIRONMENT CHECK FAILED")
        print("Fix environment issues before running tests")
        return False
    
    print("\n🧪 RUNNING UNFAKEABLE LLM TESTS...")
    print("These tests can ONLY pass with real AI intelligence:")
    print("- Multi-language understanding")
    print("- Context awareness")
    print("- Intent extraction from garbled text")
    print("- Conversation memory")
    print("- Intelligent validation")
    print("- No hallucination")
    print()
    
    # Run the test suite
    try:
        results, pass_rate = await run_all_tests()
        
        # Create deployment report
        report = create_deployment_report(results, pass_rate)
        
        print("\n" + "=" * 70)
        print("📊 FINAL ASSESSMENT")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Constitutional Compliance: {'✅ YES' if pass_rate >= 95 else '❌ NO'}")
        print(f"Deployment Allowed: {'✅ YES' if pass_rate == 100 else '❌ BLOCKED'}")
        
        if pass_rate == 100:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Constitutional Amendment #15 compliance verified")
            print("✅ System demonstrates 100% LLM intelligence")
            print("✅ Safe to deploy to production")
            
            # Create success marker
            with open("DEPLOYMENT_APPROVED.txt", "w") as f:
                f.write(f"DEPLOYMENT APPROVED\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Pass Rate: {pass_rate}%\n")
                f.write(f"Constitutional Compliance: Verified\n")
                f.write(f"LLM Intelligence: 100%\n")
            
            print("📄 Created DEPLOYMENT_APPROVED.txt")
            
        else:
            print("\n🚨 DEPLOYMENT BLOCKED!")
            print("❌ Not all tests passed - Constitutional violation")
            print("❌ System does not meet 95%+ LLM intelligence requirement")
            
            # Show failures
            print("\n🔍 FAILED TESTS:")
            for test_name, result in results.items():
                if "FAILED" in result["status"] or "ERROR" in result["status"]:
                    print(f"  ❌ {test_name}")
                    if result["error"]:
                        print(f"     Error: {result['error']}")
            
            print("\n📋 REQUIRED ACTIONS:")
            print("1. Fix failing tests")
            print("2. Ensure OpenAI API is properly configured")
            print("3. Verify LLM responses are natural and intelligent")
            print("4. Re-run tests until 100% pass rate achieved")
            
            # Create failure marker
            with open("DEPLOYMENT_BLOCKED.txt", "w") as f:
                f.write(f"DEPLOYMENT BLOCKED\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Pass Rate: {pass_rate}%\n")
                f.write(f"Constitutional Violation: Amendment #15\n")
                f.write(f"Required: 95%+ LLM intelligence\n")
                f.write(f"Achieved: {pass_rate}%\n")
        
        print(f"\n📄 Full report saved to: deployment_readiness_report.json")
        return pass_rate == 100
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        print("Cannot verify constitutional compliance")
        
        # Create error marker
        with open("DEPLOYMENT_ERROR.txt", "w") as f:
            f.write(f"DEPLOYMENT ERROR\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {str(e)}\n")
            f.write(f"Status: Cannot verify constitutional compliance\n")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    print("\n" + "=" * 70)
    if success:
        print("🟢 READY FOR DEPLOYMENT")
        exit(0)
    else:
        print("🔴 DEPLOYMENT BLOCKED")
        exit(1)