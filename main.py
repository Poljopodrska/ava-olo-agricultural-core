#!/usr/bin/env python3
"""
AVA OLO Monitoring Dashboards - Diagnostic Mode
This minimal version helps identify deployment issues
"""

import os
import sys
import traceback
from fastapi import FastAPI
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="AVA OLO Monitoring Dashboards - Diagnostic Mode",
    description="Minimal version for debugging AWS deployment issues",
    version="diagnostic-1.0.0"
)

@app.get("/")
async def root():
    """Comprehensive diagnostic information"""
    import_status = {}
    env_status = {}
    
    # Check critical environment variables
    critical_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY", 
        "AWS_REGION",
        "APP_ENV",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_PORT"
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        env_status[var] = {
            "exists": value is not None,
            "length": len(value) if value else 0,
            "preview": value[:15] + "..." if value and len(value) > 15 else value
        }
    
    # Test imports
    test_imports = [
        ("psycopg2", "import psycopg2"),
        ("openai", "import openai"),
        ("asyncpg", "import asyncpg"),
        ("dotenv", "from dotenv import load_dotenv")
    ]
    
    for name, import_cmd in test_imports:
        try:
            exec(import_cmd)
            import_status[name] = "✅ OK"
        except Exception as e:
            import_status[name] = f"❌ {str(e)}"
    
    # Check dotenv
    try:
        from dotenv import load_dotenv
        env_file_exists = os.path.exists('.env')
        dotenv_status = f"File exists: {env_file_exists}"
    except:
        dotenv_status = "Failed to import dotenv"
    
    return {
        "status": "diagnostic",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment_variables": env_status,
        "import_tests": import_status,
        "dotenv_status": dotenv_status,
        "message": "Diagnostic information - check environment_variables section"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "monitoring-dashboards"}

@app.get("/debug/env")
async def debug_env():
    """Debug environment variables (safe version)"""
    env_status = {}
    
    # Check critical environment variables
    critical_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY", 
        "AWS_REGION",
        "APP_ENV",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_PORT"
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        env_status[var] = {
            "exists": value is not None,
            "length": len(value) if value else 0,
            "starts_with": value[:10] + "..." if value and len(value) > 10 else value
        }
    
    return {
        "environment_variables": env_status,
        "python_version": sys.version,
        "working_directory": os.getcwd()
    }

@app.get("/debug/imports")
async def debug_imports():
    """Test critical imports"""
    import_status = {}
    
    # Test each import that might be causing issues
    test_imports = [
        ("fastapi", "from fastapi import FastAPI"),
        ("uvicorn", "import uvicorn"),
        ("asyncpg", "import asyncpg"),
        ("sqlalchemy", "import sqlalchemy"),
        ("openai", "import openai"),
        ("psycopg2", "import psycopg2"),
        ("dotenv", "from dotenv import load_dotenv"),
        ("httpx", "import httpx"),
        ("jinja2", "import jinja2")
    ]
    
    for name, import_cmd in test_imports:
        try:
            exec(import_cmd)
            import_status[name] = {"status": "success", "error": None}
        except Exception as e:
            import_status[name] = {"status": "failed", "error": str(e)}
    
    return {"import_tests": import_status}

@app.get("/debug/dotenv")
async def debug_dotenv():
    """Test dotenv loading"""
    try:
        from dotenv import load_dotenv
        
        # Check if .env file exists
        env_file_exists = os.path.exists('.env')
        
        # Try to load dotenv
        load_result = load_dotenv()
        
        return {
            "dotenv_status": "success",
            "env_file_exists": env_file_exists,
            "load_result": load_result,
            "current_directory": os.getcwd(),
            "directory_contents": os.listdir('.')
        }
    except Exception as e:
        return {
            "dotenv_status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/debug/database")
async def debug_database():
    """Test database connection (read-only)"""
    try:
        import asyncpg
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"status": "failed", "error": "DATABASE_URL not found"}
        
        # Parse the URL to show connection details (safely)
        return {
            "status": "database_url_found", 
            "url_length": len(database_url),
            "url_starts_with": database_url[:20] + "..." if len(database_url) > 20 else database_url
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Keep it simple for startup
if __name__ == "__main__":
    print("🚀 Starting AVA OLO Monitoring Dashboards - Diagnostic Mode")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8080,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        traceback.print_exc()
        sys.exit(1)