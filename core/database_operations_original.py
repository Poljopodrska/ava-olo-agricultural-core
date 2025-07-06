"""
Database Operations - Farmer data management for AVA OLO
Handles all database operations with proper error isolation
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
    Isolated database operations module - PostgreSQL ONLY
    All farmer data operations with proper error handling
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or DATABASE_URL
        # Ensure PostgreSQL only
        assert self.connection_string.startswith("postgresql://"), "❌ Only PostgreSQL connections allowed"
        
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
                    FROM ava_farmers 
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
                           email, phone_number, farm_location, farm_type, total_size_ha
                    FROM ava_farmers 
                    ORDER BY farm_name
                    LIMIT :limit
                    """),
                    {"limit": limit}
                )
                
                farmers = []
                for row in results:
                    farmers.append({
                        "id": row.id,
                        "name": f"{row.manager_name} {row.manager_last_name}".strip(),
                        "farm_name": row.farm_name,
                        "phone": row.phone_number,
                        "location": row.farm_location,
                        "farm_type": row.farm_type,
                        "total_size_ha": float(row.total_size_ha) if row.total_size_ha else 0.0
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
                    FROM ava_fields f
                    LEFT JOIN ava_field_crops fc ON f.field_id = fc.field_id 
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
    
    async def create_field(self, farmer_id: int, field_data: Dict[str, Any]) -> Optional[int]:
        """Create a new field for farmer"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    INSERT INTO ava_fields (farmer_id, field_name, field_size, 
                                          field_location, soil_type)
                    VALUES (:farmer_id, :field_name, :field_size, :field_location, :soil_type)
                    RETURNING field_id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "field_name": field_data.get("field_name"),
                        "field_size": field_data.get("field_size"),
                        "field_location": field_data.get("field_location"),
                        "soil_type": field_data.get("soil_type")
                    }
                )
                session.commit()
                field_id = result.scalar()
                
                logger.info(f"Created field {field_id} for farmer {farmer_id}")
                return field_id
                
        except Exception as e:
            logger.error(f"Error creating field: {str(e)}")
            return None
    
    async def add_crop_to_field(self, field_id: int, crop_data: Dict[str, Any]) -> bool:
        """Add crop to field"""
        try:
            with self.get_session() as session:
                # First mark any existing active crops as harvested
                session.execute(
                    text("""
                    UPDATE ava_field_crops 
                    SET status = 'harvested', actual_harvest_date = CURRENT_DATE
                    WHERE field_id = :field_id AND status = 'active'
                    """),
                    {"field_id": field_id}
                )
                
                # Add new crop
                session.execute(
                    text("""
                    INSERT INTO ava_field_crops (field_id, crop_name, variety, 
                                               planting_date, expected_harvest_date)
                    VALUES (:field_id, :crop_name, :variety, :planting_date, 
                           :expected_harvest_date)
                    """),
                    {
                        "field_id": field_id,
                        "crop_name": crop_data.get("crop_name"),
                        "variety": crop_data.get("variety"),
                        "planting_date": crop_data.get("planting_date"),
                        "expected_harvest_date": crop_data.get("expected_harvest_date")
                    }
                )
                session.commit()
                
                logger.info(f"Added crop to field {field_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding crop to field: {str(e)}")
            return False
    
    async def log_farm_task(self, farmer_id: int, task_data: Dict[str, Any]) -> Optional[int]:
        """Log a farm task/operation"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    INSERT INTO farm_tasks (farmer_id, field_id, task_type, 
                                          task_description, task_date, status)
                    VALUES (:farmer_id, :field_id, :task_type, :task_description, 
                           :task_date, :status)
                    RETURNING id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "field_id": task_data.get("field_id"),
                        "task_type": task_data.get("task_type"),
                        "task_description": task_data.get("task_description"),
                        "task_date": task_data.get("task_date", date.today()),
                        "status": task_data.get("status", "completed")
                    }
                )
                session.commit()
                task_id = result.scalar()
                
                logger.info(f"Logged task {task_id} for farmer {farmer_id}")
                return task_id
                
        except Exception as e:
            logger.error(f"Error logging farm task: {str(e)}")
            return None
    
    async def get_recent_conversations(self, farmer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for context"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT id, question, answer, created_at, topic, confidence_score
                    FROM ava_conversations
                    WHERE farmer_id = :farmer_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {"farmer_id": farmer_id, "limit": limit}
                ).fetchall()
                
                conversations = []
                for row in results:
                    conversations.append({
                        "id": row[0],
                        "question": row[1],
                        "answer": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "topic": row[4],
                        "confidence_score": float(row[5]) if row[5] else None
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def save_conversation(self, farmer_id: int, conversation_data: Dict[str, Any]) -> Optional[int]:
        """Save a conversation"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    INSERT INTO ava_conversations (farmer_id, wa_phone_number, question, 
                                                 answer, language, topic, confidence_score)
                    VALUES (:farmer_id, :wa_phone_number, :question, :answer, 
                           :language, :topic, :confidence_score)
                    RETURNING id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "wa_phone_number": conversation_data.get("wa_phone_number"),
                        "question": conversation_data.get("question"),
                        "answer": conversation_data.get("answer"),
                        "language": conversation_data.get("language", "hr"),
                        "topic": conversation_data.get("topic"),
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
        """Get crop information from catalog"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT id, crop_name, crop_type, typical_cycle_days, 
                           croatian_name, description
                    FROM ava_crops
                    WHERE LOWER(crop_name) = LOWER(:crop_name) 
                       OR LOWER(croatian_name) = LOWER(:crop_name)
                    """),
                    {"crop_name": crop_name}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "crop_name": result[1],
                        "crop_type": result[2],
                        "typical_cycle_days": result[3],
                        "croatian_name": result[4],
                        "description": result[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting crop info: {str(e)}")
            return None
    
    async def log_llm_operation(self, operation_data: Dict[str, Any]) -> None:
        """Log LLM operation for debugging"""
        try:
            with self.get_session() as session:
                session.execute(
                    text("""
                    INSERT INTO llm_debug_log (operation_type, input_text, output_text,
                                             model_used, tokens_used, latency_ms, 
                                             success, error_message)
                    VALUES (:operation_type, :input_text, :output_text, :model_used,
                           :tokens_used, :latency_ms, :success, :error_message)
                    """),
                    operation_data
                )
                session.commit()
                
        except Exception as e:
            logger.error(f"Error logging LLM operation: {str(e)}")
    
    async def get_conversations_for_approval(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get conversations grouped by approval status for agronomic dashboard"""
        try:
            with self.get_session() as session:
                results = session.execute(
                    text("""
                    SELECT c.id, c.farmer_id, c.question as user_input, c.answer as ava_response, 
                           c.created_at as timestamp, c.approved_status,
                           f.manager_name, f.manager_last_name, f.phone_number, 
                           f.farm_location, f.farm_type, f.total_size_ha
                    FROM ava_conversations c
                    JOIN ava_farmers f ON c.farmer_id = f.id
                    ORDER BY c.approved_status ASC, c.created_at DESC
                    LIMIT 100
                    """)
                ).fetchall()
                
                unapproved = []
                approved = []
                
                for row in results:
                    conv = {
                        "id": row.id,
                        "farmer_id": row.farmer_id,
                        "farmer_name": f"{row.manager_name} {row.manager_last_name}".strip(),
                        "farmer_phone": row.phone_number,
                        "farmer_location": row.farm_location,
                        "farmer_type": row.farm_type,
                        "farmer_size": f"{float(row.total_size_ha):.1f}" if row.total_size_ha else "0.0",
                        "last_message": row.user_input[:100] + "..." if len(row.user_input) > 100 else row.user_input,
                        "timestamp": row.timestamp
                    }
                    
                    if row.approved_status:
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
                    SELECT c.id, c.farmer_id, c.question as user_input, c.answer as ava_response, 
                           c.created_at as timestamp, c.approved_status,
                           f.manager_name, f.manager_last_name, f.phone_number, 
                           f.farm_location, f.farm_type, f.total_size_ha
                    FROM ava_conversations c
                    JOIN ava_farmers f ON c.farmer_id = f.id
                    WHERE c.id = :conversation_id
                    """),
                    {"conversation_id": conversation_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result.id,
                        "farmer_id": result.farmer_id,
                        "farmer_name": f"{result.manager_name} {result.manager_last_name}".strip(),
                        "user_input": result.user_input,
                        "ava_response": result.ava_response,
                        "timestamp": result.timestamp,
                        "approved_status": result.approved_status
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting conversation details: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False