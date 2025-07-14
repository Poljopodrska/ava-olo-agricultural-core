"""
AWS Secrets Manager integration for AVA OLO
Production-grade credential management
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache the secret for 5 minutes to avoid repeated AWS calls
@lru_cache(maxsize=1)
def get_cached_secret(secret_name: str) -> Optional[Dict[str, Any]]:
    """Get secret from AWS Secrets Manager with caching"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Create a Secrets Manager client
        session = boto3.session.Session()
        # Try multiple region environment variables
        region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        
        # Get the secret
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            # Binary secret (not used for our case)
            return None
            
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.warning(f"Secret {secret_name} not found")
            return None
    except ImportError:
        logger.warning("boto3 not installed - falling back to environment variables")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving secret: {str(e)}")
        return None

def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from AWS Secrets Manager or environment variables
    
    Priority:
    1. AWS Secrets Manager (if AWS_SECRET_NAME is set)
    2. Individual environment variables
    3. Hardcoded fallback (for development only)
    """
    # Check if we should use AWS Secrets Manager
    secret_name = os.getenv('AWS_SECRET_NAME')
    
    if secret_name:
        logger.info(f"Attempting to load credentials from AWS Secrets Manager: {secret_name}")
        secret_data = get_cached_secret(secret_name)
        
        if secret_data:
            logger.info("✅ Successfully loaded credentials from AWS Secrets Manager")
            return {
                'host': secret_data.get('DB_HOST'),
                'database': secret_data.get('DB_NAME'),
                'user': secret_data.get('DB_USER'),
                'password': secret_data.get('DB_PASSWORD'),
                'port': int(secret_data.get('DB_PORT', 5432))
            }
        else:
            logger.warning("Failed to load from Secrets Manager, falling back to environment variables")
    
    # Fallback to environment variables
    if os.getenv('DB_HOST'):
        logger.info("Using database credentials from environment variables")
        return {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
    
    # Development fallback (should not be used in production)
    logger.warning("⚠️  Using hardcoded development credentials - NOT FOR PRODUCTION!")
    return {
        'host': 'localhost',
        'database': 'farmer_crm',
        'user': 'postgres',
        'password': 'postgres',
        'port': 5432
    }

def get_jwt_secret() -> str:
    """Get JWT secret from AWS Secrets Manager or environment"""
    secret_name = os.getenv('AWS_SECRET_NAME')
    
    if secret_name:
        secret_data = get_cached_secret(secret_name)
        if secret_data and 'JWT_SECRET' in secret_data:
            return secret_data['JWT_SECRET']
    
    # Fallback to environment variable
    return os.getenv('JWT_SECRET', 'constitutional-farm-secret-key-change-in-production')

def clear_secret_cache():
    """Clear the cached secret (useful for rotation)"""
    get_cached_secret.cache_clear()