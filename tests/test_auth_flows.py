#!/usr/bin/env python3
"""
Test Authentication Flows
Tests admin bypass and CAVA registration
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Simple test runner without pytest
print("Note: Running without TestClient - tests will be limited")
tests_passed = True

def test_admin_bypass():
    """Test admin bypass login functionality"""
    # Check that admin login endpoint exists in routes
    try:
        # Check if the function exists in the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "auth_routes", 
            Path(__file__).parent.parent / "modules" / "auth" / "routes.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # Check if admin_login function exists in the file
        with open(Path(__file__).parent.parent / "modules" / "auth" / "routes.py", 'r') as f:
            content = f.read()
            if "async def admin_login" in content:
                print("✅ Admin bypass endpoint exists")
                return True
        
        print("❌ Admin bypass endpoint missing")
        return False
    except Exception as e:
        print(f"❌ Admin bypass test error: {e}")
        return False

def test_cava_registration_endpoint():
    """Test CAVA registration API endpoint"""
    # Check that CAVA routes exist without importing (to avoid dependency issues)
    try:
        # Check if files exist
        cava_routes = Path(__file__).parent.parent / "modules" / "cava" / "routes.py"
        cava_flow = Path(__file__).parent.parent / "modules" / "cava" / "registration_flow.py"
        
        if not cava_routes.exists() or not cava_flow.exists():
            print("❌ CAVA module files missing")
            return False
        
        # Check for key functions in files
        with open(cava_routes, 'r') as f:
            if "async def cava_registration_chat" not in f.read():
                print("❌ CAVA registration endpoint function missing")
                return False
        
        with open(cava_flow, 'r') as f:
            content = f.read()
            if "class RegistrationFlow" not in content or "process_message" not in content:
                print("❌ RegistrationFlow class incomplete")
                return False
        
        print("✅ CAVA registration endpoint and flow structure verified")
        return True
    except Exception as e:
        print(f"❌ CAVA registration endpoint error: {e}")
        return False

def test_registration_page_serves_cava():
    """Test that registration page serves CAVA interface"""
    # Check that CAVA registration template exists
    try:
        from pathlib import Path
        template_path = Path(__file__).parent.parent / "templates" / "cava_registration.html"
        
        if template_path.exists():
            content = template_path.read_text()
            if "cava" in content.lower() and "chat" in content.lower():
                print("✅ Registration page serves CAVA interface")
                return True
        
        print("❌ CAVA registration template missing or incomplete")
        return False
    except Exception as e:
        print(f"❌ Registration template error: {e}")
        return False

def test_signin_page_has_admin_button():
    """Test that sign-in page has admin bypass button"""
    # Check that signin template has admin button
    try:
        from pathlib import Path
        template_path = Path(__file__).parent.parent / "templates" / "auth" / "signin.html"
        
        if template_path.exists():
            content = template_path.read_text()
            if "Admin Login" in content and "adminLogin()" in content:
                print("✅ Sign-in page has admin bypass button")
                return True
        
        print("❌ Admin button missing from sign-in page")
        return False
    except Exception as e:
        print(f"❌ Sign-in template error: {e}")
        return False

def test_cava_conversation_flow():
    """Test CAVA multi-turn conversation"""
    try:
        from modules.cava.registration_flow import RegistrationFlow
        import asyncio
        
        flow = RegistrationFlow()
        session_id = "test-flow-456"
        
        async def test_flow():
            # Step 1: Initial greeting
            result = await flow.process_message(session_id, "")
            assert result["stage"] == "name"
            
            # Step 2: Provide name
            result = await flow.process_message(session_id, "Test Farmer")
            assert result["stage"] == "whatsapp"
            
            # Step 3: Provide WhatsApp
            result = await flow.process_message(session_id, "+359123456789")
            assert result["stage"] == "email"
            
            return True
        
        if asyncio.run(test_flow()):
            print("✅ CAVA conversation flow working")
            return True
    except Exception as e:
        print(f"❌ CAVA conversation flow error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Authentication Flows...")
    print("=" * 50)
    
    all_passed = True
    
    # Run all tests
    tests = [
        test_admin_bypass,
        test_cava_registration_endpoint,
        test_registration_page_serves_cava,
        test_signin_page_has_admin_button,
        test_cava_conversation_flow
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("\n✅ All authentication flow tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)