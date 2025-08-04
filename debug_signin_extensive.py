#!/usr/bin/env python3
"""
EXTENSIVE DEBUGGING for sign-in Internal Server Error
Tests every possible failure point
"""
import sys
import os
import traceback
import importlib.util

# Add the path to the agricultural-core module
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*80)
print("EXTENSIVE SIGN-IN DEBUGGING")
print("="*80)

# Test 1: Check if all required files exist
print("\n1. CHECKING FILE EXISTENCE:")
print("-"*40)
files_to_check = [
    "templates/auth/signin.html",
    "modules/auth/routes.py",
    "modules/core/language_service.py",
    "modules/core/translations.py",
    "modules/core/config.py",
    "modules/core/database_manager.py"
]

all_files_exist = True
for file_path in files_to_check:
    exists = os.path.exists(file_path)
    print(f"  {'✓' if exists else '✗'} {file_path}: {'EXISTS' if exists else 'MISSING'}")
    if not exists:
        all_files_exist = False

# Test 2: Try importing each module
print("\n2. TESTING MODULE IMPORTS:")
print("-"*40)

modules_to_test = [
    ("modules.core.config", "config.py"),
    ("modules.core.translations", "translations.py"),
    ("modules.core.language_service", "language_service.py"),
    ("modules.core.database_manager", "database_manager.py"),
    ("modules.auth.routes", "auth/routes.py")
]

for module_name, file_desc in modules_to_test:
    try:
        print(f"\n  Testing: {module_name}")
        module = __import__(module_name, fromlist=[''])
        print(f"    ✓ Import successful")
        
        # Check specific functions/classes
        if module_name == "modules.core.language_service":
            if hasattr(module, 'get_language_service'):
                print(f"    ✓ get_language_service function found")
            else:
                print(f"    ✗ get_language_service function NOT FOUND")
                
        if module_name == "modules.core.translations":
            if hasattr(module, 'get_translations'):
                print(f"    ✓ get_translations function found")
            else:
                print(f"    ✗ get_translations function NOT FOUND")
                
    except ImportError as e:
        print(f"    ✗ Import failed: {e}")
    except Exception as e:
        print(f"    ✗ Unexpected error: {e}")
        traceback.print_exc()

# Test 3: Check template syntax
print("\n3. CHECKING TEMPLATE SYNTAX:")
print("-"*40)

signin_template_path = "templates/auth/signin.html"
if os.path.exists(signin_template_path):
    with open(signin_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for common template issues
    issues = []
    
    # Check if template uses undefined variables
    if '{{ t.' in content:
        print("  ✓ Template uses translation variables (t.)")
    else:
        print("  ⚠ Template doesn't use translation variables")
    
    # Check for unclosed tags
    open_brackets = content.count('{{')
    close_brackets = content.count('}}')
    if open_brackets == close_brackets:
        print(f"  ✓ Template brackets balanced ({open_brackets} pairs)")
    else:
        print(f"  ✗ TEMPLATE BRACKETS UNBALANCED: {{ = {open_brackets}, }} = {close_brackets}")
        issues.append("Unbalanced brackets")
    
    # Check for missing endif/endfor
    if_count = content.count('{% if')
    endif_count = content.count('{% endif')
    if if_count == endif_count:
        print(f"  ✓ If statements balanced ({if_count} pairs)")
    else:
        print(f"  ✗ IF STATEMENTS UNBALANCED: if = {if_count}, endif = {endif_count}")
        issues.append("Unbalanced if statements")
        
    for_count = content.count('{% for')
    endfor_count = content.count('{% endfor')
    if for_count == endfor_count:
        print(f"  ✓ For loops balanced ({for_count} pairs)")
    else:
        print(f"  ✗ FOR LOOPS UNBALANCED: for = {for_count}, endfor = {endfor_count}")
        issues.append("Unbalanced for loops")

# Test 4: Test language service directly
print("\n4. TESTING LANGUAGE SERVICE:")
print("-"*40)

try:
    from modules.core.language_service import get_language_service
    
    print("  Creating language service instance...")
    lang_service = get_language_service()
    print("  ✓ Language service created")
    
    # Check if it has the required method
    if hasattr(lang_service, 'detect_language_from_ip'):
        print("  ✓ detect_language_from_ip method exists")
        
        # Try to check if it's async
        import inspect
        if inspect.iscoroutinefunction(lang_service.detect_language_from_ip):
            print("  ✓ detect_language_from_ip is async (coroutine)")
        else:
            print("  ✗ detect_language_from_ip is NOT async - THIS WILL CAUSE ERRORS!")
    else:
        print("  ✗ detect_language_from_ip method NOT FOUND")
        
except Exception as e:
    print(f"  ✗ Error testing language service: {e}")
    traceback.print_exc()

# Test 5: Test translations
print("\n5. TESTING TRANSLATIONS:")
print("-"*40)

try:
    from modules.core.translations import get_translations
    
    # Test getting English translations
    print("  Getting English translations...")
    en_trans = get_translations('en')
    if en_trans:
        print(f"  ✓ English translations loaded: {type(en_trans)}")
        if hasattr(en_trans, '__dict__'):
            print(f"    Has {len(en_trans.__dict__)} attributes")
    else:
        print("  ✗ English translations returned None or empty")
        
    # Test getting Slovenian translations
    print("  Getting Slovenian translations...")
    sl_trans = get_translations('sl')
    if sl_trans:
        print(f"  ✓ Slovenian translations loaded: {type(sl_trans)}")
    else:
        print("  ⚠ Slovenian translations returned None or empty")
        
except Exception as e:
    print(f"  ✗ Error testing translations: {e}")
    traceback.print_exc()

# Test 6: Check FastAPI route registration
print("\n6. CHECKING ROUTE REGISTRATION:")
print("-"*40)

try:
    from modules.auth.routes import router
    
    # Check if signin route exists
    routes = []
    for route in router.routes:
        if hasattr(route, 'path'):
            routes.append((route.path, route.methods if hasattr(route, 'methods') else 'N/A'))
            
    print(f"  Found {len(routes)} routes in auth router:")
    for path, methods in routes:
        print(f"    {path}: {methods}")
        
    # Check specifically for signin
    signin_get = any('/signin' in path and 'GET' in str(methods) for path, methods in routes)
    signin_post = any('/signin' in path and 'POST' in str(methods) for path, methods in routes)
    
    if signin_get:
        print("  ✓ GET /auth/signin route registered")
    else:
        print("  ✗ GET /auth/signin route NOT FOUND")
        
    if signin_post:
        print("  ✓ POST /auth/signin route registered")
    else:
        print("  ✗ POST /auth/signin route NOT FOUND")
        
except Exception as e:
    print(f"  ✗ Error checking routes: {e}")
    traceback.print_exc()

# Test 7: Simulate the signin_page function
print("\n7. SIMULATING SIGNIN_PAGE FUNCTION:")
print("-"*40)

try:
    import asyncio
    from fastapi import Request
    from fastapi.templating import Jinja2Templates
    
    async def test_signin_page():
        try:
            print("  Step 1: Import modules...")
            from modules.core.language_service import get_language_service
            from modules.core.translations import get_translations
            from modules.core.config import VERSION
            print("    ✓ Imports successful")
            
            print("  Step 2: Get language service...")
            language_service = get_language_service()
            print("    ✓ Language service obtained")
            
            print("  Step 3: Test language detection...")
            test_ip = "127.0.0.1"
            try:
                detected_language = await language_service.detect_language_from_ip(test_ip)
                print(f"    ✓ Language detected: {detected_language}")
            except Exception as e:
                print(f"    ⚠ Language detection failed (expected): {e}")
                detected_language = 'en'
                
            print("  Step 4: Get translations...")
            translations = get_translations(detected_language)
            if translations:
                print(f"    ✓ Translations obtained: {type(translations)}")
            else:
                print("    ✗ Translations is None!")
                
            print("  Step 5: Prepare template context...")
            context = {
                "request": "mock_request",
                "version": VERSION,
                "language": detected_language,
                "t": translations
            }
            print(f"    ✓ Context prepared: {list(context.keys())}")
            
            print("  Step 6: Check template rendering...")
            templates = Jinja2Templates(directory="templates")
            
            # We can't actually render without a real Request object, but we can check if template exists
            template_path = "auth/signin.html"
            full_path = os.path.join("templates", template_path)
            if os.path.exists(full_path):
                print(f"    ✓ Template exists at {full_path}")
            else:
                print(f"    ✗ Template NOT FOUND at {full_path}")
                
        except Exception as e:
            print(f"  ✗ Error in simulation: {e}")
            traceback.print_exc()
    
    # Run the async test
    print("  Running async simulation...")
    asyncio.run(test_signin_page())
    
except Exception as e:
    print(f"  ✗ Error setting up simulation: {e}")
    traceback.print_exc()

# Test 8: Check for circular imports
print("\n8. CHECKING FOR CIRCULAR IMPORTS:")
print("-"*40)

try:
    # Try importing in different orders
    print("  Testing import order 1...")
    import importlib
    importlib.reload(sys.modules.get('modules.core.config', sys))
    importlib.reload(sys.modules.get('modules.core.translations', sys))
    importlib.reload(sys.modules.get('modules.core.language_service', sys))
    print("    ✓ Import order 1 successful")
    
    print("  Testing import order 2...")
    importlib.reload(sys.modules.get('modules.auth.routes', sys))
    print("    ✓ Import order 2 successful")
    
except Exception as e:
    print(f"  ✗ Circular import detected: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUGGING COMPLETE - CHECK RESULTS ABOVE")
print("="*80)

# Final diagnosis
print("\nFINAL DIAGNOSIS:")
print("-"*40)
print("Most likely causes of Internal Server Error:")
print("1. Template file missing or has syntax errors")
print("2. Language service not returning expected format")
print("3. Translations module not returning proper object")
print("4. Async/await issue in route handler")
print("5. Template trying to access undefined variables")
print("\nCheck the results above to identify the exact issue.")