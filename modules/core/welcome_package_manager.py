#!/usr/bin/env python3
"""
Redis-based Welcome Package Manager for Farmer Conversations
Provides instant farmer context for FAVA conversations with 4-hour cache TTL
"""
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class WelcomePackageManager:
    """
    Manages farmer welcome packages in Redis cache
    
    SIMPLE CONCEPT: 
    - Store farmer's current context (fields, crops, tasks) in Redis
    - Auto-expire after 4 hours to ensure freshness
    - Rebuild from database when missing or expired
    """
    
    def __init__(self, redis_client, db_ops):
        self.redis = redis_client
        self.db = db_ops
        self.ttl_seconds = 14400  # 4 hours
        self.logger = logging.getLogger(__name__)
    
    def get_welcome_package(self, farmer_id: int) -> Dict:
        """
        Main method: Get farmer's welcome package
        
        LOGIC FLOW:
        1. Try to get from Redis first (fast path)
        2. If not found or expired, rebuild from database
        3. Return farmer context ready for FAVA
        """
        cache_key = f"welcome_package:{farmer_id}"
        
        try:
            # Try Redis first
            cached_package = self.redis.get(cache_key)
            
            if cached_package:
                # Found in cache - parse and return
                package_data = json.loads(cached_package)
                self.logger.info(f"Welcome package loaded from Redis for farmer {farmer_id}")
                return package_data
            
            # Not in cache - build fresh
            return self._build_and_cache_package(farmer_id)
            
        except Exception as e:
            self.logger.error(f"Redis error for farmer {farmer_id}: {e}")
            # Fallback to database if Redis fails
            return self._build_package_from_database(farmer_id)
    
    def _build_and_cache_package(self, farmer_id: int) -> Dict:
        """
        Build fresh package from database and store in Redis
        """
        package_data = self._build_package_from_database(farmer_id)
        
        # Store in Redis with 4-hour expiration
        cache_key = f"welcome_package:{farmer_id}"
        try:
            self.redis.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(package_data, default=self._json_serializer)
            )
            self.logger.info(f"Welcome package cached in Redis for farmer {farmer_id}")
        except Exception as e:
            self.logger.error(f"Failed to cache package for farmer {farmer_id}: {e}")
        
        return package_data
    
    def _json_serializer(self, obj):
        """Handle special types for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    
    def _build_package_from_database(self, farmer_id: int) -> Dict:
        """
        Query database and build complete farmer context
        Adapted to actual AVA OLO database schema
        """
        
        # Basic farmer info
        farmer_query = """
            SELECT farm_name, manager_name, manager_last_name, city, country, 
                   phone, wa_phone_number, email, created_at
            FROM farmers 
            WHERE id = %s
        """
        farmer_result = self.db.execute_query(farmer_query, (farmer_id,))
        
        # All farmer's fields (adapted to actual schema)
        fields_query = """
            SELECT field_name, area_ha, latitude, longitude, 
                   blok_id, raba, country, created_at
            FROM fields 
            WHERE farmer_id = %s
            ORDER BY created_at DESC
        """
        fields_result = self.db.execute_query(fields_query, (farmer_id,))
        
        # Recent tasks (last 30 days)
        tasks_query = """
            SELECT t.task_type, t.task_description, t.due_date, 
                   t.status, t.created_at, f.field_name 
            FROM tasks t 
            JOIN fields f ON t.field_id = f.id 
            WHERE f.farmer_id = %s 
                AND t.created_at >= %s
            ORDER BY t.created_at DESC 
            LIMIT 10
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)
        tasks_result = self.db.execute_query(tasks_query, (farmer_id, thirty_days_ago))
        
        # Current crops
        crops_query = """
            SELECT fc.crop_name, fc.variety, fc.planting_date, 
                   fc.harvest_date, fc.status, fc.area_ha, f.field_name 
            FROM field_crops fc 
            JOIN fields f ON fc.field_id = f.id 
            WHERE f.farmer_id = %s
                AND (fc.status IS NULL OR fc.status != 'harvested')
            ORDER BY fc.planting_date DESC
        """
        crops_result = self.db.execute_query(crops_query, (farmer_id,))
        
        # Build package structure
        farmer_info = {}
        if farmer_result.get('success') and farmer_result.get('rows'):
            row = farmer_result['rows'][0]
            farmer_info = {
                "farm_name": row[0],
                "manager_name": row[1],
                "manager_last_name": row[2],
                "city": row[3],
                "country": row[4],
                "phone": row[5],
                "wa_phone_number": row[6],
                "email": row[7],
                "member_since": row[8].isoformat() if row[8] else None
            }
        
        fields = []
        total_hectares = 0
        if fields_result.get('success') and fields_result.get('rows'):
            for field in fields_result['rows']:
                field_data = {
                    "name": field[0],
                    "area_ha": float(field[1]) if field[1] else 0,
                    "latitude": float(field[2]) if field[2] else None,
                    "longitude": float(field[3]) if field[3] else None,
                    "blok_id": field[4],
                    "raba": field[5],
                    "country": field[6]
                }
                fields.append(field_data)
                if field[1]:
                    total_hectares += float(field[1])
        
        recent_tasks = []
        if tasks_result.get('success') and tasks_result.get('rows'):
            for task in tasks_result['rows']:
                recent_tasks.append({
                    "task_type": task[0],
                    "description": task[1],
                    "due_date": task[2].isoformat() if task[2] else None,
                    "status": task[3],
                    "created_at": task[4].isoformat() if task[4] else None,
                    "field": task[5]
                })
        
        current_crops = []
        if crops_result.get('success') and crops_result.get('rows'):
            for crop in crops_result['rows']:
                current_crops.append({
                    "crop": crop[0],
                    "variety": crop[1],
                    "planting_date": crop[2].isoformat() if crop[2] else None,
                    "harvest_date": crop[3].isoformat() if crop[3] else None,
                    "status": crop[4],
                    "area_ha": float(crop[5]) if crop[5] else 0,
                    "field": crop[6]
                })
        
        # Build complete package
        package = {
            "farmer_id": farmer_id,
            "farmer_info": farmer_info,
            "fields": fields,
            "total_fields": len(fields),
            "total_hectares": round(total_hectares, 2),
            "recent_tasks": recent_tasks,
            "current_crops": current_crops,
            "generated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.ttl_seconds)).isoformat(),
            "source": "database"
        }
        
        return package
    
    def update_package_data(self, farmer_id: int, updates: Dict):
        """
        Update existing package when farmer adds new data
        
        USAGE: When farmer says "I planted corn in north field"
        Call this to immediately update Redis cache
        """
        cache_key = f"welcome_package:{farmer_id}"
        
        try:
            # Get current package
            current_package = self.get_welcome_package(farmer_id)
            
            # Apply updates
            if 'fields' in updates:
                current_package['fields'] = updates['fields']
                current_package['total_fields'] = len(updates['fields'])
            
            if 'crops' in updates:
                current_package['current_crops'] = updates['crops']
            
            if 'tasks' in updates:
                current_package['recent_tasks'] = updates['tasks']
            
            current_package["last_updated"] = datetime.now().isoformat()
            
            # Save back to Redis
            self.redis.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(current_package, default=self._json_serializer)
            )
            
            self.logger.info(f"Welcome package updated for farmer {farmer_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update package for farmer {farmer_id}: {e}")
    
    def clear_package(self, farmer_id: int):
        """Force refresh by clearing cache"""
        cache_key = f"welcome_package:{farmer_id}"
        try:
            self.redis.delete(cache_key)
            self.logger.info(f"Welcome package cleared for farmer {farmer_id}")
        except Exception as e:
            self.logger.error(f"Failed to clear package for farmer {farmer_id}: {e}")
    
    def get_package_stats(self, farmer_id: int) -> Dict:
        """Get statistics about the welcome package"""
        cache_key = f"welcome_package:{farmer_id}"
        
        try:
            # Check if exists and get TTL
            ttl = self.redis.ttl(cache_key)
            exists = ttl > 0
            
            return {
                "exists": exists,
                "ttl_seconds": ttl if exists else 0,
                "ttl_hours": round(ttl / 3600, 2) if exists else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get package stats for farmer {farmer_id}: {e}")
            return {"exists": False, "ttl_seconds": 0, "ttl_hours": 0}