#!/usr/bin/env python3
"""Test imports for main.py"""
import sys
import os

# Add the directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    
    # Test core imports
    from modules.core.config import config, constitutional_deployment_completion
    print("OK config imports")
    
    from modules.core.translations import TranslationDict
    print("OK translations import")
    
    from modules.core.database_manager import get_db_manager
    print("OK database_manager import")
    
    # Test all route imports
    from modules.api.health_routes import router as health_router
    print("OK health_routes")
    
    from modules.api.weather_routes import router as weather_router
    print("OK weather_routes")
    
    from modules.api.task_management_routes import router as task_management_router
    print("OK task_management_routes")
    
    from modules.api.debug_edi_kante import router as debug_edi_router
    print("OK debug_edi_kante")
    
    # Test main app
    from main import app
    print("OK main app import")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"\nERROR Import failed: {e}")
    import traceback
    traceback.print_exc()