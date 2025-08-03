#!/usr/bin/env python3
"""Test critical dependencies at startup"""
import sys

print(f"Python version: {sys.version}")
print("Testing critical dependencies...")

# Test each dependency
dependencies = [
    "psycopg2",
    "fastapi", 
    "uvicorn",
    "jinja2",
    "httpx",
    "dotenv",
    "sqlalchemy",
    "openai",
    "asyncpg",
    "pydantic",
    "psutil",
    "passlib",
    "boto3",
    "twilio",
    "langdetect",
    "stripe"
]

failed = []
for dep in dependencies:
    try:
        __import__(dep)
        print(f"  {dep}: OK")
    except ImportError as e:
        print(f"  {dep}: FAILED - {e}")
        failed.append(dep)

if failed:
    print(f"\nFailed to import: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\nAll dependencies loaded successfully!")
    
# Specific Twilio test
try:
    from twilio.request_validator import RequestValidator
    from twilio.twiml.messaging_response import MessagingResponse
    print("Twilio components loaded successfully!")
except ImportError as e:
    print(f"Twilio components failed: {e}")
    sys.exit(1)