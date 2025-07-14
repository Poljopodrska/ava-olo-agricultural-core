#!/usr/bin/env python3
"""Test minimal startup"""
import sys
print("Starting test...")
sys.stdout.flush()

try:
    print("1. Testing FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    print("2. Testing uvicorn import...")
    import uvicorn
    print("✅ Uvicorn imported")
    
    print("3. Testing config_manager import...")
    from config_manager import config
    print(f"✅ Config imported: {config}")
    
    print("4. Testing database_operations import...")
    from database_operations import ConstitutionalDatabaseOperations
    print("✅ Database operations imported")
    
    print("5. Creating FastAPI app...")
    app = FastAPI(title="Test App")
    print("✅ App created")
    
    print("\n✅ ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
print("\nTest complete.")