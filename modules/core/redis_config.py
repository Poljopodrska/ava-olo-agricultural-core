#!/usr/bin/env python3
"""
Redis configuration and connection management for AVA OLO
"""
import redis
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class RedisConfig:
    """
    Redis connection configuration
    
    Handles connection to Redis for caching farmer welcome packages
    """
    
    @staticmethod
    def get_redis_client() -> Optional[redis.Redis]:
        """
        Get configured Redis client
        
        Uses environment variables for connection settings
        Falls back to ElastiCache if available in AWS
        """
        
        # Get Redis connection details from environment
        # Don't default to a non-existent host - require explicit configuration
        redis_host = os.getenv('REDIS_HOST')
        if not redis_host:
            logger.warning("REDIS_HOST not configured - Redis caching disabled")
            return None
            
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        try:
            # Create Redis client
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                max_connections=50,
                health_check_interval=30
            )
            
            # Test connection
            client.ping()
            logger.info(f"Redis connected successfully to {redis_host}:{redis_port}")
            return client
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {redis_host}:{redis_port}: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis configuration error: {e}")
            return None
    
    @staticmethod
    def test_redis_connection() -> bool:
        """Test if Redis is accessible"""
        try:
            client = RedisConfig.get_redis_client()
            if client:
                client.ping()
                logger.info("Redis connection test successful")
                return True
            return False
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False
    
    @staticmethod
    def get_redis_info() -> Dict:
        """Get Redis server information"""
        try:
            client = RedisConfig.get_redis_client()
            if client:
                info = client.info()
                return {
                    "connected": True,
                    "redis_version": info.get('redis_version', 'unknown'),
                    "used_memory_human": info.get('used_memory_human', 'unknown'),
                    "connected_clients": info.get('connected_clients', 0),
                    "uptime_in_days": info.get('uptime_in_days', 0)
                }
            return {"connected": False}
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"connected": False, "error": str(e)}
    
    @staticmethod
    def setup_redis_for_welcome_packages():
        """
        Setup Redis with appropriate settings for welcome packages
        """
        try:
            client = RedisConfig.get_redis_client()
            if not client:
                logger.error("Cannot setup Redis - no connection")
                return False
            
            # Set max memory policy to allkeys-lru (evict least recently used keys)
            # This ensures old welcome packages are removed if memory is full
            try:
                client.config_set('maxmemory-policy', 'allkeys-lru')
                logger.info("Redis maxmemory-policy set to allkeys-lru")
            except redis.ResponseError:
                # May not have CONFIG permission in managed Redis
                logger.warning("Cannot set Redis config (managed instance)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Redis: {e}")
            return False