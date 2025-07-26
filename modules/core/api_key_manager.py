"""
Multi-Layer API Key Management with Fallbacks and Self-Healing
"""
import os
import json
from typing import Optional, Dict, List
import asyncio
from datetime import datetime
import logging

# Optional boto3 import
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Multi-layer API key management with fallbacks"""
    
    # Class-level storage for persistence
    _cached_key: Optional[str] = None
    _last_check: Optional[datetime] = None
    _key_sources: List[str] = []
    
    @classmethod
    async def ensure_api_key(cls) -> bool:
        """Ensure API key is available through multiple methods"""
        
        cls._last_check = datetime.now()
        cls._key_sources = []
        
        # Method 1: Check if already cached
        if cls._cached_key and cls._cached_key.startswith("sk-"):
            os.environ["OPENAI_API_KEY"] = cls._cached_key
            try:
                import openai
                openai.api_key = cls._cached_key
            except:
                pass
            cls._key_sources.append("cached")
            logger.info("✅ Using cached API key")
            return True
        
        # Method 2: Environment variables (multiple names)
        env_names = [
            "OPENAI_API_KEY",
            "OPENAI_KEY",
            "openai_api_key",
            "OPENAIKEY",
            "OPENAI_API_TOKEN"
        ]
        
        for env_name in env_names:
            key = os.getenv(env_name)
            if key and key.startswith("sk-"):
                cls._cached_key = key
                os.environ["OPENAI_API_KEY"] = key
                try:
                    import openai
                    openai.api_key = key
                except:
                    pass
                cls._key_sources.append(f"env:{env_name}")
                logger.info(f"✅ Found API key in {env_name}")
                cls.save_backup()
                return True
        
        # Method 3: AWS Secrets Manager
        if HAS_BOTO3:
            try:
                secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
                secret_names = [
                    "ava-olo/openai-api-key",
                    "openai-api-key",
                    "ava-olo-secrets"
                ]
                
                for secret_name in secret_names:
                    try:
                        response = secrets_client.get_secret_value(SecretId=secret_name)
                        secret_data = response.get('SecretString', '{}')
                    
                        # Handle both string and JSON secrets
                        if secret_data.startswith('sk-'):
                            key = secret_data
                        else:
                            secret = json.loads(secret_data)
                            # Check various keys in the secret
                            for key_name in ["OPENAI_API_KEY", "openai_api_key", "api_key"]:
                                if key_name in secret:
                                    key = secret[key_name]
                                    break
                            else:
                                continue
                        
                        if key and key.startswith("sk-"):
                            cls._cached_key = key
                            os.environ["OPENAI_API_KEY"] = key
                            try:
                                import openai
                                openai.api_key = key
                            except:
                                pass
                            cls._key_sources.append(f"secrets:{secret_name}")
                            logger.info(f"✅ Found API key in AWS Secrets Manager: {secret_name}")
                            cls.save_backup()
                            return True
                    except Exception as e:
                        logger.debug(f"Secrets Manager {secret_name} failed: {e}")
                        continue
            except Exception as e:
                logger.debug(f"AWS Secrets Manager not available: {e}")
                pass
        
        # Method 4: Check database configuration
        try:
            from modules.core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            async with db_manager.get_connection_async() as conn:
                # First ensure table exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        key VARCHAR(255) PRIMARY KEY,
                        value TEXT,
                        encrypted BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                config = await conn.fetchrow("""
                    SELECT value FROM system_config 
                    WHERE key = 'OPENAI_API_KEY' 
                    LIMIT 1
                """)
                
                if config and config['value'] and config['value'].startswith("sk-"):
                    cls._cached_key = config['value']
                    os.environ["OPENAI_API_KEY"] = config['value']
                    try:
                        import openai
                        openai.api_key = config['value']
                    except:
                        pass
                    cls._key_sources.append("database")
                    logger.info("✅ Found API key in database")
                    cls.save_backup()
                    return True
        except Exception as e:
            logger.debug(f"Database lookup failed: {e}")
            pass
        
        # Method 5: Check mounted files
        file_locations = [
            "/secrets/openai_key",
            "/app/secrets/openai_key",
            "/etc/secrets/openai_key",
            ".openai_key",
            ".env.production"
        ]
        
        for file_path in file_locations:
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    
                    # Handle .env files
                    if file_path.endswith('.env') or file_path.endswith('.env.production'):
                        for line in content.split('\n'):
                            if line.startswith('OPENAI_API_KEY='):
                                key = line.split('=', 1)[1].strip()
                                break
                        else:
                            continue
                    else:
                        key = content
                    
                    if key and key.startswith("sk-"):
                        cls._cached_key = key
                        os.environ["OPENAI_API_KEY"] = key
                        try:
                            import openai
                            openai.api_key = key
                        except:
                            pass
                        cls._key_sources.append(f"file:{file_path}")
                        logger.info(f"✅ Found API key in file: {file_path}")
                        cls.save_backup()
                        return True
            except Exception as e:
                logger.debug(f"File {file_path} not accessible: {e}")
                continue
        
        # Method 6: Try to recover from previous deployment
        try:
            # Check if there's a backup in temp
            backup_path = "/tmp/.openai_key_backup"
            with open(backup_path, 'r') as f:
                key = f.read().strip()
                if key and key.startswith("sk-"):
                    cls._cached_key = key
                    os.environ["OPENAI_API_KEY"] = key
                    try:
                        import openai
                        openai.api_key = key
                    except:
                        pass
                    cls._key_sources.append("backup")
                    logger.info("✅ Recovered API key from backup")
                    return True
        except Exception as e:
            logger.debug(f"Backup recovery failed: {e}")
            pass
        
        # Method 7: Check ECS task definition (if running in ECS)
        try:
            if os.getenv('ECS_CONTAINER_METADATA_URI_V4'):
                import requests
                metadata_uri = os.getenv('ECS_CONTAINER_METADATA_URI_V4')
                task_metadata = requests.get(f"{metadata_uri}/task").json()
                
                # This would need proper ECS API access
                logger.debug("ECS metadata available but task definition lookup not implemented")
        except:
            pass
        
        logger.error("❌ No API key found in any location")
        logger.info(f"Searched locations: {cls._key_sources}")
        return False
    
    @classmethod
    def save_backup(cls):
        """Save API key backup for recovery"""
        if cls._cached_key:
            try:
                # Save to multiple backup locations
                backup_locations = [
                    "/tmp/.openai_key_backup",
                    "/var/cache/.openai_key_backup"
                ]
                
                for backup_path in backup_locations:
                    try:
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        with open(backup_path, 'w') as f:
                            f.write(cls._cached_key)
                        logger.info(f"Saved API key backup to {backup_path}")
                    except:
                        continue
                        
                # Also try to save to database
                try:
                    from modules.core.database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    
                    async def save_to_db():
                        async with db_manager.get_connection_async() as conn:
                            await conn.execute("""
                                INSERT INTO system_config (key, value, updated_at)
                                VALUES ('OPENAI_API_KEY', $1, NOW())
                                ON CONFLICT (key) DO UPDATE 
                                SET value = $1, updated_at = NOW()
                            """, cls._cached_key)
                    
                    asyncio.create_task(save_to_db())
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Failed to save backup: {e}")
    
    @classmethod
    def get_diagnostic_info(cls) -> Dict:
        """Get detailed diagnostic information"""
        return {
            "has_cached_key": bool(cls._cached_key),
            "cached_key_preview": f"{cls._cached_key[:10]}..." if cls._cached_key else None,
            "key_sources_tried": cls._key_sources,
            "environment_check": {
                name: bool(os.getenv(name))
                for name in ["OPENAI_API_KEY", "OPENAI_KEY", "openai_api_key"]
            },
            "last_check": cls._last_check.isoformat() if cls._last_check else None,
            "backup_exists": os.path.exists("/tmp/.openai_key_backup")
        }
    
    @classmethod
    async def test_api_key(cls, key: str) -> bool:
        """Test if an API key works"""
        try:
            import openai
            
            # Temporarily set the key
            old_key = openai.api_key
            openai.api_key = key
            
            # Try a simple completion
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            # Restore old key
            openai.api_key = old_key
            
            return True
        except:
            return False