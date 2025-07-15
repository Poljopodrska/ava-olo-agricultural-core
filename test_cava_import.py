#!/usr/bin/env python3
"""Test CAVA import to find the exact error"""

import sys
import traceback

print("Testing CAVA imports...")

try:
    print("1. Importing cava_routes...")
    from api.cava_routes import cava_router
    print("✅ cava_router imported successfully")
    
    print("\n2. Testing router inclusion in FastAPI...")
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(cava_router)
    print("✅ Router included successfully")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to find the exact line
    import re
    tb = traceback.format_exc()
    # Look for file paths and line numbers
    matches = re.findall(r'File "([^"]+)", line (\d+)', tb)
    if matches:
        print("\n📍 Error locations:")
        for file_path, line_num in matches:
            if "site-packages" not in file_path:  # Skip library files
                print(f"  - {file_path}:{line_num}")