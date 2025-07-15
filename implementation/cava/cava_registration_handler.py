"""
🏛️ CAVA Registration Handler
Replaces old registration systems with CAVA-powered registration
Uses the central CAVA service for all registration logic
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from implementation.cava.cava_central_service import get_cava_service, cava_handle_registration

logger = logging.getLogger(__name__)

class CAVARegistrationHandler:
    """
    Registration handler that uses CAVA for all logic
    No more hardcoded registration flow - CAVA handles everything
    """
    
    def __init__(self):
        self.active_sessions = {}  # Track active registration sessions
    
    async def start_registration(self, farmer_id: int, initial_message: str = None) -> Dict[str, Any]:
        """
        Start a new registration session
        If initial_message provided, process it (e.g., "Peter Knaflič")
        """
        session_id = str(uuid.uuid4())
        
        # Store session info
        self.active_sessions[farmer_id] = {
            "session_id": session_id,
            "started_at": datetime.now().isoformat(),
            "completed": False
        }
        
        if initial_message:
            # Process the initial message (like name)
            return await self.process_registration_message(farmer_id, initial_message)
        else:
            # Send empty message to trigger welcome
            cava = await get_cava_service()
            return await cava.send_message(
                farmer_id=farmer_id,
                message="",
                session_id=session_id,
                channel="registration"
            )
    
    async def process_registration_message(
        self,
        farmer_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Process a registration message through CAVA
        CAVA handles all the logic of what to ask next
        """
        # Get or create session
        session_info = self.active_sessions.get(farmer_id)
        if not session_info:
            return await self.start_registration(farmer_id, message)
        
        session_id = session_info["session_id"]
        
        # Send to CAVA
        response = await cava_handle_registration(
            farmer_id=farmer_id,
            message=message,
            session_id=session_id
        )
        
        # Check if registration completed
        if response.get("success") and "complete" in response.get("message", "").lower():
            session_info["completed"] = True
            session_info["completed_at"] = datetime.now().isoformat()
            logger.info("✅ Registration completed for farmer %s", farmer_id)
        
        return response
    
    async def get_registration_status(self, farmer_id: int) -> Dict[str, Any]:
        """Get current registration status for a farmer"""
        session_info = self.active_sessions.get(farmer_id, {})
        
        if not session_info:
            return {
                "registered": False,
                "in_progress": False,
                "session_id": None
            }
        
        # Get conversation history from CAVA
        cava = await get_cava_service()
        history = await cava.get_conversation_history(session_info["session_id"])
        
        return {
            "registered": session_info.get("completed", False),
            "in_progress": not session_info.get("completed", False),
            "session_id": session_info["session_id"],
            "started_at": session_info.get("started_at"),
            "completed_at": session_info.get("completed_at"),
            "conversation_history": history
        }
    
    def clear_session(self, farmer_id: int):
        """Clear registration session (for testing or reset)"""
        if farmer_id in self.active_sessions:
            del self.active_sessions[farmer_id]
            logger.info("Cleared registration session for farmer %s", farmer_id)

# Global registration handler instance
_registration_handler = None

def get_registration_handler() -> CAVARegistrationHandler:
    """Get the global registration handler instance"""
    global _registration_handler
    if _registration_handler is None:
        _registration_handler = CAVARegistrationHandler()
    return _registration_handler

# Convenience functions for easy integration
async def handle_registration_input(farmer_id: int, user_input: str) -> Dict[str, Any]:
    """
    Main function to handle any registration input
    This is what signup forms should call
    """
    handler = get_registration_handler()
    return await handler.process_registration_message(farmer_id, user_input)

async def start_new_registration(farmer_id: int) -> Dict[str, Any]:
    """Start a fresh registration session"""
    handler = get_registration_handler()
    return await handler.start_registration(farmer_id)

async def check_registration_status(farmer_id: int) -> Dict[str, Any]:
    """Check if farmer is registered or registration in progress"""
    handler = get_registration_handler()
    return await handler.get_registration_status(farmer_id)