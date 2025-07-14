"""
AWS App Runner Startup Diagnostic
Identifies the correct way to start the application
"""

import os
import sys
import importlib.util
from pathlib import Path

def find_fastapi_apps():
    """Find all FastAPI app instances"""
    apps_found = []
    
    # Look for Python files with FastAPI
    for py_file in Path('.').glob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            if 'FastAPI' in content and 'app =' in content:
                # Try to extract app variable name
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'FastAPI' in line and '=' in line:
                        app_var = line.split('=')[0].strip()
                        apps_found.append({
                            'file': str(py_file),
                            'app_variable': app_var,
                            'has_uvicorn': 'uvicorn.run' in content,
                            'has_main': 'if __name__' in content,
                            'port_in_uvicorn': '8000' in content or '8080' in content
                        })
                        break
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return apps_found

def check_port_config():
    """Check port configuration"""
    port_configs = []
    
    for py_file in Path('.').glob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            if 'port' in content.lower():
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if 'port' in line.lower() and ('=' in line or 'uvicorn' in line):
                        port_configs.append({
                            'file': str(py_file),
                            'line': line_num,
                            'content': line.strip()
                        })
        except Exception:
            pass
    
    return port_configs

def check_imports():
    """Check for import issues"""
    import_issues = []
    
    main_files = ['api_gateway_constitutional.py', 'api_gateway_simple.py', 'api_gateway_localized.py']
    
    for file in main_files:
        if Path(file).exists():
            try:
                with open(file, 'r') as f:
                    content = f.read()
                
                # Look for imports
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        if 'database_operations' in line and 'constitutional' in line:
                            import_issues.append({
                                'file': file,
                                'line': line_num,
                                'issue': 'Missing database_operations_constitutional.py',
                                'content': line.strip()
                            })
            except Exception as e:
                import_issues.append({
                    'file': file,
                    'issue': f'Could not read file: {e}'
                })
    
    return import_issues

def main():
    print("🔍 AWS APP RUNNER STARTUP DIAGNOSTIC")
    print("=" * 50)
    
    # Find FastAPI apps
    apps = find_fastapi_apps()
    print(f"\n📱 FASTAPI APPS FOUND: {len(apps)}")
    for app in apps:
        print(f"  File: {app['file']}")
        print(f"  App Variable: {app['app_variable']}")
        print(f"  Has uvicorn.run: {app['has_uvicorn']}")
        print(f"  Has __main__: {app['has_main']}")
        print(f"  Port in code: {app['port_in_uvicorn']}")
        print()
    
    # Check ports
    ports = check_port_config()
    print(f"🔌 PORT CONFIGURATIONS: {len(ports)}")
    for port in ports:
        print(f"  {port['file']}:{port['line']} - {port['content']}")
    
    # Check imports
    imports = check_imports()
    print(f"\n🚨 IMPORT ISSUES: {len(imports)}")
    for issue in imports:
        print(f"  {issue['file']}: {issue['issue']}")
        if 'content' in issue:
            print(f"    Line: {issue['content']}")
    
    # Check for missing files
    print("\n📁 FILE EXISTENCE CHECK:")
    critical_files = [
        'database_operations_constitutional.py',
        'database_operations.py', 
        'llm_first_database_engine.py',
        'ava-olo-shared/config_manager.py'
    ]
    
    for file in critical_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
    
    # Recommendations
    print("\n🚀 STARTUP RECOMMENDATIONS:")
    
    if apps:
        # Find the best app to use
        constitutional_app = None
        simple_app = None
        
        for app in apps:
            if 'constitutional' in app['file']:
                constitutional_app = app
            elif 'simple' in app['file']:
                simple_app = app
        
        main_app = constitutional_app or simple_app or apps[0]
        
        print(f"1. 🎯 RECOMMENDED APP: {main_app['file']}")
        print(f"2. App variable: {main_app['app_variable']}")
        
        # Check port issue
        if main_app['port_in_uvicorn'] and '8000' in str(main_app):
            print(f"3. ⚠️ PORT ISSUE: Using port 8000, AWS App Runner needs 8080")
        else:
            print(f"3. ✅ Port: Should be compatible")
        
        # Generate startup command
        file_name = main_app['file'].replace('.py', '')
        app_var = main_app['app_variable']
        
        print(f"4. 🚀 AWS App Runner command: uvicorn {file_name}:{app_var} --host 0.0.0.0 --port 8080")
        
        # Check if main can be run directly
        if main_app['has_uvicorn'] and main_app['has_main']:
            print(f"5. 🔄 Alternative: python3 {main_app['file']} (but fix port to 8080)")
        
    else:
        print("❌ No FastAPI apps found!")
        print("   - No files contain both 'FastAPI' and 'app ='")
    
    # Check for missing environment
    print("\n🔑 ENVIRONMENT CHECK:")
    critical_vars = ['OPENAI_API_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = []
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: MISSING")
            missing_vars.append(var)
    
    # Final diagnosis
    print("\n🏥 DIAGNOSIS:")
    
    issues = []
    
    if not apps:
        issues.append("❌ No FastAPI apps found")
    
    if imports:
        issues.append("❌ Import errors detected")
    
    if missing_vars:
        issues.append(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    
    # Check for wrong port
    port_issues = [p for p in ports if '8000' in p['content'] and 'uvicorn' in p['content']]
    if port_issues:
        issues.append("❌ Wrong port (8000 instead of 8080)")
    
    if not issues:
        print("✅ No critical issues found - should work!")
    else:
        print("🚨 CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)