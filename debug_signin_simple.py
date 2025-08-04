#!/usr/bin/env python3
"""
Simple debugging for sign-in Internal Server Error
"""
import sys
import os
import traceback

# Add the path
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*80)
print("SIGN-IN ERROR DEBUGGING")
print("="*80)

# Check if signin.html exists
print("\n1. Checking if signin.html template exists...")
signin_path = "templates/auth/signin.html"
if os.path.exists(signin_path):
    print(f"   [OK] {signin_path} exists")
    print(f"   Size: {os.path.getsize(signin_path)} bytes")
else:
    print(f"   [ERROR] {signin_path} NOT FOUND!")

# Try to import and test the route directly
print("\n2. Testing auth routes import...")
try:
    from modules.auth.routes import router, signin_page
    print("   [OK] Auth routes imported successfully")
    print(f"   signin_page function: {signin_page}")
except ImportError as e:
    print(f"   [ERROR] Failed to import auth routes: {e}")
    traceback.print_exc()

# Test language service
print("\n3. Testing language service...")
try:
    from modules.core.language_service import get_language_service
    print("   [OK] Language service imported")
    
    lang_service = get_language_service()
    print(f"   [OK] Language service instance created: {type(lang_service)}")
    
    # Check if method exists
    if hasattr(lang_service, 'detect_language_from_ip'):
        print("   [OK] detect_language_from_ip method exists")
    else:
        print("   [ERROR] detect_language_from_ip method NOT FOUND")
        
except Exception as e:
    print(f"   [ERROR] Language service error: {e}")
    traceback.print_exc()

# Test translations
print("\n4. Testing translations...")
try:
    from modules.core.translations import get_translations
    print("   [OK] Translations module imported")
    
    en_trans = get_translations('en')
    print(f"   [OK] English translations: {type(en_trans)}")
    
    if en_trans:
        # Try to access a common field
        if hasattr(en_trans, 'signin_title'):
            print(f"   [OK] signin_title = '{en_trans.signin_title}'")
        else:
            print("   [WARNING] signin_title not found in translations")
    else:
        print("   [ERROR] English translations is None!")
        
except Exception as e:
    print(f"   [ERROR] Translations error: {e}")
    traceback.print_exc()

# Test the actual signin_page function
print("\n5. Simulating signin_page function...")
try:
    import asyncio
    
    async def test_signin():
        from modules.auth.routes import signin_page
        from fastapi import Request
        from starlette.datastructures import Headers, URL
        from starlette.requests import HTTPConnection
        
        # Create a mock request
        class MockClient:
            host = "127.0.0.1"
            port = 80
            
        class MockRequest(Request):
            def __init__(self):
                self.client = MockClient()
                self._headers = Headers({"host": "localhost"})
                self._url = URL("http://localhost/auth/signin")
                
        try:
            print("   Creating mock request...")
            mock_request = MockRequest()
            
            print("   Calling signin_page...")
            result = await signin_page(mock_request)
            print(f"   [OK] signin_page returned: {type(result)}")
            
        except Exception as e:
            print(f"   [ERROR] signin_page failed: {e}")
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_signin())
    
except Exception as e:
    print(f"   [ERROR] Test setup failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUGGING COMPLETE")
print("="*80)