#!/usr/bin/env python3
"""
🏛️ CAVA Central Service Manager
Manages CAVA as a singleton service for the entire application
All parts of the app connect to this central instance
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

class CAVACentralService:
    """
    Singleton CAVA service manager
    Ensures all parts of the app use the same CAVA instance
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def initialize(self):
        """Initialize the central CAVA service once"""
        async with self._lock:
            if self._initialized:
                return
            
            # Check if running in integrated mode (within main API)
            integrated_mode = os.getenv('CAVA_INTEGRATED_MODE', 'false').lower() == 'true'
            
            if integrated_mode:
                # Use direct function calls instead of HTTP
                self.integrated_mode = True
                self.cava_url = None  # Not used in integrated mode
            else:
                # Use HTTP calls to separate service
                self.integrated_mode = False
                self.cava_url = os.getenv('CAVA_SERVICE_URL', 'http://localhost:8001')
            self.timeout = aiohttp.ClientTimeout(total=30)
            self.session = None
            self._initialized = True
            
            logger.info("🏛️ CAVA Central Service initialized at %s", self.cava_url)
            
            # Check if CAVA is running
            await self.health_check()
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def health_check(self) -> bool:
        """Check if CAVA service is healthy"""
        # In integrated mode, always return True (no separate service to check)
        if self.integrated_mode:
            logger.info("✅ CAVA health: integrated mode active")
            return True
            
        try:
            await self.ensure_session()
            async with self.session.get(f"{self.cava_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ CAVA health: %s", data['status'])
                    return True
                else:
                    logger.error("❌ CAVA unhealthy: status %s", response.status)
                    return False
        except Exception as e:
            logger.error("❌ CAVA health check failed: %s", str(e))
            return False
    
    async def send_message(
        self,
        farmer_id: int,
        message: str,
        session_id: Optional[str] = None,
        channel: str = "web"
    ) -> Dict[str, Any]:
        """
        Send message to CAVA and get response
        Central method used by all parts of the app
        """
        # Integrated mode - use direct function calls
        if self.integrated_mode:
            from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine
            
            if not hasattr(self, '_engine'):
                self._engine = CAVAUniversalConversationEngine()
                await self._engine.initialize()
            
            return await self._engine.handle_farmer_message(
                farmer_id=farmer_id,
                message=message,
                session_id=session_id,
                channel=channel
            )
        
        # Standalone mode - use HTTP
        await self.ensure_session()
        
        try:
            payload = {
                "farmer_id": farmer_id,
                "message": message,
                "channel": channel
            }
            
            if session_id:
                payload["session_id"] = session_id
            
            async with self.session.post(
                f"{self.cava_url}/conversation",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error("CAVA error: %s", error_text)
                    return {
                        "success": False,
                        "error": f"CAVA returned {response.status}",
                        "message": "I'm having trouble processing that. Please try again."
                    }
                    
        except asyncio.TimeoutError:
            logger.error("CAVA timeout")
            return {
                "success": False,
                "error": "timeout",
                "message": "The system is taking too long to respond. Please try again."
            }
        except Exception as e:
            logger.error("CAVA request failed: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "I'm having technical difficulties. Please try again later."
            }
    
    async def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Get conversation history from CAVA"""
        await self.ensure_session()
        
        try:
            async with self.session.post(
                f"{self.cava_url}/conversation/history",
                json={"session_id": session_id}
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error("Failed to get history: %s", str(e))
            return None
    
    async def close(self):
        """Close the central service"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔒 CAVA Central Service closed")
    
    @classmethod
    def reset(cls):
        """Reset singleton (mainly for testing)"""
        if cls._instance and cls._instance.session:
            asyncio.create_task(cls._instance.close())
        cls._instance = None

# Global CAVA instance getter
_cava_service = None

async def get_cava_service() -> CAVACentralService:
    """
    Get the global CAVA service instance
    This ensures all parts of the app use the same CAVA
    """
    global _cava_service
    if _cava_service is None:
        _cava_service = CAVACentralService()
        await _cava_service.initialize()
    return _cava_service

# Convenience function for registration
async def cava_handle_registration(
    farmer_id: int,
    message: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function specifically for registration
    Used by signup forms throughout the app
    """
    cava = await get_cava_service()
    return await cava.send_message(
        farmer_id=farmer_id,
        message=message,
        session_id=session_id,
        channel="registration"
    )

# Convenience function for farming conversations
async def cava_handle_farming(
    farmer_id: int,
    message: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for farming conversations
    Used by chat interfaces throughout the app
    """
    cava = await get_cava_service()
    return await cava.send_message(
        farmer_id=farmer_id,
        message=message,
        session_id=session_id,
        channel="farming_chat"
    )