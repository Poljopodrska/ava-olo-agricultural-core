"""
Emergency Fix Routes for System Recovery
"""
from fastapi import APIRouter
from modules.core.api_key_manager import APIKeyManager
from modules.core.startup_validator import StartupValidator
from modules.core.database_manager import DatabaseManager
from modules.cava.conversation_memory import CAVAMemory
import boto3
import os
import json
from datetime import datetime

router = APIRouter(prefix="/api/v1/emergency", tags=["emergency"])

@router.post("/fix-all")
async def emergency_fix_all():
    """Emergency fix for all known issues"""
    
    fixes_applied = []
    errors = []
    
    # Fix 1: API Key Recovery
    try:
        if not await APIKeyManager.ensure_api_key():
            # Try ECS metadata recovery
            try:
                if os.getenv('ECS_CONTAINER_METADATA_URI_V4'):
                    # This is running in ECS
                    ecs_client = boto3.client('ecs', region_name='us-east-1')
                    
                    # Get task ARN from metadata
                    import requests
                    metadata_uri = os.getenv('ECS_CONTAINER_METADATA_URI_V4')
                    task_metadata = requests.get(f"{metadata_uri}/task").json()
                    task_arn = task_metadata.get('TaskARN', '')
                    
                    if task_arn:
                        # Get task details
                        response = ecs_client.describe_tasks(
                            cluster='ava-olo-production',
                            tasks=[task_arn]
                        )
                        
                        if response['tasks']:
                            task_def_arn = response['tasks'][0]['taskDefinitionArn']
                            
                            # Get task definition
                            task_def = ecs_client.describe_task_definition(
                                taskDefinition=task_def_arn
                            )
                            
                            # Look for API key in environment
                            for container in task_def['taskDefinition']['containerDefinitions']:
                                if container['name'] == 'agricultural':
                                    for env in container.get('environment', []):
                                        if env['name'] == 'OPENAI_API_KEY' and env['value'].startswith('sk-'):
                                            os.environ['OPENAI_API_KEY'] = env['value']
                                            APIKeyManager._cached_key = env['value']
                                            APIKeyManager.save_backup()
                                            fixes_applied.append("recovered_openai_key_from_ecs")
                                            break
            except Exception as e:
                errors.append(f"ECS recovery failed: {str(e)}")
            
            # Try loading from .env.production backup
            if not os.getenv('OPENAI_API_KEY'):
                try:
                    with open('.env.production', 'r') as f:
                        for line in f:
                            if line.startswith('OPENAI_API_KEY='):
                                known_key = line.strip().split('=', 1)[1]
                                break
                        else:
                            known_key = None
                except:
                    known_key = None
                if known_key and await APIKeyManager.test_api_key(known_key):
                    os.environ['OPENAI_API_KEY'] = known_key
                    APIKeyManager._cached_key = known_key
                    APIKeyManager.save_backup()
                    fixes_applied.append("recovered_from_env_production")
        else:
            fixes_applied.append("api_key_already_available")
            
    except Exception as e:
        errors.append(f"API key recovery error: {str(e)}")
    
    # Fix 2: Re-initialize OpenAI Config
    try:
        from modules.core.openai_config import OpenAIConfig
        if OpenAIConfig.initialize(force=True):
            fixes_applied.append("reinitialized_openai_config")
        else:
            errors.append("OpenAI config initialization failed")
    except Exception as e:
        errors.append(f"OpenAI config error: {str(e)}")
    
    # Fix 3: Re-initialize CAVA Memory
    try:
        # Force new instance
        global cava_memory
        from modules.api import chat_routes
        chat_routes.cava_memory = CAVAMemory()
        fixes_applied.append("reinitialized_cava_memory")
    except Exception as e:
        errors.append(f"CAVA memory error: {str(e)}")
    
    # Fix 4: Clear corrupted cache
    try:
        db_manager = DatabaseManager()
        async with db_manager.get_connection_async() as conn:
            # Create system_cache table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_cache (
                    key VARCHAR(255) PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clear OpenAI related cache
            await conn.execute("DELETE FROM system_cache WHERE key LIKE 'openai_%'")
            fixes_applied.append("cleared_system_cache")
            
    except Exception as e:
        errors.append(f"Cache clearing error: {str(e)}")
    
    # Fix 5: Save current configuration to database
    try:
        if os.getenv('OPENAI_API_KEY'):
            db_manager = DatabaseManager()
            async with db_manager.get_connection_async() as conn:
                # Ensure system_config table exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        key VARCHAR(255) PRIMARY KEY,
                        value TEXT,
                        encrypted BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Save API key
                await conn.execute("""
                    INSERT INTO system_config (key, value, updated_at)
                    VALUES ('OPENAI_API_KEY', $1, NOW())
                    ON CONFLICT (key) DO UPDATE 
                    SET value = $1, updated_at = NOW()
                """, os.getenv('OPENAI_API_KEY'))
                
                fixes_applied.append("saved_config_to_database")
        
    except Exception as e:
        errors.append(f"Config save error: {str(e)}")
    
    # Re-validate system
    validation = await StartupValidator.validate_and_fix()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "fixes_applied": fixes_applied,
        "errors": errors,
        "system_status": validation,
        "api_key_recovered": bool(os.getenv('OPENAI_API_KEY')),
        "recommendation": "System should be operational" if validation["system_ready"] else "Restart service if issues persist"
    }

@router.get("/api-key-status")
async def check_api_key_status():
    """Quick check of API key status"""
    
    api_key_info = APIKeyManager.get_diagnostic_info()
    
    return {
        "has_key": bool(os.getenv('OPENAI_API_KEY')),
        "key_preview": os.getenv('OPENAI_API_KEY', '')[:10] + '...' if os.getenv('OPENAI_API_KEY') else None,
        "sources_checked": api_key_info.get('key_sources_tried', []),
        "cached_key": api_key_info.get('has_cached_key', False),
        "environment_vars": api_key_info.get('environment_check', {})
    }

@router.post("/force-key-recovery")
async def force_key_recovery():
    """Force API key recovery from all sources"""
    
    # Clear cache to force fresh search
    APIKeyManager._cached_key = None
    
    # Try recovery
    success = await APIKeyManager.ensure_api_key()
    
    if success:
        # Save backup
        APIKeyManager.save_backup()
        
        # Re-initialize OpenAI
        from modules.core.openai_config import OpenAIConfig
        OpenAIConfig.initialize(force=True)
    
    return {
        "success": success,
        "api_key_info": APIKeyManager.get_diagnostic_info(),
        "key_found": bool(os.getenv('OPENAI_API_KEY'))
    }