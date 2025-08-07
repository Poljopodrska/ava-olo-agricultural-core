#!/usr/bin/env python3
"""
Configuration module for AVA OLO Monitoring Dashboards
Handles environment variables, constants, and service configuration
"""
import os
import sys
import hashlib
import logging
from datetime import datetime

# Service-specific deployment tracking
SERVICE_NAME = "agricultural-core"
DEPLOYMENT_TIMESTAMP = '20250807001200'  # v4.19.2 - Add detailed logging for message saving
COMMIT_HASH = "debug-message-saving"  # Debug why messages aren't being saved to database
BUILD_ID = f"{COMMIT_HASH}-{hashlib.md5(f'{SERVICE_NAME}-{DEPLOYMENT_TIMESTAMP}'.encode()).hexdigest()[:8]}"
VERSION = "v4.19.2"

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
def get_database_config():
    """Get database configuration from environment variables"""
    # Construct DATABASE_URL from individual components if not set
    if not os.getenv('DATABASE_URL'):
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME', 'farmer_crm')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', '5432')
        
        # Handle potential HTML encoding issues from AWS ECS
        if db_password:
            # Check if password appears to be HTML-encoded
            if '&lt;' in db_password or '&gt;' in db_password or '&amp;' in db_password:
                import html
                db_password = html.unescape(db_password)
        
        # URL encode the password for special characters
        if db_password:
            import urllib.parse
            db_password_encoded = urllib.parse.quote_plus(db_password)
        else:
            db_password_encoded = ''
        
        # Construct the URL
        if db_host and db_password_encoded:
            DATABASE_URL = f"postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}"
            os.environ['DATABASE_URL'] = DATABASE_URL
        else:
            DATABASE_URL = None
    else:
        DATABASE_URL = os.getenv('DATABASE_URL')
    
    return {
        'url': DATABASE_URL,
        'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
        'database': os.getenv('DB_NAME', 'postgres'),  # asyncpg expects 'database' key
        'name': os.getenv('DB_NAME', 'postgres'),  # Keep for backward compatibility
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'j2D8J4LH:~eFrUz>$:kkNT(P$Rq_'),
        'port': os.getenv('DB_PORT', '5432')
    }

# Environment detection
def is_production():
    """Check if running in production environment"""
    return os.getenv('ENVIRONMENT') == 'production' or os.getenv('AWS_EXECUTION_ENV') is not None

# API Keys
def get_api_keys():
    """Get API keys from environment"""
    return {
        'google_maps': os.getenv('GOOGLE_MAPS_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY')
    }

# Service paths
def get_service_paths():
    """Get paths for static files and templates"""
    return {
        'static': './static',
        'templates': './templates'
    }

# Version Management
def get_current_service_version():
    """Get the current version"""
    return VERSION

def constitutional_deployment_completion():
    """Report version after every deployment - CONSTITUTIONAL REQUIREMENT"""
    current_version = get_current_service_version()
    
    print("=" * 50)
    print("🏛️ CONSTITUTIONAL DEPLOYMENT COMPLETE")
    print(f"📊 CURRENT VERSION: {current_version}")
    print(f"🌐 SERVICE: Monitoring Dashboards")
    print(f"⏰ DEPLOYED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print(f"FINAL VERSION CHECK: {current_version}")
    
    return current_version

# Export all configuration
config = {
    'service_name': SERVICE_NAME,
    'version': VERSION,
    'build_id': BUILD_ID,
    'deployment_timestamp': DEPLOYMENT_TIMESTAMP,
    'database': get_database_config(),
    'is_production': is_production(),
    'api_keys': get_api_keys(),
    'paths': get_service_paths()
}