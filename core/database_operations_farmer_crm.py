"""
Database Operations - Farmer CRM database connection
Connects to existing Windows PostgreSQL with real farmer data
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL, DB_POOL_SETTINGS

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Database operations for existing farmer_crm database
    Connects to Windows PostgreSQL with real agricultural data
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or DATABASE_URL
        # Ensure PostgreSQL only
        assert self.connection_string.startswith("postgresql://"), "❌ Only PostgreSQL connections allowed"
        
        # For WSL2 to Windows connection, we might need to adjust the connection
        if "host.docker.internal" in self.connection_string:
            # This is correct for WSL2 to Windows connection
            pass
        
        self.engine = create_engine(
            self.connection_string,
            **DB_POOL_SETTINGS
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def get_farmer_info(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """Get farmer information by ID"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT id, farm_name, manager_name, manager_last_name, 
                           total_hectares, farmer_type, city, wa_phone_number
                    FROM farmers 
                    WHERE id = :farmer_id
                    """),
                    {"farmer_id": farmer_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "farm_name": result[1],
                        "manager_name": result[2],
                        "manager_last_name": result[3],
                        "total_hectares": float(result[4]) if result[4] else 0,
                        "farmer_type": result[5],
                        "city": result[6],
                        "wa_phone_number": result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting farmer info: {str(e)}")
            return None
    
    async def get_all_farmers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of all farmers for UI selection"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT id, farm_name, manager_name, manager_last_name, 
                           email, phone_number, farm_location, farmer_type, total_hectares
                    FROM farmers 
                    ORDER BY farm_name
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()
                
                farmers = []
                for row in results:
                    farmers.append({
                        "id": row[0],
                        "name": f"{row[2]} {row[3]}".strip() if row[2] and row[3] else "Unknown",
                        "farm_name": row[1] or "Unknown Farm",
                        "phone": row[5] or "",
                        "location": row[6] or "",
                        "farm_type": row[7] or "",
                        "total_size_ha": float(row[8]) if row[8] else 0.0
                    })
                
                return farmers
                
        except Exception as e:
            logger.error(f"Error getting all farmers: {str(e)}")
            return []
    
    async def get_farmer_fields(self, farmer_id: int) -> List[Dict[str, Any]]:
        """Get all fields for a farmer"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT f.field_id, f.field_name, f.field_size, f.field_location,
                           f.soil_type, 
                           fc.crop_name, fc.variety, fc.planting_date, fc.status
                    FROM fields f
                    LEFT JOIN field_crops fc ON f.field_id = fc.field_id 
                        AND fc.status = 'active'
                    WHERE f.farmer_id = :farmer_id
                    ORDER BY f.field_name
                    """),
                    {"farmer_id": farmer_id}
                ).fetchall()
                
                fields = []
                for row in results:
                    fields.append({
                        "field_id": row[0],
                        "field_name": row[1],
                        "field_size": float(row[2]) if row[2] else 0,
                        "field_location": row[3],
                        "soil_type": row[4],
                        "current_crop": row[5],
                        "variety": row[6],
                        "planting_date": row[7].isoformat() if row[7] else None,
                        "crop_status": row[8]
                    })
                
                return fields
                
        except Exception as e:
            logger.error(f"Error getting farmer fields: {str(e)}")
            return []
    
    async def get_recent_conversations(self, farmer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for context from incoming_messages table"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT message_id, message_body, ai_response, received_at, 
                           message_type, confidence_score, approved_status
                    FROM incoming_messages
                    WHERE farmer_id = :farmer_id
                    ORDER BY received_at DESC
                    LIMIT :limit
                    """),
                    {"farmer_id": farmer_id, "limit": limit}
                ).fetchall()
                
                conversations = []
                for row in results:
                    conversations.append({
                        "id": row[0],
                        "user_input": row[1],
                        "ava_response": row[2],
                        "timestamp": row[3],
                        "message_type": row[4],
                        "confidence_score": float(row[5]) if row[5] else None,
                        "approved_status": row[6] if row[6] is not None else False
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def save_conversation(self, farmer_id: int, conversation_data: Dict[str, Any]) -> Optional[int]:
        """Save a conversation to incoming_messages table"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    INSERT INTO incoming_messages (farmer_id, wa_phone_number, message_body, 
                                                 ai_response, language, message_type, confidence_score)
                    VALUES (:farmer_id, :wa_phone_number, :message_body, :ai_response, 
                           :language, :message_type, :confidence_score)
                    RETURNING message_id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "wa_phone_number": conversation_data.get("wa_phone_number"),
                        "message_body": conversation_data.get("question"),
                        "ai_response": conversation_data.get("answer"),
                        "language": conversation_data.get("language", "hr"),
                        "message_type": conversation_data.get("topic", "general"),
                        "confidence_score": conversation_data.get("confidence_score")
                    }
                )
                session.commit()
                conv_id = result.scalar()
                
                logger.info(f"Saved conversation {conv_id}")
                return conv_id
                
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return None
    
    async def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get crop information from crops_catalog"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT crop_id, name_english, name_croatian, category, 
                           planting_season, harvest_season, description
                    FROM crops_catalog
                    WHERE LOWER(name_english) = LOWER(:crop_name) 
                       OR LOWER(name_croatian) = LOWER(:crop_name)
                    """),
                    {"crop_name": crop_name}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "crop_name": result[1],
                        "croatian_name": result[2],
                        "category": result[3],
                        "planting_season": result[4],
                        "harvest_season": result[5],
                        "description": result[6]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting crop info: {str(e)}")
            return None
    
    async def get_conversations_for_approval(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get conversations grouped by approval status for agronomic dashboard"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT m.message_id, m.farmer_id, m.message_body as user_input, 
                           m.ai_response as ava_response, m.received_at as timestamp, 
                           m.approved_status,
                           f.manager_name, f.manager_last_name, f.phone_number, 
                           f.farm_location, f.farmer_type, f.total_hectares
                    FROM incoming_messages m
                    JOIN farmers f ON m.farmer_id = f.id
                    WHERE m.ai_response IS NOT NULL
                    ORDER BY m.approved_status ASC, m.received_at DESC
                    LIMIT 100
                    """)
                ).fetchall()
                
                unapproved = []
                approved = []
                
                for row in results:
                    conv = {
                        "id": row[0],
                        "farmer_id": row[1],
                        "farmer_name": f"{row[6]} {row[7]}".strip() if row[6] and row[7] else "Unknown",
                        "farmer_phone": row[8] or "",
                        "farmer_location": row[9] or "",
                        "farmer_type": row[10] or "",
                        "farmer_size": f"{float(row[11]):.1f}" if row[11] else "0.0",
                        "last_message": row[2][:100] + "..." if row[2] and len(row[2]) > 100 else row[2] or "",
                        "timestamp": row[4]
                    }
                    
                    if row[5]:  # approved_status
                        approved.append(conv)
                    else:
                        unapproved.append(conv)
                
                return {"unapproved": unapproved, "approved": approved}
                
        except Exception as e:
            logger.error(f"Error getting conversations for approval: {str(e)}")
            return {"unapproved": [], "approved": []}
    
    async def get_conversation_details(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed conversation information"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT m.message_id, m.farmer_id, m.message_body as user_input, 
                           m.ai_response as ava_response, m.received_at as timestamp, 
                           m.approved_status,
                           f.manager_name, f.manager_last_name, f.phone_number, 
                           f.farm_location, f.farmer_type, f.total_hectares
                    FROM incoming_messages m
                    JOIN farmers f ON m.farmer_id = f.id
                    WHERE m.message_id = :conversation_id
                    """),
                    {"conversation_id": conversation_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "farmer_id": result[1],
                        "farmer_name": f"{result[6]} {result[7]}".strip() if result[6] and result[7] else "Unknown",
                        "user_input": result[2],
                        "ava_response": result[3],
                        "timestamp": result[4],
                        "approved_status": result[5] if result[5] is not None else False
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting conversation details: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """Check database connectivity to farmer_crm database"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM farmers"))
                count = result.scalar()
                logger.info(f"Database health check: Connected to farmer_crm with {count} farmers")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

    async def test_windows_postgresql(self) -> bool:
        """Test connection to Windows PostgreSQL"""
        try:
            with self.get_session() as session:
                # Test farmers table
                farmer_count = session.execute(text("SELECT COUNT(*) FROM farmers")).scalar()
                print(f"✅ Connected to farmer_crm! Found {farmer_count} farmers")
                
                # Show some sample data
                farmers = session.execute(text("SELECT farm_name, manager_name, farmer_type FROM farmers LIMIT 5")).fetchall()
                print("\n📋 Sample farmers:")
                for farm in farmers:
                    print(f"  - {farm[0]}: {farm[1]} ({farm[2]})")
                
                # Test other tables
                tables = ['fields', 'field_crops', 'incoming_messages', 'crops_catalog']
                print("\n📊 Table counts:")
                for table in tables:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"  - {table}: {count} records")
                
                return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False