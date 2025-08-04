#!/usr/bin/env python3
"""
Test the translation fix
"""
import sys
import os

# Add the path
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*60)
print("TESTING TRANSLATION FIX")
print("="*60)

from modules.core.translations import get_translations

# Test English translations
print("\nTesting English translations:")
t = get_translations('en')
print(f"Type: {type(t)}")
print(f"Bool value: {bool(t)}")

# Test attribute access (as templates use it)
print("\nTesting attribute access (t.key):")
print(f"  t.sign_in_title = '{t.sign_in_title}'")
print(f"  t.whatsapp_label = '{t.whatsapp_label}'")
print(f"  t.password_label = '{t.password_label}'")
print(f"  t.sign_in_button = '{t.sign_in_button}'")

# Test missing key
print(f"  t.missing_key = '{t.missing_key}'")

# Test dict access
print("\nTesting dict access (t['key']):")
print(f"  t['sign_in_title'] = '{t['sign_in_title']}'")

# Test get method
print("\nTesting get method:")
print(f"  t.get('sign_in_title', 'default') = '{t.get('sign_in_title', 'default')}'")
print(f"  t.get('missing_key', 'default') = '{t.get('missing_key', 'default')}'")

# Test Slovenian
print("\n" + "-"*60)
print("Testing Slovenian translations:")
t_sl = get_translations('sl')
print(f"  t_sl.sign_in_title = '{t_sl.sign_in_title}'")
print(f"  t_sl.whatsapp_label = '{t_sl.whatsapp_label}'")

print("\n" + "="*60)
print("TRANSLATION FIX TEST COMPLETE")
print("="*60)