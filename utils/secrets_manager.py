#!/usr/bin/env python3
"""
AWS Secrets Manager Integration
Securely manage application secrets using AWS Secrets Manager
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class SecretsManager:
    """AWS Secrets Manager client for secure credential management"""
    
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize AWS Secrets Manager client"""
        self.region_name = region_name
        try:
            self.client = boto3.client(
                'secretsmanager',
                region_name=region_name
            )
            logger.info(f"✅ Connected to AWS Secrets Manager in {region_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to AWS Secrets Manager: {e}")
            self.client = None
    
    def create_secret(self, secret_name: str, secret_value: Dict[str, str], description: str = "") -> bool:
        """Create a new secret in AWS Secrets Manager"""
        if not self.client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            response = self.client.create_secret(
                Name=secret_name,
                Description=description,
                SecretString=json.dumps(secret_value)
            )
            logger.info(f"✅ Created secret: {secret_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                logger.info(f"Secret {secret_name} already exists, updating...")
                return self.update_secret(secret_name, secret_value)
            else:
                logger.error(f"❌ Failed to create secret {secret_name}: {e}")
                return False
    
    def update_secret(self, secret_name: str, secret_value: Dict[str, str]) -> bool:
        """Update an existing secret"""
        if not self.client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            response = self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            logger.info(f"✅ Updated secret: {secret_name}")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to update secret {secret_name}: {e}")
            return False
    
    def get_secret(self, secret_name: str) -> Optional[Dict[str, str]]:
        """Retrieve a secret from AWS Secrets Manager"""
        if not self.client:
            logger.error("AWS Secrets Manager client not available")
            return None
        
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            return json.loads(secret_string)
        except ClientError as e:
            logger.error(f"❌ Failed to retrieve secret {secret_name}: {e}")
            return None
    
    def delete_secret(self, secret_name: str, force_delete: bool = False) -> bool:
        """Delete a secret (with optional force delete)"""
        if not self.client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            self.client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=force_delete
            )
            action = "force deleted" if force_delete else "scheduled for deletion"
            logger.info(f"✅ Secret {secret_name} {action}")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to delete secret {secret_name}: {e}")
            return False
    
    def list_secrets(self) -> list:
        """List all secrets"""
        if not self.client:
            logger.error("AWS Secrets Manager client not available")
            return []
        
        try:
            response = self.client.list_secrets()
            return response.get('SecretList', [])
        except ClientError as e:
            logger.error(f"❌ Failed to list secrets: {e}")
            return []

def migrate_env_to_secrets():
    """Migrate environment variables to AWS Secrets Manager"""
    print("🔐 Migrating secrets to AWS Secrets Manager...")
    
    # Initialize secrets manager
    sm = SecretsManager()
    if not sm.client:
        print("❌ Cannot connect to AWS Secrets Manager. Check your credentials.")
        return False
    
    # Define secrets to migrate
    secrets_to_migrate = {
        "ava-olo/database": {
            "DB_HOST": os.getenv('DB_HOST', ''),
            "DB_NAME": os.getenv('DB_NAME', ''),
            "DB_USER": os.getenv('DB_USER', ''),
            "DB_PASSWORD": os.getenv('DB_PASSWORD', ''),
            "DB_PORT": os.getenv('DB_PORT', '5432'),
            "DB_SSL_MODE": os.getenv('DB_SSL_MODE', 'require')
        },
        "ava-olo/admin": {
            "ADMIN_USERNAME": os.getenv('ADMIN_USERNAME', 'admin'),
            "ADMIN_PASSWORD": os.getenv('ADMIN_PASSWORD', ''),
            "ADMIN_PASSWORD_HASH": os.getenv('ADMIN_PASSWORD_HASH', '')
        },
        "ava-olo/api": {
            "API_SECRET_KEY": os.getenv('API_SECRET_KEY', ''),
            "DEV_ACCESS_KEY": os.getenv('DEV_ACCESS_KEY', '')
        }
    }
    
    success_count = 0
    total_count = len(secrets_to_migrate)
    
    for secret_name, secret_values in secrets_to_migrate.items():
        # Filter out empty values
        filtered_values = {k: v for k, v in secret_values.items() if v}
        
        if not filtered_values:
            print(f"⚠️  Skipping {secret_name} - no values to migrate")
            continue
        
        description = f"AVA OLO {secret_name.split('/')[-1]} secrets"
        if sm.create_secret(secret_name, filtered_values, description):
            success_count += 1
            print(f"✅ Migrated: {secret_name}")
        else:
            print(f"❌ Failed to migrate: {secret_name}")
    
    print(f"\n📊 Migration Summary: {success_count}/{total_count} secrets migrated")
    
    if success_count > 0:
        print("\n🔧 Next steps:")
        print("1. Update your applications to use the secrets manager utility")
        print("2. Remove sensitive values from .env files")
        print("3. Update task definitions to use AWS Secrets Manager")
        print("4. Grant ECS tasks permission to access secrets")
    
    return success_count == total_count

def get_database_config() -> Dict[str, str]:
    """Get database configuration from AWS Secrets Manager"""
    sm = SecretsManager()
    config = sm.get_secret("ava-olo/database")
    
    if config:
        logger.info("✅ Database config loaded from AWS Secrets Manager")
        return config
    else:
        logger.warning("⚠️ Failed to load from Secrets Manager, falling back to env vars")
        return {
            "DB_HOST": os.getenv('DB_HOST', ''),
            "DB_NAME": os.getenv('DB_NAME', ''),
            "DB_USER": os.getenv('DB_USER', ''),
            "DB_PASSWORD": os.getenv('DB_PASSWORD', ''),
            "DB_PORT": os.getenv('DB_PORT', '5432'),
            "DB_SSL_MODE": os.getenv('DB_SSL_MODE', 'require')
        }

def get_admin_config() -> Dict[str, str]:
    """Get admin configuration from AWS Secrets Manager"""
    sm = SecretsManager()
    config = sm.get_secret("ava-olo/admin")
    
    if config:
        logger.info("✅ Admin config loaded from AWS Secrets Manager")
        return config
    else:
        logger.warning("⚠️ Failed to load from Secrets Manager, falling back to env vars")
        return {
            "ADMIN_USERNAME": os.getenv('ADMIN_USERNAME', 'admin'),
            "ADMIN_PASSWORD": os.getenv('ADMIN_PASSWORD', ''),
            "ADMIN_PASSWORD_HASH": os.getenv('ADMIN_PASSWORD_HASH', '')
        }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run migration
    migrate_env_to_secrets()