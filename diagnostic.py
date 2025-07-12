#!/usr/bin/env python3
"""Diagnostic script to check repository structure"""
import os

def check_repository_structure():
    """Check what files actually exist for dashboard functionality"""
    
    print("=== CHECKING REPOSITORY STRUCTURE ===")
    
    # Check for main dashboard files
    dashboard_files = [
        'main.py',
        'health_check_dashboard.py',
        'business_dashboard.py', 
        'database_explorer.py',
        'agronomic_approval.py'
    ]
    
    for file in dashboard_files:
        exists = "✅" if os.path.exists(file) else "❌"
        print(f"{exists} {file}")
    
    # Check for templates directory
    templates_exists = "✅" if os.path.exists('templates') else "❌"
    print(f"{templates_exists} templates/")
    
    if os.path.exists('templates'):
        templates = os.listdir('templates')
        for template in templates:
            print(f"  - {template}")
    
    # Check for static directory
    static_exists = "✅" if os.path.exists('static') else "❌"
    print(f"{static_exists} static/")
    
    print("\n=== KEY FILES IN REPOSITORY ===")
    for file in os.listdir('.'):
        if file.endswith('.py') and not file.startswith('.'):
            print(f"  {file}")

if __name__ == "__main__":
    check_repository_structure()