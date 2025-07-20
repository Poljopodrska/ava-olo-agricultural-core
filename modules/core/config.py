#!/usr/bin/env python3
"""
Configuration module for AVA OLO Agricultural Core
Handles environment variables, constants, and service configuration
"""
import os
import sys
import hashlib
import logging
from datetime import datetime

# Service-specific deployment tracking
SERVICE_NAME = "agricultural-core"
DEPLOYMENT_TIMESTAMP = '20250720112900'  # Updated for restore deployment
BUILD_ID = hashlib.md5(f"{SERVICE_NAME}-{DEPLOYMENT_TIMESTAMP}".encode()).hexdigest()[:8]
VERSION = f"v3.3.1-restore-{BUILD_ID}"

# CAVA VERSION - Critical for CAVA registration
CAVA_VERSION = "3.3.7-test-isolation"

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def emergency_log(message):
    """Emergency logging that goes to stdout (shows in AWS logs)"""
    timestamp = datetime.now().isoformat()
    print(f"🚨 EMERGENCY LOG {timestamp}: {message}", flush=True)
    sys.stdout.flush()

# Environment detection
def is_production():
    """Check if running in production environment"""
    return os.getenv('ENVIRONMENT') == 'production' or os.getenv('AWS_EXECUTION_ENV') is not None

# API Keys and Service URLs
def get_service_config():
    """Get service configuration from environment"""
    return {
        'llm_service_url': os.getenv('AVA_LLM_SERVICE_URL', 'http://localhost:8001'),
        'cava_llm_model': os.getenv('CAVA_LLM_MODEL', 'gpt-4'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'whatsapp_token': os.getenv('WHATSAPP_TOKEN', 'test-token'),
        'deployment_timestamp': DEPLOYMENT_TIMESTAMP,
        'build_id': BUILD_ID
    }

# Service paths
def get_service_paths():
    """Get paths for templates and static files"""
    return {
        'templates': './templates',
        'static': './static'
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
    print(f"🤖 CAVA VERSION: {CAVA_VERSION}")
    print(f"🌐 SERVICE: Agricultural Core")
    print(f"⏰ DEPLOYED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print(f"FINAL VERSION CHECK: {current_version}")
    
    return current_version

# Export all configuration
config = {
    'service_name': SERVICE_NAME,
    'version': VERSION,
    'cava_version': CAVA_VERSION,
    'build_id': BUILD_ID,
    'deployment_timestamp': DEPLOYMENT_TIMESTAMP,
    'is_production': is_production(),
    'service': get_service_config(),
    'paths': get_service_paths()
}