#!/usr/bin/env python3
"""
CAVA Setup Routes - Create required tables
"""
from fastapi import APIRouter, HTTPException
import logging
from modules.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cava", tags=["cava-setup"])

@router.post("/setup-tables")
async def setup_cava_tables():
    """Create required CAVA tables if they don't exist"""
    try:
        db_manager = DatabaseManager()
        results = {
            "tables_created": [],
            "tables_existed": [],
            "errors": []
        }
        
        # Create chat_messages table
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if chat_messages exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'chat_messages'
                        )
                    """)
                    exists = cursor.fetchone()[0]
                    
                    if not exists:
                        cursor.execute("""
                            CREATE TABLE chat_messages (
                                id SERIAL PRIMARY KEY,
                                wa_phone_number VARCHAR(255) NOT NULL,
                                role VARCHAR(50) NOT NULL,
                                content TEXT NOT NULL,
                                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                            );
                            
                            CREATE INDEX idx_chat_messages_phone ON chat_messages(wa_phone_number);
                            CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
                            CREATE INDEX idx_chat_messages_role ON chat_messages(role);
                        """)
                        conn.commit()
                        results["tables_created"].append("chat_messages")
                        logger.info("Created chat_messages table")
                    else:
                        results["tables_existed"].append("chat_messages")
                        
                        # Check columns
                        cursor.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'chat_messages'
                        """)
                        columns = [row[0] for row in cursor.fetchall()]
                        
                        # Fix column names if needed
                        if 'role' not in columns and 'direction' in columns:
                            cursor.execute("ALTER TABLE chat_messages RENAME COLUMN direction TO role;")
                            conn.commit()
                            logger.info("Renamed direction to role")
                        
                        if 'content' not in columns and 'message_content' in columns:
                            cursor.execute("ALTER TABLE chat_messages RENAME COLUMN message_content TO content;")
                            conn.commit()
                            logger.info("Renamed message_content to content")
                        
                        if 'timestamp' not in columns and 'created_at' in columns:
                            cursor.execute("ALTER TABLE chat_messages RENAME COLUMN created_at TO timestamp;")
                            conn.commit()
                            logger.info("Renamed created_at to timestamp")
                            
        except Exception as e:
            results["errors"].append(f"chat_messages: {str(e)}")
            logger.error(f"Error with chat_messages: {e}")
        
        # Create llm_usage_log table
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if llm_usage_log exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'llm_usage_log'
                        )
                    """)
                    exists = cursor.fetchone()[0]
                    
                    if not exists:
                        cursor.execute("""
                            CREATE TABLE llm_usage_log (
                                id SERIAL PRIMARY KEY,
                                farmer_phone VARCHAR(20),
                                model VARCHAR(50),
                                tokens_in INTEGER,
                                tokens_out INTEGER,
                                cost DECIMAL(10,6),
                                timestamp TIMESTAMP DEFAULT NOW()
                            );
                            
                            CREATE INDEX idx_llm_usage_phone ON llm_usage_log(farmer_phone);
                            CREATE INDEX idx_llm_usage_timestamp ON llm_usage_log(timestamp);
                        """)
                        conn.commit()
                        results["tables_created"].append("llm_usage_log")
                        logger.info("Created llm_usage_log table")
                    else:
                        results["tables_existed"].append("llm_usage_log")
                        
        except Exception as e:
            results["errors"].append(f"llm_usage_log: {str(e)}")
            logger.error(f"Error with llm_usage_log: {e}")
        
        # Get table statistics
        stats = {}
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for table in ['chat_messages', 'llm_usage_log']:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            stats[table] = count
                        except:
                            stats[table] = "error"
        except:
            pass
        
        results["table_stats"] = stats
        results["success"] = len(results["errors"]) == 0
        
        return results
        
    except Exception as e:
        logger.error(f"Setup tables error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/table-status")
async def check_table_status():
    """Check status of CAVA tables"""
    try:
        db_manager = DatabaseManager()
        status = {
            "tables": {},
            "total_tables": 0
        }
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get all tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                all_tables = [row[0] for row in cursor.fetchall()]
                status["total_tables"] = len(all_tables)
                
                # Check CAVA tables specifically
                cava_tables = ['chat_messages', 'llm_usage_log']
                
                for table in cava_tables:
                    if table in all_tables:
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        # Get columns
                        cursor.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, (table,))
                        columns = {row[0]: row[1] for row in cursor.fetchall()}
                        
                        status["tables"][table] = {
                            "exists": True,
                            "row_count": count,
                            "columns": columns
                        }
                    else:
                        status["tables"][table] = {
                            "exists": False,
                            "row_count": 0,
                            "columns": {}
                        }
        
        return status
        
    except Exception as e:
        logger.error(f"Table status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))