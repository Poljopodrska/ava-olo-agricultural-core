"""
Startup Validator with Auto-Recovery Mechanisms
"""
from modules.core.api_key_manager import APIKeyManager
from modules.cava.conversation_memory import CAVAMemory
from modules.core.database_manager import DatabaseManager
from datetime import datetime
from typing import Dict
import openai
import asyncio
import json
import os
import logging

logger = logging.getLogger(__name__)

class StartupValidator:
    """Validates and fixes system state on startup"""
    
    @staticmethod
    async def validate_and_fix() -> Dict:
        """Comprehensive validation and auto-fix"""
        
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "fixes_applied": [],
            "system_ready": False
        }
        
        # Check 1: OpenAI API Key
        print("🔍 Validating OpenAI API key...")
        api_key_status = await APIKeyManager.ensure_api_key()
        validation_report["checks"]["openai_api_key"] = api_key_status
        
        if not api_key_status:
            print("⚠️ OpenAI API key not found - attempting emergency recovery...")
            
            # Try known working key from .env.production (loaded dynamically)
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
                os.environ["OPENAI_API_KEY"] = known_key
                openai.api_key = known_key
                APIKeyManager._cached_key = known_key
                APIKeyManager.save_backup()
                validation_report["fixes_applied"].append("emergency_key_recovery")
                api_key_status = True
                print("✅ Emergency key recovery successful")
        
        # Check 2: Test OpenAI Connection
        if api_key_status:
            try:
                # Get OpenAI client
                from modules.core.openai_config import OpenAIConfig
                client = OpenAIConfig.get_client()
                
                if client:
                    test_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    validation_report["checks"]["openai_connection"] = True
                    print("✅ OpenAI connection verified")
                else:
                    validation_report["checks"]["openai_connection"] = False
                    print("❌ OpenAI client initialization failed")
                    
            except Exception as e:
                validation_report["checks"]["openai_connection"] = False
                validation_report["checks"]["openai_error"] = str(e)
                print(f"❌ OpenAI connection failed: {e}")
        
        # Check 3: Database Connection
        try:
            db_manager = DatabaseManager()
            
            # Test with async connection
            async with db_manager.get_connection_async() as conn:
                await conn.fetchval("SELECT 1")
                validation_report["checks"]["database"] = True
                print("✅ Database connection verified")
                
        except Exception as e:
            validation_report["checks"]["database"] = False
            validation_report["checks"]["database_error"] = str(e)
            print(f"❌ Database connection failed: {e}")
        
        # Check 4: CAVA Tables
        try:
            async with db_manager.get_connection_async() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('chat_messages', 'farmer_facts', 'llm_usage_log')
                """)
                
                table_names = [t['table_name'] for t in tables]
                validation_report["checks"]["cava_tables"] = len(table_names) == 3
                
                if len(table_names) < 3:
                    # Create missing tables
                    await StartupValidator.create_cava_tables(conn)
                    validation_report["fixes_applied"].append("created_missing_tables")
                    print("✅ Created missing CAVA tables")
                else:
                    print("✅ CAVA tables verified")
                    
        except Exception as e:
            validation_report["checks"]["cava_tables"] = False
            print(f"❌ CAVA tables check failed: {e}")
        
        # Check 5: CAVA Memory System
        try:
            cava = CAVAMemory()
            test_context = await cava.get_conversation_context("+385STARTUP_TEST")
            validation_report["checks"]["cava_memory"] = True
            print("✅ CAVA memory system verified")
        except Exception as e:
            validation_report["checks"]["cava_memory"] = False
            validation_report["checks"]["cava_error"] = str(e)
            print(f"❌ CAVA memory system failed: {e}")
        
        # Check 6: Memory Enforcer
        try:
            from modules.cava.memory_enforcer import MemoryEnforcer
            enforcer = MemoryEnforcer()
            test_facts = enforcer.extract_critical_facts({})
            validation_report["checks"]["memory_enforcer"] = True
            print("✅ Memory enforcer verified")
        except Exception as e:
            validation_report["checks"]["memory_enforcer"] = False
            print(f"❌ Memory enforcer failed: {e}")
        
        # Determine overall status
        critical_checks = [
            validation_report["checks"].get("openai_api_key", False),
            validation_report["checks"].get("openai_connection", False),
            validation_report["checks"].get("database", False),
            validation_report["checks"].get("cava_tables", False)
        ]
        
        validation_report["system_ready"] = all(critical_checks)
        
        # Save validation report
        try:
            async with db_manager.get_connection_async() as conn:
                # Ensure health log table exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_health_log (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        validation_report JSONB,
                        system_ready BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    INSERT INTO system_health_log (timestamp, validation_report, system_ready)
                    VALUES ($1, $2, $3)
                """, datetime.now(), json.dumps(validation_report), validation_report["system_ready"])
                
        except Exception as e:
            logger.error(f"Failed to save health log: {e}")
        
        return validation_report
    
    @staticmethod
    async def create_cava_tables(conn):
        """Create missing CAVA tables"""
        
        # Create chat_messages table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                wa_phone_number VARCHAR(20) NOT NULL,
                role VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create farmer_facts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS farmer_facts (
                id SERIAL PRIMARY KEY,
                wa_phone_number VARCHAR(20) NOT NULL,
                fact_type VARCHAR(50),
                fact_value TEXT,
                confidence FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create llm_usage_log table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage_log (
                id SERIAL PRIMARY KEY,
                farmer_phone VARCHAR(20),
                model VARCHAR(50),
                tokens_in INTEGER,
                tokens_out INTEGER,
                cost DECIMAL(10,6),
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_phone ON chat_messages(wa_phone_number)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_farmer_facts_phone ON farmer_facts(wa_phone_number)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_usage_phone ON llm_usage_log(farmer_phone)")
    
    @staticmethod
    async def continuous_health_check():
        """Run health checks every 5 minutes"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            
            try:
                # Quick health check
                if not os.getenv("OPENAI_API_KEY"):
                    print("⚠️ API key lost - attempting recovery...")
                    await APIKeyManager.ensure_api_key()
                
                # Test chat functionality
                from modules.api.chat_routes import chat_endpoint, ChatRequest
                test_request = ChatRequest(
                    wa_phone_number="+385HEALTH_CHECK",
                    message="System health check"
                )
                
                try:
                    response = await chat_endpoint(test_request)
                    
                    if response.model_used == "unavailable":
                        print("⚠️ Chat unavailable - attempting recovery...")
                        await StartupValidator.validate_and_fix()
                except:
                    # If chat fails, try to fix
                    await StartupValidator.validate_and_fix()
                    
            except Exception as e:
                logger.error(f"Health check error: {e}")
                # Try to recover anyway
                try:
                    await StartupValidator.validate_and_fix()
                except:
                    pass