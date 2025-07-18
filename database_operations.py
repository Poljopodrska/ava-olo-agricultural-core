"""
Database Operations - Farmer CRM database connection
Connects to existing Windows PostgreSQL with real farmer data
"""
import asyncio
import logging
import json
import traceback
import psycopg2
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
import sys
from contextlib import contextmanager

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import DATABASE_URL, DB_POOL_SETTINGS
except ImportError:
    DATABASE_URL = None
    DB_POOL_SETTINGS = {}

logger = logging.getLogger(__name__)

# Add the WORKING connection method from main.py
@contextmanager
def get_working_db_connection():
    """Use the EXACT same connection method as the working database dashboard"""
    connection = None
    
    try:
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME', 'farmer_crm')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        port = int(os.getenv('DB_PORT', '5432'))
        
        print(f"DEBUG: Attempting connection to {host}:{port}/{database} as {user}")
        
        # Strategy 1: Try with SSL required (AWS RDS default)
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='require'
                )
                print("DEBUG: Connected with SSL required")
            except psycopg2.OperationalError as ssl_error:
                print(f"DEBUG: SSL required failed: {ssl_error}")
        
        # Strategy 2: Try with SSL preferred
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='prefer'
                )
                print("DEBUG: Connected with SSL preferred")
            except psycopg2.OperationalError as ssl_pref_error:
                print(f"DEBUG: SSL preferred failed: {ssl_pref_error}")
        
        # Strategy 3: Try connecting to postgres database instead
        if not connection:
            try:
                connection = psycopg2.connect(
                    host=host,
                    database='postgres',  # Try postgres database
                    user=user,
                    password=password,
                    port=port,
                    connect_timeout=10,
                    sslmode='require'
                )
                print("DEBUG: Connected to postgres database instead")
            except psycopg2.OperationalError as postgres_error:
                print(f"DEBUG: Postgres database connection failed: {postgres_error}")
        
        if connection:
            yield connection
        else:
            yield None
            
    except Exception as e:
        print(f"DEBUG: Connection error: {e}")
        if connection:
            connection.close()
        raise
    finally:
        if connection and not connection.closed:
            connection.close()

class DatabaseOperations:
    """
    Database operations for existing farmer_crm database
    Connects to Windows PostgreSQL with real agricultural data
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or DATABASE_URL
        # Ensure PostgreSQL only
        assert self.connection_string.startswith("postgresql://"), "❌ Only PostgreSQL connections allowed"
        
        # Clean up connection string - remove any whitespace issues
        self.connection_string = self.connection_string.strip()
        
        # Fix hostname spaces in connection string
        if "@" in self.connection_string:
            parts = self.connection_string.split("@")
            if len(parts) == 2:
                before_host = parts[0]
                after_host = parts[1]
                # Remove spaces from hostname part
                host_and_rest = after_host.split(":")
                if len(host_and_rest) >= 2:
                    hostname = host_and_rest[0].replace(" ", "")
                    port_and_db = ":".join(host_and_rest[1:])
                    self.connection_string = f"{before_host}@{hostname}:{port_and_db}"
        
        print(f"DEBUG: Database connection string: {self.connection_string[:50]}...{self.connection_string[-20:]}")
        
        # Extract and validate connection components
        if "@" in self.connection_string:
            try:
                # Parse connection string
                parts = self.connection_string.replace("postgresql://", "").split("@")
                user_pass = parts[0]
                host_port_db = parts[1]
                
                user = user_pass.split(":")[0]
                host = host_port_db.split(":")[0]
                
                print(f"DEBUG: Connecting as user: '{user}'")
                print(f"DEBUG: Connecting to host: '{host}'")
                
                if " " in host:
                    print(f"WARNING: Still found spaces in hostname: '{host}'")
                elif not host.endswith(".amazonaws.com"):
                    print(f"WARNING: Unusual hostname format: '{host}'")
                    print(f"Expected AWS RDS hostname format: *.amazonaws.com")
                else:
                    print(f"INFO: Hostname format looks correct: '{host}'")
            except Exception as e:
                print(f"WARNING: Could not parse connection string: {e}")
        
        # For WSL2 to Windows connection, we might need to adjust the connection
        if "host.docker.internal" in self.connection_string:
            # This is correct for WSL2 to Windows connection
            pass
        
        # Add SSL requirement for AWS RDS
        engine_kwargs = DB_POOL_SETTINGS.copy()
        if ".amazonaws.com" in self.connection_string:
            engine_kwargs["connect_args"] = {
                "sslmode": "require",
                "connect_timeout": 30,
                "application_name": "ava-olo-monitoring-dashboard"
            }
            print("INFO: Added SSL requirement for AWS RDS connection")
            print("INFO: Using sslmode=require with 30s timeout for RDS connection")
        
        self.engine = create_engine(
            self.connection_string,
            **engine_kwargs
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
                           city, wa_phone_number
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
                        "total_hectares": 0,  # Default since column doesn't exist
                        "farmer_type": "Farm",  # Default since column doesn't exist
                        "city": result[4],
                        "wa_phone_number": result[5]
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
                           email, phone, city, wa_phone_number
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
                        "phone": row[5] or row[7] or "",
                        "location": row[6] or "",
                        "farm_type": "Farm",  # Default since column doesn't exist
                        "total_size_ha": 0.0  # Default since column doesn't exist
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
                    SELECT id, message_text, timestamp, role
                    FROM incoming_messages
                    WHERE farmer_id = :farmer_id
                    ORDER BY timestamp DESC
                    LIMIT :limit
                    """),
                    {"farmer_id": farmer_id, "limit": limit}
                ).fetchall()
                
                conversations = []
                for row in results:
                    conversations.append({
                        "id": row[0],
                        "user_input": row[1] if row[3] == 'user' else "",
                        "ava_response": row[1] if row[3] == 'assistant' else "",
                        "timestamp": row[2],
                        "message_type": "chat",
                        "confidence_score": 0.8,
                        "approved_status": False
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def save_conversation(self, farmer_id: int, conversation_data: Dict[str, Any]) -> Optional[int]:
        """Save a conversation to incoming_messages table"""
        try:
            with self.get_session() as session:
                # Save user message
                result1 = session.execute(
                    text("""
                    INSERT INTO incoming_messages (farmer_id, phone_number, message_text, role, timestamp)
                    VALUES (:farmer_id, :phone_number, :message_text, 'user', CURRENT_TIMESTAMP)
                    RETURNING id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "phone_number": conversation_data.get("wa_phone_number", "unknown"),
                        "message_text": conversation_data.get("question")
                    }
                )
                
                # Save assistant response
                result2 = session.execute(
                    text("""
                    INSERT INTO incoming_messages (farmer_id, phone_number, message_text, role, timestamp)
                    VALUES (:farmer_id, :phone_number, :message_text, 'assistant', CURRENT_TIMESTAMP)
                    RETURNING id
                    """),
                    {
                        "farmer_id": farmer_id,
                        "phone_number": conversation_data.get("wa_phone_number", "unknown"),
                        "message_text": conversation_data.get("answer")
                    }
                )
                session.commit()
                conv_id = result2.scalar()
                
                logger.info(f"Saved conversation pair")
                return conv_id
                
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return None
    
    async def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get crop information from crop_protection_croatia"""
        try:
            with self.get_session() as session:
                # First check if we have crop technology info
                result = session.execute(
                    text("""
                    SELECT DISTINCT crop_type
                    FROM crop_technology
                    WHERE LOWER(crop_type) = LOWER(:crop_name)
                    LIMIT 1
                    """),
                    {"crop_name": crop_name}
                ).fetchone()
                
                if result:
                    return {
                        "id": 1,
                        "crop_name": result[0],
                        "croatian_name": result[0],
                        "category": "Crop",
                        "planting_season": "Spring",
                        "harvest_season": "Fall",
                        "description": f"Information about {result[0]}"
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting crop info: {str(e)}")
            return None
    
    def get_conversations_for_approval(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get conversations grouped by approval status for agronomic dashboard"""
        try:
            with self.get_session() as session:
                # Get latest user messages for each farmer
                results = session.execute(
                    text("""
                    WITH latest_messages AS (
                        SELECT DISTINCT ON (farmer_id) 
                               m.id, m.farmer_id, m.message_text, m.timestamp,
                               f.manager_name, f.manager_last_name, f.phone, 
                               f.city, f.farm_name
                        FROM incoming_messages m
                        JOIN farmers f ON m.farmer_id = f.id
                        WHERE m.role = 'user'
                        ORDER BY farmer_id, m.timestamp DESC
                    )
                    SELECT * FROM latest_messages
                    ORDER BY timestamp DESC
                    LIMIT 100
                    """)
                ).fetchall()
                
                # For now, all conversations are unapproved since the table doesn't have approval status
                unapproved = []
                
                for row in results:
                    conv = {
                        "id": row[0],
                        "farmer_id": row[1],
                        "farmer_name": f"{row[4]} {row[5]}".strip() if row[4] and row[5] else "Unknown",
                        "farmer_phone": row[6] or "",
                        "farmer_location": row[7] or "",
                        "farmer_type": "Farm",
                        "farmer_size": "0.0",
                        "last_message": row[2][:100] + "..." if row[2] and len(row[2]) > 100 else row[2] or "",
                        "timestamp": row[3]
                    }
                    unapproved.append(conv)
                
                return {"unapproved": unapproved, "approved": []}
                
        except Exception as e:
            logger.error(f"Error getting conversations for approval: {str(e)}")
            return {"unapproved": [], "approved": []}
    
    async def get_conversation_details(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed conversation information"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT m.id, m.farmer_id, m.message_text, m.timestamp, m.role,
                           f.manager_name, f.manager_last_name, f.phone, 
                           f.city, f.farm_name
                    FROM incoming_messages m
                    JOIN farmers f ON m.farmer_id = f.id
                    WHERE m.id = :conversation_id
                    """),
                    {"conversation_id": conversation_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "farmer_id": result[1],
                        "farmer_name": f"{result[5]} {result[6]}".strip() if result[5] and result[6] else "Unknown",
                        "user_input": result[2] if result[4] == 'user' else "",
                        "ava_response": result[2] if result[4] == 'assistant' else "",
                        "timestamp": result[3],
                        "approved_status": False
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting conversation details: {str(e)}")
            return None

    def health_check(self) -> bool:
        """Check database connectivity to farmer_crm database"""
        try:
            print("INFO: Starting comprehensive database health check...")
            
            with self.get_session() as session:
                # Test basic connectivity
                print("INFO: Testing basic connectivity...")
                basic_result = session.execute(text("SELECT 1")).scalar()
                if basic_result != 1:
                    print("ERROR: Basic connectivity test failed")
                    return False
                print("✅ Basic connectivity: OK")
                
                # Test farmers table access
                print("INFO: Testing farmers table access...")
                result = session.execute(text("SELECT COUNT(*) FROM farmers"))
                count = result.scalar()
                print(f"✅ Farmers table access: OK ({count} farmers found)")
                
                # Test fields table access
                print("INFO: Testing fields table access...")
                fields_result = session.execute(text("SELECT COUNT(*) FROM fields"))
                fields_count = fields_result.scalar()
                print(f"✅ Fields table access: OK ({fields_count} fields found)")
                
                logger.info(f"Database health check: Connected to farmer_crm with {count} farmers and {fields_count} fields")
                print("✅ Database health check: PASSED")
                return True
                
        except Exception as e:
            print(f"❌ Database health check failed: {str(e)}")
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
                farmers = session.execute(text("SELECT farm_name, manager_name, city FROM farmers LIMIT 5")).fetchall()
                print("\n📋 Sample farmers:")
                for farm in farmers:
                    print(f"  - {farm[0]}: {farm[1]} ({farm[2]})")
                
                # Test other tables
                tables = ['fields', 'field_crops', 'incoming_messages', 'crop_protection_croatia']
                print("\n📊 Table counts:")
                for table in tables:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"  - {table}: {count} records")
                
                return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def insert_farmer_with_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new farmer with fields and app access credentials"""
        logger.info("=== INSERT_FARMER_WITH_FIELDS START ===")
        logger.info(f"🚀 DEPLOYMENT MARKER: 2025-07-18-15:01 - JSON import is at line 7")
        logger.info(f"Method type: {type(self.insert_farmer_with_fields)}")
        logger.info(f"Data received: {json.dumps(data, default=str)[:500]}...")
        
        try:
            logger.info(f"Step 1: Starting farmer registration for {data.get('manager_name')} {data.get('manager_last_name')}")
            
            # Use the WORKING connection method instead of SQLAlchemy
            logger.info("Step 2: Attempting database connection using get_working_db_connection...")
            with get_working_db_connection() as connection:
                if not connection:
                    logger.error("❌ ERROR: Could not establish database connection")
                    return {"success": False, "error": "Database connection failed"}
                
                logger.info("✅ Database connection established successfully")
                logger.info(f"Connection type: {type(connection)}")
                logger.info(f"Connection info: {connection.info if hasattr(connection, 'info') else 'No info available'}")
                
                logger.info("Step 3: Creating database cursor...")
                cursor = connection.cursor()
                logger.info(f"✅ Cursor created: {type(cursor)}")
                
                # First, create a user authentication entry (we'll need to create this table)
                # For now, we'll store the password hash in a separate table or as a comment
                
                # Insert the farmer using psycopg2 style (like working dashboard)
                logger.info("Step 4: Executing INSERT query for farmer...")
                logger.info(f"Query parameters: farm_name={data.get('farm_name')}, manager={data.get('manager_name')} {data.get('manager_last_name')}")
                
                cursor.execute("""
                    INSERT INTO farmers (
                        farm_name, manager_name, manager_last_name, 
                        city, country, phone, wa_phone_number, email, 
                        state_farm_number, street_and_no, village, postal_code
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                    """, (
                        data.get("farm_name"),
                        data.get("manager_name"),
                        data.get("manager_last_name"),
                        data.get("city"),
                        data.get("country"),
                        data.get("phone") or None,
                        data.get("wa_phone_number"),
                        data.get("email"),
                        data.get("state_farm_number") or None,
                        data.get("street_and_no") or None,
                        data.get("village") or None,
                        data.get("postal_code") or None
                    ))
                
                # Get the farmer_id
                result = cursor.fetchone()
                if not result:
                    logger.error("❌ No farmer_id returned from INSERT!")
                    raise Exception("Failed to insert farmer - no ID returned")
                    
                farmer_id = result[0]
                logger.info(f"✅ Farmer inserted with ID: {farmer_id}")
                
                # Insert fields
                logger.info(f"Step 5: Inserting {len(data.get('fields', []))} fields...")
                for field in data.get("fields", []):
                    # Handle polygon data if present
                    polygon_data = field.get("polygon_data")
                    calculated_area = None
                    centroid_lat = None
                    centroid_lng = None
                    
                    if polygon_data:
                        # Parse polygon data JSON
                        if isinstance(polygon_data, str):
                            polygon_data = json.loads(polygon_data)
                        
                        calculated_area = polygon_data.get("area")
                        centroid = polygon_data.get("centroid", {})
                        centroid_lat = centroid.get("lat")
                        centroid_lng = centroid.get("lng")
                    
                    # Check if fields table has area_hectares or area_ha column
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'fields' AND column_name IN ('area_hectares', 'area_ha')
                    """)
                    area_column = cursor.fetchone()
                    area_col_name = area_column[0] if area_column else 'area_ha'  # Use area_ha as default
                    
                    # Try to insert field - handle duplicate key issues
                    try:
                        # First try without specifying ID (should use auto-increment)
                        cursor.execute(f"""
                            INSERT INTO fields (
                                farmer_id, field_name, {area_col_name}
                            ) VALUES (
                                %s, %s, %s
                            )
                            RETURNING id
                        """, (
                            farmer_id,
                            field.get("name"),
                            field.get("size")
                        ))
                        field_id = cursor.fetchone()[0]
                        logger.info(f"✅ Inserted field '{field.get('name')}' with ID {field_id}")
                    except psycopg2.errors.UniqueViolation as e:
                        logger.warning(f"⚠️ Duplicate key error: {str(e)}")
                        # Rollback the failed transaction
                        connection.rollback()
                        logger.info("Rolled back failed transaction")
                        
                        # Try to find max ID and insert with explicit ID
                        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM fields")
                        next_id = cursor.fetchone()[0]
                        logger.info(f"Retrying with explicit ID: {next_id}")
                        cursor.execute(f"""
                            INSERT INTO fields (
                                id, farmer_id, field_name, {area_col_name}
                            ) VALUES (
                                %s, %s, %s, %s
                            )
                            RETURNING id
                        """, (
                            next_id,
                            farmer_id,
                            field.get("name"),
                            field.get("size")
                        ))
                        field_id = cursor.fetchone()[0]
                        logger.info(f"✅ Inserted field '{field.get('name')}' with explicit ID {field_id}")
                
                # Create user authentication record
                # For now, we'll store a hashed password in a comment
                # In production, this should be in a proper authentication table
                import hashlib
                password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
                
                # Store authentication info (temporary solution) using psycopg2
                cursor.execute("""
                    INSERT INTO incoming_messages (
                        farmer_id, phone_number, message_text, role, timestamp
                    ) VALUES (
                        %s, %s, %s, 'system', CURRENT_TIMESTAMP
                    )
                """, (
                    farmer_id,
                    data['email'],
                    f"AUTH_RECORD: email={data['email']}, password_hash={password_hash}"
                ))
                
                connection.commit()
                
                print(f"✅ Successfully registered farmer {data['manager_name']} {data['manager_last_name']} with ID {farmer_id}")
                print(f"   - Farm: {data.get('farm_name')}")
                print(f"   - Fields: {len(data.get('fields', []))}")
                print(f"   - Location: {data.get('city')}, {data.get('country')}")
                
                logger.info(f"Successfully registered farmer {data['manager_name']} {data['manager_last_name']} with ID {farmer_id}")
                return {"success": True, "farmer_id": farmer_id}
                
        except Exception as e:
            logger.error("❌ EXCEPTION IN INSERT_FARMER_WITH_FIELDS")
            logger.error(f"❌ Error message: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
            
            # Check for specific database errors
            if "duplicate key" in str(e).lower():
                logger.error("🚨 DUPLICATE KEY ERROR - Field ID already exists!")
                # Extract the duplicate ID if possible
                import re
                match = re.search(r'Key \(id\)=\((\d+)\)', str(e))
                if match:
                    dup_id = match.group(1)
                    logger.error(f"🚨 Duplicate ID: {dup_id}")
                    return {"success": False, "error": f"Field ID {dup_id} already exists. The database may need ID sequence reset."}
            
            # Check for specific error patterns
            if "generator" in str(e).lower():
                logger.error("🚨 GENERATOR ERROR DETECTED IN DATABASE OPERATIONS!")
            if "await" in str(e).lower() or "async" in str(e).lower():
                logger.error("🚨 ASYNC/AWAIT ERROR DETECTED!")
            
            print(f"❌ Error inserting farmer with fields: {str(e)}")
            return {"success": False, "error": str(e)}