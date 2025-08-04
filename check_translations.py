#!/usr/bin/env python3
"""
Check translations structure
"""
import sys
import os

# Add the path
sys.path.insert(0, 'C:/AVA-Projects/ava-olo-agricultural-core')
os.chdir('C:/AVA-Projects/ava-olo-agricultural-core')

print("="*60)
print("CHECKING TRANSLATIONS STRUCTURE")
print("="*60)

from modules.core.translations import get_translations

# Get English translations
print("\nEnglish translations:")
en_trans = get_translations('en')
print(f"Type: {type(en_trans)}")

if isinstance(en_trans, dict):
    print(f"Number of keys: {len(en_trans)}")
    print("\nFirst 10 keys:")
    for i, key in enumerate(list(en_trans.keys())[:10]):
        print(f"  - {key}: {en_trans[key][:50] if isinstance(en_trans[key], str) else en_trans[key]}")
        
    # Check for signin-related keys
    print("\nSign-in related keys:")
    signin_keys = [k for k in en_trans.keys() if 'sign' in k.lower()]
    for key in signin_keys:
        print(f"  - {key}: {en_trans[key][:50] if isinstance(en_trans[key], str) else en_trans[key]}")
        
elif hasattr(en_trans, '__dict__'):
    print("Object with attributes:")
    attrs = en_trans.__dict__
    print(f"Number of attributes: {len(attrs)}")
    print("\nFirst 10 attributes:")
    for i, (key, value) in enumerate(list(attrs.items())[:10]):
        print(f"  - {key}: {value[:50] if isinstance(value, str) else value}")
else:
    print(f"Unknown structure: {en_trans}")

# Check Slovenian translations
print("\n" + "-"*60)
print("Slovenian translations:")
sl_trans = get_translations('sl')
print(f"Type: {type(sl_trans)}")

if isinstance(sl_trans, dict):
    print(f"Number of keys: {len(sl_trans)}")
    print("\nFirst 5 keys:")
    for i, key in enumerate(list(sl_trans.keys())[:5]):
        print(f"  - {key}: {sl_trans[key][:50] if isinstance(sl_trans[key], str) else sl_trans[key]}")