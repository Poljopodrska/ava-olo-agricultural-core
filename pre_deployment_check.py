#!/usr/bin/env python3
"""
AVA OLO Pre-Deployment Safety Check
Ensures the application is ready for AWS deployment
"""

import os
import sys
import json
import psycopg2
from datetime import datetime

class DeploymentChecker:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        
    def add_check(self, name, passed, message):
        """Add a check result"""
        self.checks.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            
    def check_python_syntax(self):
        """Check all Python files for syntax errors"""
        print("\n🔍 Checking Python syntax...")
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip virtual environments and cache
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        syntax_errors = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
        
        if syntax_errors:
            self.add_check("Python Syntax", False, f"Found {len(syntax_errors)} syntax errors")
            for error in syntax_errors[:5]:  # Show first 5 errors
                print(f"  ❌ {error}")
        else:
            self.add_check("Python Syntax", True, f"All {len(python_files)} Python files have valid syntax")
            
    def check_imports(self):
        """Check critical imports"""
        print("\n📦 Checking critical imports...")
        
        critical_imports = [
            ("fastapi", "FastAPI framework"),
            ("uvicorn", "ASGI server"),
            ("psycopg2", "PostgreSQL driver"),
            ("pydantic", "Data validation"),
        ]
        
        missing_imports = []
        for module, description in critical_imports:
            try:
                __import__(module)
            except ImportError:
                missing_imports.append(f"{module} ({description})")
        
        if missing_imports:
            self.add_check("Critical Imports", False, f"Missing: {', '.join(missing_imports)}")
        else:
            self.add_check("Critical Imports", True, "All critical packages available")
            
    def check_environment_vars(self):
        """Check required environment variables"""
        print("\n🔐 Checking environment variables...")
        
        required_vars = [
            "DATABASE_URL",
            "DB_HOST",
            "DB_PASSWORD",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        # DATABASE_URL can be constructed from components
        if "DATABASE_URL" in missing_vars and not any(v in missing_vars for v in ["DB_HOST", "DB_PASSWORD"]):
            missing_vars.remove("DATABASE_URL")
        
        if missing_vars:
            self.add_check("Environment Variables", False, f"Missing: {', '.join(missing_vars)}")
        else:
            self.add_check("Environment Variables", True, "All required environment variables set")
            
    def check_database_connection(self):
        """Test database connection"""
        print("\n🗄️ Checking database connection...")
        
        try:
            # Try to get connection details
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                db_host = os.getenv('DB_HOST')
                db_name = os.getenv('DB_NAME', 'farmer_crm')
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD')
                db_port = os.getenv('DB_PORT', '5432')
                
                if db_host and db_password:
                    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            if not db_url:
                self.add_check("Database Connection", False, "No database configuration found")
                return
                
            # Test connection
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check if core tables exist
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('farmers', 'fields', 'incoming_messages')
            """)
            table_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            if table_count >= 3:
                self.add_check("Database Connection", True, f"Connected, {table_count} core tables found")
            else:
                self.add_check("Database Connection", False, f"Connected but only {table_count}/3 core tables found")
                
        except Exception as e:
            self.add_check("Database Connection", False, f"Connection failed: {str(e)[:50]}")
            
    def check_main_application(self):
        """Check main.py structure"""
        print("\n🎯 Checking main application...")
        
        if not os.path.exists('main.py'):
            self.add_check("Main Application", False, "main.py not found")
            return
            
        try:
            with open('main.py', 'r') as f:
                content = f.read()
                
            # Check for critical components
            checks = {
                "FastAPI app": "app = FastAPI" in content,
                "Database connection": "get_constitutional_db_connection" in content or "get_db_connection" in content,
                "Routes defined": "@app.get" in content or "@app.post" in content,
                "Landing page": '@app.get("/", response_class=HTMLResponse)' in content or '@app.get("/")' in content,
            }
            
            missing = [name for name, found in checks.items() if not found]
            
            if missing:
                self.add_check("Main Application", False, f"Missing: {', '.join(missing)}")
            else:
                self.add_check("Main Application", True, "All critical components present")
                
        except Exception as e:
            self.add_check("Main Application", False, f"Error reading main.py: {str(e)}")
            
    def check_dependencies(self):
        """Check requirements.txt"""
        print("\n📋 Checking dependencies...")
        
        if not os.path.exists('requirements.txt'):
            self.add_check("Dependencies", False, "requirements.txt not found")
            return
            
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
                
            critical_packages = ['fastapi', 'uvicorn', 'psycopg2', 'pydantic']
            missing = [pkg for pkg in critical_packages if pkg not in requirements]
            
            if missing:
                self.add_check("Dependencies", False, f"Missing from requirements.txt: {', '.join(missing)}")
            else:
                self.add_check("Dependencies", True, "All critical packages in requirements.txt")
                
        except Exception as e:
            self.add_check("Dependencies", False, f"Error reading requirements.txt: {str(e)}")
            
    def check_no_hardcoded_secrets(self):
        """Check for hardcoded secrets"""
        print("\n🔒 Checking for hardcoded secrets...")
        
        patterns = [
            'sk-',  # OpenAI API key
            'postgres://',  # Database URL
            'password=',
            'api_key=',
            'secret=',
        ]
        
        found_secrets = []
        for root, dirs, files in os.walk('.'):
            if '.git' in root or 'venv' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            for pattern in patterns:
                                if pattern in content and 'os.getenv' not in content:
                                    # Check if it's not in a comment or example
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines):
                                        if pattern in line and not line.strip().startswith('#'):
                                            found_secrets.append(f"{file_path}:{i+1}")
                    except:
                        pass
        
        if found_secrets:
            self.add_check("Security Check", False, f"Found {len(found_secrets)} potential hardcoded secrets")
            for secret in found_secrets[:3]:
                print(f"  ⚠️  {secret}")
        else:
            self.add_check("Security Check", True, "No hardcoded secrets found")
            
    def run_all_checks(self):
        """Run all deployment checks"""
        print("🚀 AVA OLO Pre-Deployment Safety Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.check_python_syntax()
        self.check_imports()
        self.check_environment_vars()
        self.check_database_connection()
        self.check_main_application()
        self.check_dependencies()
        self.check_no_hardcoded_secrets()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 DEPLOYMENT CHECK SUMMARY")
        print("=" * 50)
        
        for check in self.checks:
            status = "✅" if check["passed"] else "❌"
            print(f"{status} {check['name']}: {check['message']}")
        
        print("\n" + "-" * 50)
        print(f"Total Checks: {len(self.checks)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n✅ DEPLOYMENT READY: All checks passed!")
            return True
        else:
            print(f"\n❌ NOT READY FOR DEPLOYMENT: {self.failed} checks failed")
            print("\nPlease fix the issues above before deploying to AWS.")
            return False

if __name__ == "__main__":
    checker = DeploymentChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)