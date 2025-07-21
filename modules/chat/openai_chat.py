#!/usr/bin/env python3
"""
OpenAI Chat Service
Direct integration with GPT-4 for agricultural conversations
"""
import os
import logging
from typing import Dict, List, Optional
import httpx
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIChat:
    """OpenAI GPT-4 chat service for agricultural assistance"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"  # Use gpt-3.5-turbo if gpt-4 not available
        self.conversations = {}  # Store conversations by session_id
        self.max_history = 10  # Keep last 10 messages for context
        
    def _get_system_prompt(self, farmer_context: Dict) -> str:
        """Generate system prompt with farmer context"""
        prompt = """You are AVA, an intelligent agricultural assistant helping farmers with their daily operations. 
You have expertise in:
- Crop management and cultivation techniques
- Weather impact on farming
- Pest and disease identification
- Irrigation and water management
- Harvest timing and techniques
- Soil health and fertilization

Be helpful, practical, and provide actionable advice. Keep responses concise and farmer-friendly."""

        if farmer_context:
            prompt += f"\n\nThe farmer you're talking to has these fields:\n"
            for field in farmer_context.get('fields', []):
                prompt += f"- {field['name']}: {field['crop']} ({field['hectares']} ha)\n"
                
        return prompt
    
    async def send_message(self, session_id: str, message: str, farmer_context: Dict) -> Dict:
        """Send message to OpenAI and get response"""
        try:
            # Get or create conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            history = self.conversations[session_id]
            
            # Build messages array
            messages = [
                {"role": "system", "content": self._get_system_prompt(farmer_context)}
            ]
            
            # Add conversation history
            messages.extend(history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Use mock response if no API key
            if not self.api_key:
                return await self._get_mock_response(message, farmer_context)
            
            # Call OpenAI API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data['choices'][0]['message']['content']
                    
                    # Update conversation history
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": ai_response})
                    
                    # Keep only last N messages
                    self.conversations[session_id] = history[-self.max_history:]
                    
                    return {
                        "response": ai_response,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model
                    }
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return await self._get_mock_response(message, farmer_context)
                    
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return await self._get_mock_response(message, farmer_context)
    
    async def _get_mock_response(self, message: str, farmer_context: Dict) -> Dict:
        """Generate mock response when API is unavailable"""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if "weather" in message_lower:
            response = "Based on the current weather forecast, conditions look favorable for the next few days. Make sure to monitor the hourly forecast for any changes in precipitation that might affect your field operations."
        elif "harvest" in message_lower:
            response = "For optimal harvest timing, monitor your crop's maturity indicators. Consider the weather forecast - you'll want dry conditions for at least 2-3 days during harvest. Check the moisture content if possible."
        elif "pest" in message_lower or "disease" in message_lower:
            response = "Regular field inspection is key for pest and disease management. Look for unusual spots, discoloration, or insect damage. Early detection allows for more effective treatment. Would you like me to help identify specific symptoms?"
        elif "irrigation" in message_lower or "water" in message_lower:
            response = "Proper irrigation depends on your soil type, crop stage, and weather conditions. Check soil moisture at root depth. Generally, deep and infrequent watering promotes better root development than frequent shallow irrigation."
        elif "fertiliz" in message_lower:
            response = "Fertilization should be based on soil test results and crop requirements. Split applications often work better than single large doses. Consider the growth stage of your crop and upcoming weather when planning applications."
        else:
            response = "I'm here to help with your agricultural questions. You can ask me about weather conditions, crop management, pest control, irrigation, harvest timing, or any other farming concerns you have."
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "mock"
        }
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

# Singleton instance
_openai_chat = None

def get_openai_chat() -> OpenAIChat:
    """Get or create OpenAI chat instance"""
    global _openai_chat
    if _openai_chat is None:
        _openai_chat = OpenAIChat()
    return _openai_chat