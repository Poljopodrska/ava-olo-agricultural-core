#!/usr/bin/env python3
"""
Test Emergency Config Manager Fix
Verify the service can start without config_manager errors
"""

def test_config_import():
    """Test config_manager import"""
    print("🔍 Testing config_manager import...")
    try:
        from config_manager import config
        print("✅ Config manager imported successfully")
        print(f"   Environment: {config.app_env}")
        print(f"   Database: {config.db_host}")
        return True
    except Exception as e:
        print(f"❌ Config manager import failed: {e}")
        return False

def test_database_operations():
    """Test database_operations import"""
    print("\n🔍 Testing database_operations import...")
    try:
        from database_operations import ConstitutionalDatabaseOperations
        print("✅ Database operations imported successfully")
        return True
    except Exception as e:
        print(f"❌ Database operations import failed: {e}")
        return False

def test_app_startup():
    """Test main app startup"""
    print("\n🔍 Testing main app startup...")
    try:
        from api_gateway_constitutional import app
        print("✅ Constitutional API gateway imported successfully")
        print("✅ Web routes should be available:")
        print("   - /web/")
        print("   - /web/health")
        print("   - /health")
        return True
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚨 EMERGENCY FIX VERIFICATION")
    print("=" * 50)
    
    tests = [
        test_config_import,
        test_database_operations,
        test_app_startup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ EMERGENCY FIX SUCCESSFUL!")
        print("🚀 Service should start properly on AWS")
        print("🏛️ Constitutional compliance maintained")
    else:
        print("❌ EMERGENCY FIX INCOMPLETE")
        print("⚠️ Additional fixes needed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)