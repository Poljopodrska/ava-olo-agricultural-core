#!/usr/bin/env python3
"""
Test sign-in locally to identify the exact error
"""
import sys
import os
import asyncio
import traceback

# Add path
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*80)
print("LOCAL SIGNIN TEST - FINDING THE EXACT ERROR")
print("="*80)

async def test_signin():
    try:
        print("\n1. Setting up FastAPI app...")
        from fastapi import FastAPI, Request
        from fastapi.templating import Jinja2Templates
        
        # Create minimal app
        app = FastAPI()
        templates = Jinja2Templates(directory="templates")
        
        print("   ✓ FastAPI app created")
        
        print("\n2. Importing modules...")
        from modules.core.config import VERSION
        from modules.core.language_service import get_language_service
        from modules.core.translations import get_translations
        print("   ✓ Modules imported")
        
        print("\n3. Creating mock request...")
        from starlette.datastructures import Headers
        
        class MockClient:
            host = "127.0.0.1"
            port = 80
        
        class MockRequest:
            def __init__(self):
                self.client = MockClient()
                self.headers = Headers({"host": "localhost"})
                
        request = MockRequest()
        print("   ✓ Mock request created")
        
        print("\n4. Testing language detection...")
        language_service = get_language_service()
        client_ip = "127.0.0.1"
        
        try:
            detected_language = await language_service.detect_language_from_ip(client_ip)
            print(f"   ✓ Language detected: {detected_language}")
        except Exception as e:
            print(f"   ⚠ Language detection failed (expected): {e}")
            detected_language = 'en'
            
        print("\n5. Getting translations...")
        translations = get_translations(detected_language)
        print(f"   Type: {type(translations)}")
        print(f"   Has sign_in_title: {hasattr(translations, 'sign_in_title')}")
        if hasattr(translations, 'sign_in_title'):
            print(f"   sign_in_title = '{translations.sign_in_title}'")
            
        print("\n6. Attempting to render template...")
        try:
            # Try to render the template
            response = templates.TemplateResponse("auth/signin.html", {
                "request": request,
                "version": VERSION,
                "language": detected_language,
                "t": translations
            })
            
            print("   ✓ Template rendered successfully!")
            
            # Try to get the body
            body = response.body
            print(f"   Response body length: {len(body)} bytes")
            
        except Exception as e:
            print(f"   ✗ TEMPLATE RENDERING FAILED!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {e}")
            print("\n   Full traceback:")
            traceback.print_exc()
            
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        traceback.print_exc()

# Run the test
print("\nRunning async test...")
asyncio.run(test_signin())

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)