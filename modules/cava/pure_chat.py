#!/usr/bin/env python3
"""
Pure Chat - No validation, no hardcoding, just LLM
"""
from typing import Dict
import logging
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

class PureChat:
    """Pure LLM chat - no validation or hardcoding"""
    
    def __init__(self):
        self.chat_service = get_openai_chat()
    
    async def chat(self, session_id: str, message: str) -> Dict:
        """Just pass message to LLM with minimal context"""
        
        # Simple prompt - let LLM handle everything
        prompt = f"""You are AVA, helping a farmer register.
You need to collect their first name, last name, and WhatsApp number.
Respond naturally to whatever they say.
If they mention crocodiles or sunshine, acknowledge it and gently guide back.

Farmer said: {message}

Respond in a friendly, conversational way."""

        try:
            # Get LLM response
            result = await self.chat_service.send_message(
                f"pure_chat_{session_id}",
                prompt,
                {"temperature": 0.7}
            )
            
            response = result.get("response", "Hello! I'm AVA. I'd love to help you register.")
            
            return {"response": response}
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            # Even fallback should be natural
            return {"response": "Hello! I'm AVA. I'd love to help you register."}