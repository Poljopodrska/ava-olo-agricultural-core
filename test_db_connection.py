"""
Test database connection with different password handling methods
This will help us diagnose the exact issue
"""
from fastapi import FastAPI
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/test-db-env")
async def test_db_environment():
    """Test what environment variables are being read"""
    return {
        "DB_HOST": os.getenv('DB_HOST', 'not-set'),
        "DB_NAME": os.getenv('DB_NAME', 'not-set'),
        "DB_USER": os.getenv('DB_USER', 'not-set'),
        "DB_PASSWORD_LENGTH": len(os.getenv('DB_PASSWORD', '')),
        "DB_PASSWORD_FIRST_10": os.getenv('DB_PASSWORD', '')[:10] + "...",
        "DB_PASSWORD_HAS_DOLLAR": '$' in os.getenv('DB_PASSWORD', ''),
        "DB_PORT": os.getenv('DB_PORT', 'not-set')
    }

@app.get("/test-db-connection")
async def test_db_connection():
    """Test different connection methods"""
    results = []
    
    # Method 1: Using environment variable
    try:
        password_env = os.getenv('DB_PASSWORD', '')
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=password_env,
            port=int(os.getenv('DB_PORT', '5432')),
            connect_timeout=5,
            sslmode='prefer'
        )
        conn.close()
        results.append({"method": "env_variable", "success": True, "password_len": len(password_env)})
    except Exception as e:
        results.append({"method": "env_variable", "success": False, "error": str(e)})
    
    # Method 2: Using hardcoded password with special handling
    try:
        # Using raw string
        password_raw = r'2hpzvrg_xP~qNbz1[_NppSK$e*O1'
        conn = psycopg2.connect(
            host='farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
            database='farmer_crm',
            user='postgres',
            password=password_raw,
            port=5432,
            connect_timeout=5,
            sslmode='prefer'
        )
        conn.close()
        results.append({"method": "hardcoded_raw", "success": True})
    except Exception as e:
        results.append({"method": "hardcoded_raw", "success": False, "error": str(e)})
    
    # Method 3: Password with escaped dollar
    try:
        password_escaped = '2hpzvrg_xP~qNbz1[_NppSK$$e*O1'  # Double $$ 
        conn = psycopg2.connect(
            host='farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
            database='farmer_crm',
            user='postgres',
            password=password_escaped,
            port=5432,
            connect_timeout=5,
            sslmode='prefer'
        )
        conn.close()
        results.append({"method": "escaped_dollar", "success": True})
    except Exception as e:
        results.append({"method": "escaped_dollar", "success": False, "error": str(e)})
    
    return {
        "connection_tests": results,
        "recommendation": "Check which method succeeds"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)