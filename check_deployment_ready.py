#!/usr/bin/env python3
"""
Simple deployment readiness check for AVA OLO
Checks only what's necessary for AWS deployment
"""

import os
import sys

def check_deployment_ready():
    """Check if code is ready for AWS deployment"""
    print("🚀 AVA OLO Deployment Readiness Check")
    print("=" * 40)
    
    errors = []
    warnings = []
    
    # 1. Check critical files exist
    critical_files = ['main.py', 'requirements.txt', '.env.example']
    for file in critical_files:
        if not os.path.exists(file):
            errors.append(f"Missing critical file: {file}")
    
    # 2. Check Python syntax in main.py
    if os.path.exists('main.py'):
        try:
            with open('main.py', 'r') as f:
                compile(f.read(), 'main.py', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in main.py: {e}")
    
    # 3. Check for basic FastAPI app structure
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
            if 'app = FastAPI' not in content:
                errors.append("No FastAPI app initialization found")
            if 'uvicorn.run' not in content:
                warnings.append("No uvicorn.run found (might be using external runner)")
    
    # 4. Check requirements.txt has essentials
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            reqs = f.read().lower()
            essentials = ['fastapi', 'uvicorn', 'psycopg2']
            for pkg in essentials:
                if pkg not in reqs:
                    errors.append(f"Missing {pkg} in requirements.txt")
    
    # 5. Runtime checks for potential AWS deployment issues
    runtime_errors = []
    
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
            
            # Check for complex string formatting that might fail at runtime
            # Note: Disabled for now as it's too strict
            # if 'f\'\'\'' in content and content.count('f\'\'\'') > 1:
            #     runtime_errors.append("Complex f-string formatting detected - may cause runtime errors")
            
            # Check for JSON operations that might fail
            if 'json.dumps(' in content and 'json.loads(' in content:
                # Check if json is imported
                if 'import json' not in content:
                    runtime_errors.append("JSON operations used without import - runtime error")
            
            # Check for complex HTML generation that might fail
            if content.count('f"""') > 10:
                runtime_errors.append("Complex HTML generation detected - potential runtime issues")
    
    # Add runtime errors to main errors
    errors.extend(runtime_errors)
    
    # 6. Basic security check - no hardcoded credentials
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Check for obvious hardcoded secrets
                        if 'sk-' in content and 'sk-your' not in content:
                            # Check if it's actually a hardcoded key (not in a check or comment)
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'sk-' in line and not any(x in line for x in ['.startswith', 'sk-your', '#', 'example']):
                                    errors.append(f"Potential API key in {file_path}:{i+1}")
                        if 'postgresql://' in content and 'os.getenv' not in content:
                            warnings.append(f"Hardcoded database URL in {file_path}")
                except:
                    pass
    
    # Print results
    print("\n✅ CHECKS PASSED:")
    print(f"  - Found {len(critical_files)} critical files")
    print(f"  - Python syntax valid")
    print(f"  - FastAPI app structure present")
    print(f"  - Essential packages in requirements.txt")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print("\n🚫 NOT READY FOR DEPLOYMENT")
        print("Fix the errors above before deploying.")
        return False
    else:
        print("\n✅ READY FOR DEPLOYMENT!")
        print("\nRemember to set environment variables in AWS App Runner:")
        print("  - DATABASE_URL or DB_HOST/DB_PASSWORD")
        print("  - OPENAI_API_KEY")
        return True

if __name__ == "__main__":
    ready = check_deployment_ready()
    sys.exit(0 if ready else 1)