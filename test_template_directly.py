#!/usr/bin/env python3
"""
Test template rendering directly with Jinja2
"""
import sys
import os

# Add path
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*80)
print("DIRECT TEMPLATE TEST")
print("="*80)

print("\n1. Checking template file...")
template_path = "templates/auth/signin.html"
if os.path.exists(template_path):
    print(f"   [OK] {template_path} exists")
    print(f"   Size: {os.path.getsize(template_path)} bytes")
else:
    print(f"   [ERROR] {template_path} NOT FOUND!")
    sys.exit(1)

print("\n2. Testing Jinja2 rendering...")
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    
    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    print("   [OK] Jinja2 environment created")
    
    # Load the template
    template = env.get_template('auth/signin.html')
    print("   [OK] Template loaded")
    
    # Import translations
    from modules.core.translations import get_translations
    from modules.core.config import VERSION
    
    # Get translations
    t = get_translations('en')
    print(f"   [OK] Translations loaded: {type(t)}")
    
    # Create mock request object
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/auth/signin'})()
            
    # Render the template
    print("\n3. Rendering template...")
    try:
        html = template.render(
            request=MockRequest(),
            version=VERSION,
            language='en',
            t=t
        )
        print(f"   [OK] Template rendered successfully!")
        print(f"   HTML length: {len(html)} characters")
        
        # Check for key elements
        if 'Sign In' in html or 'sign_in_title' in html:
            print("   [OK] Sign-in title found in HTML")
        if 'WhatsApp' in html:
            print("   [OK] WhatsApp field found in HTML")
        if 'Password' in html or 'password' in html.lower():
            print("   [OK] Password field found in HTML")
            
    except Exception as e:
        print(f"   [ERROR] Template rendering failed!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"   [ERROR] Import failed: {e}")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)