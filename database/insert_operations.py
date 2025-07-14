"""
Constitutional Database Insert Operations
Safe insertion functions following Constitutional Principles
"""

import logging
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager
import psycopg2
from datetime import datetime
from .data_validators import constitutional_validator

logger = logging.getLogger(__name__)

class ConstitutionalInsertOperations:
    """Safe database insertion operations with constitutional compliance"""
    
    def __init__(self, db_connection_func):
        """
        Initialize with database connection function
        
        Args:
            db_connection_func: Function that returns database connection context
        """
        self.get_db_connection = db_connection_func
    
    async def insert_farmer(self, farmer_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Insert new farmer with constitutional validation
        
        Args:
            farmer_data: Dictionary containing farmer information
            
        Returns:
            Tuple of (success, message, farmer_id)
        """
        # Constitutional validation first
        validation_result = await constitutional_validator.validate_farmer_data(farmer_data)
        
        if not validation_result['valid']:
            error_msg = '; '.join(validation_result['errors'])
            return False, f"Validation failed: {error_msg}", None
        
        if not validation_result['constitutional_compliance']:
            return False, "Constitutional compliance failed: MANGO RULE violation", None
        
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Constitutional insert: Support all countries and crops
                insert_query = """
                INSERT INTO farmers (
                    farm_name, 
                    manager_name, 
                    manager_last_name,
                    city, 
                    country, 
                    phone, 
                    wa_phone_number, 
                    email,
                    country_code,
                    preferred_language,
                    whatsapp_number,
                    timezone,
                    localization_preferences,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING farmer_id
                """
                
                # Prepare data with constitutional defaults
                values = (
                    farmer_data.get('farm_name'),
                    farmer_data.get('manager_name'),
                    farmer_data.get('manager_last_name'),
                    farmer_data.get('city'),
                    farmer_data.get('country'),
                    farmer_data.get('phone'),
                    farmer_data.get('wa_phone_number'),
                    farmer_data.get('email'),
                    farmer_data.get('country_code'),
                    farmer_data.get('preferred_language', 'en'),
                    farmer_data.get('whatsapp_number'),
                    farmer_data.get('timezone'),
                    farmer_data.get('localization_preferences', {}),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                farmer_id = cursor.fetchone()[0]
                connection.commit()
                
                # Privacy-first logging
                logger.info(f"Farmer created successfully: farmer_id={farmer_id}")
                
                success_msg = f"Farmer created successfully! ID: {farmer_id}"
                if validation_result['suggestions']:
                    success_msg += f" Suggestions: {'; '.join(validation_result['suggestions'])}"
                
                return True, success_msg, farmer_id
                
        except psycopg2.Error as e:
            logger.error(f"Database error inserting farmer: {e}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error inserting farmer: {e}")
            return False, f"Unexpected error: {str(e)}", None
    
    async def insert_field(self, field_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Insert new field data with constitutional validation
        
        Args:
            field_data: Dictionary containing field information
            
        Returns:
            Tuple of (success, message, field_id)
        """
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Use existing fields table structure - no table creation needed
                
                # Constitutional insert: Support all field types globally
                insert_query = """
                INSERT INTO fields (
                    farmer_id,
                    field_name,
                    area_ha,
                    latitude,
                    longitude,
                    country,
                    notes,
                    blok_id,
                    raba,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """
                
                values = (
                    field_data.get('farmer_id'),
                    field_data.get('field_name'),
                    field_data.get('area_ha'),
                    field_data.get('latitude'),
                    field_data.get('longitude'),
                    field_data.get('country'),
                    field_data.get('notes'),
                    field_data.get('blok_id'),
                    field_data.get('raba'),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                field_id = cursor.fetchone()[0]
                connection.commit()
                
                # Privacy-first logging
                logger.info(f"Field created successfully: field_id={field_id}")
                
                success_msg = f"Field '{field_data.get('field_name')}' added successfully! ID: {field_id}"
                if field_data.get('area_ha'):
                    success_msg += f" Area: {field_data.get('area_ha')} ha"
                
                return True, success_msg, field_id
                
        except psycopg2.Error as e:
            logger.error(f"Database error inserting field: {e}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error inserting field: {e}")
            return False, f"Unexpected error: {str(e)}", None

    async def insert_crop(self, crop_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Insert new crop data with constitutional validation
        
        Args:
            crop_data: Dictionary containing crop information
            
        Returns:
            Tuple of (success, message, crop_id)
        """
        # Constitutional validation
        validation_result = await constitutional_validator.validate_crop_data(crop_data)
        
        if not validation_result['valid']:
            error_msg = '; '.join(validation_result['errors'])
            return False, f"Validation failed: {error_msg}", None
        
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Use existing field_crops table structure - no table creation needed
                
                # Constitutional insert: Support all crops globally
                insert_query = """
                INSERT INTO crops (
                    farmer_id,
                    crop_name,
                    variety,
                    planting_date,
                    expected_harvest_date,
                    field_size_hectares,
                    planting_method,
                    growth_stage,
                    notes,
                    country,
                    climate_zone,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING crop_id
                """
                
                values = (
                    crop_data.get('farmer_id'),
                    crop_data.get('crop_name'),
                    crop_data.get('variety'),
                    crop_data.get('planting_date'),
                    crop_data.get('expected_harvest_date'),
                    crop_data.get('field_size_hectares'),
                    crop_data.get('planting_method'),
                    crop_data.get('growth_stage', 'planning'),
                    crop_data.get('notes'),
                    crop_data.get('country'),
                    crop_data.get('climate_zone'),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                crop_id = cursor.fetchone()[0]
                connection.commit()
                
                # Privacy-first logging
                logger.info(f"Crop created successfully: crop_id={crop_id}")
                
                success_msg = f"Crop '{crop_data.get('crop_name')}' added successfully! ID: {crop_id}"
                if validation_result['warnings']:
                    success_msg += f" Warnings: {'; '.join(validation_result['warnings'])}"
                if validation_result['suggestions']:
                    success_msg += f" Suggestions: {'; '.join(validation_result['suggestions'])}"
                
                return True, success_msg, crop_id
                
        except psycopg2.Error as e:
            logger.error(f"Database error inserting crop: {e}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error inserting crop: {e}")
            return False, f"Unexpected error: {str(e)}", None
    
    async def insert_agricultural_advice(self, advice_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Insert agricultural advice/knowledge with constitutional compliance
        
        Args:
            advice_data: Dictionary containing advice information
            
        Returns:
            Tuple of (success, message, advice_id)
        """
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Use existing incoming_messages table structure for advice - no table creation needed
                
                # Constitutional insert: Global advice support
                insert_query = """
                INSERT INTO agricultural_advice (
                    farmer_id,
                    crop_name,
                    advice_type,
                    title,
                    content,
                    country,
                    language,
                    climate_relevance,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING advice_id
                """
                
                values = (
                    advice_data.get('farmer_id'),
                    advice_data.get('crop_name'),
                    advice_data.get('advice_type', 'general'),
                    advice_data.get('title'),
                    advice_data.get('content'),
                    advice_data.get('country'),
                    advice_data.get('language', 'en'),
                    advice_data.get('climate_relevance'),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                advice_id = cursor.fetchone()[0]
                connection.commit()
                
                # Privacy-first logging
                logger.info(f"Agricultural advice created: advice_id={advice_id}")
                
                return True, f"Agricultural advice added successfully! ID: {advice_id}", advice_id
                
        except psycopg2.Error as e:
            logger.error(f"Database error inserting advice: {e}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error inserting advice: {e}")
            return False, f"Unexpected error: {str(e)}", None