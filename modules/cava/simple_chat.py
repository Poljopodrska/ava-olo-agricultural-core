#!/usr/bin/env python3
"""
Simple Chat for Registration - Step 1
Just passes messages to LLM with context, no extraction
"""
from typing import Dict
import logging
from modules.chat.openai_chat import get_openai_chat

logger = logging.getLogger(__name__)

class SimpleRegistrationChat:
    """Simple chat that passes messages to LLM with registration context"""
    
    def __init__(self):
        self.chat_service = get_openai_chat()
        self.conversations = {}  # Store conversation history
    
    async def chat(self, session_id: str, message: str) -> Dict:
        """Send message to LLM with registration context"""
        
        # Initialize conversation history if needed
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Add user message to history
        self.conversations[session_id].append(f"User: {message}")
        
        # Keep last 10 messages for context
        recent_history = self.conversations[session_id][-10:]
        
        # Build prompt with registration context
        prompt = f"""You are AVA, a friendly agricultural assistant helping a farmer register for AVA OLO.

Your goal is to naturally collect these 3 pieces of information through conversation:
- First name
- Last name
- WhatsApp number

Recent conversation:
{chr(10).join(recent_history)}

Instructions:
1. Be conversational and natural, like chatting on WhatsApp
2. Respond in the same language the user uses
3. Don't ask for all information at once
4. If they provide information, acknowledge it naturally
5. If they ask why you need information, explain it's for personalized farming advice and weather alerts
6. Keep responses concise and friendly

Respond naturally to the user's last message."""

        try:
            # Get LLM response
            result = await self.chat_service.send_message(
                f"reg_chat_{session_id}",
                prompt,
                {"temperature": 0.7}
            )
            
            response = result.get("response", "I'm here to help you register. What's your name?")
            
            # Add assistant response to history
            self.conversations[session_id].append(f"Assistant: {response}")
            
            return {
                "response": response,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            
            # Simple fallback responses
            if len(self.conversations[session_id]) == 1:  # First message
                response = "Hello! I'm AVA, here to help you register. What's your name?"
            else:
                response = "I'm having trouble understanding. Could you please tell me your name?"
            
            self.conversations[session_id].append(f"Assistant: {response}")
            
            return {
                "response": response,
                "session_id": session_id
            }