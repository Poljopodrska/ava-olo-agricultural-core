#!/usr/bin/env python3
"""
Test Language Detection for Slovenian Users
Verifies that IP detection and WhatsApp detection work correctly
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.core.language_service import get_language_service
from modules.core.translations import get_translations

async def test_slovenia_language():
    """Test language detection for Slovenia"""
    
    print("="*60)
    print("SLOVENIA LANGUAGE DETECTION TEST")
    print("="*60)
    
    language_service = get_language_service()
    
    # Test 1: Slovenian IP Detection
    print("\n[TEST 1] Slovenia IP Detection")
    print("-"*60)
    
    test_ips = [
        "193.2.1.1",      # Slovenia IP (ARNES)
        "193.2.222.222",  # Another Slovenia IP
        "91.185.96.1",    # Slovenia IP
    ]
    
    for ip in test_ips:
        detected = await language_service.detect_language_from_ip(ip)
        language_name = language_service.get_language_name(detected)
        print(f"IP {ip} -> {detected} ({language_name})")
        if detected == 'sl':
            print("  [OK] Correctly detected Slovenian")
        else:
            print(f"  [WARNING] Expected 'sl' but got '{detected}'")
    
    # Test 2: Slovenian WhatsApp Detection
    print("\n[TEST 2] Slovenia WhatsApp Number Detection")
    print("-"*60)
    
    test_numbers = [
        "+38640123456",   # Slovenia mobile
        "+38631999888",   # Slovenia mobile
        "+38651777666",   # Slovenia mobile
    ]
    
    for number in test_numbers:
        detected = language_service.detect_language_from_whatsapp(number)
        language_name = language_service.get_language_name(detected)
        print(f"WhatsApp {number} -> {detected} ({language_name})")
        if detected == 'sl':
            print("  [OK] Correctly detected Slovenian")
        else:
            print(f"  [FAIL] Expected 'sl' but got '{detected}'")
    
    # Test 3: Slovenian Translations
    print("\n[TEST 3] Slovenian UI Translations")
    print("-"*60)
    
    sl_translations = get_translations('sl')
    
    print("Sign In Page translations:")
    print(f"  Title: {sl_translations['sign_in_title']}")
    print(f"  Subtitle: {sl_translations['sign_in_subtitle']}")
    print(f"  WhatsApp Label: {sl_translations['whatsapp_label']}")
    print(f"  Password Label: {sl_translations['password_label']}")
    print(f"  Button: {sl_translations['sign_in_button']}")
    
    # Test 4: Complete Flow Simulation
    print("\n[TEST 4] Complete Slovenia User Flow")
    print("-"*60)
    
    # Simulate a user from Slovenia
    slovenia_ip = "193.2.1.1"
    slovenia_whatsapp = "+38640123456"
    
    print("1. User visits from Slovenia IP...")
    detected_from_ip = await language_service.detect_language_from_ip(slovenia_ip)
    print(f"   Language detected from IP: {detected_from_ip}")
    
    print("\n2. Sign-in page should show in Slovenian:")
    translations = get_translations(detected_from_ip)
    print(f"   Page title: '{translations['sign_in_title']}'")
    print(f"   WhatsApp field: '{translations['whatsapp_label']}'")
    
    print("\n3. User enters Slovenian WhatsApp number...")
    detected_from_wa = language_service.detect_language_from_whatsapp(slovenia_whatsapp)
    print(f"   Language confirmed from WhatsApp: {detected_from_wa}")
    
    print("\n4. FAVA/CAVA responses should be in Slovenian")
    print("   All future interactions in Slovenian until user requests change")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_tests_passed = True
    
    # Check IP detection
    ip_test = await language_service.detect_language_from_ip("193.2.1.1")
    if ip_test == 'sl':
        print("[OK] Slovenia IP detection works")
    else:
        print(f"[FAIL] Slovenia IP detection - got '{ip_test}' instead of 'sl'")
        all_tests_passed = False
    
    # Check WhatsApp detection
    wa_test = language_service.detect_language_from_whatsapp("+38640123456")
    if wa_test == 'sl':
        print("[OK] Slovenia WhatsApp detection works")
    else:
        print(f"[FAIL] Slovenia WhatsApp detection - got '{wa_test}' instead of 'sl'")
        all_tests_passed = False
    
    # Check translations exist
    if sl_translations and sl_translations['sign_in_title'] == 'Prijava':
        print("[OK] Slovenian translations available")
    else:
        print("[FAIL] Slovenian translations missing or incorrect")
        all_tests_passed = False
    
    if all_tests_passed:
        print("\n[SUCCESS] All Slovenia language tests passed!")
        print("\nExpected user experience:")
        print("1. Slovenian user visits site -> sees Slovenian UI")
        print("2. Enters +386 number -> confirms Slovenian preference")
        print("3. All chat responses in Slovenian")
        print("4. Can switch language by saying 'speak English please'")
    else:
        print("\n[WARNING] Some tests failed - language may not work correctly")
    
    return all_tests_passed

if __name__ == "__main__":
    result = asyncio.run(test_slovenia_language())
    sys.exit(0 if result else 1)