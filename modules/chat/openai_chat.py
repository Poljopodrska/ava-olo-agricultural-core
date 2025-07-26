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
import random

logger = logging.getLogger(__name__)

class OpenAIChat:
    """OpenAI GPT-4 chat service for agricultural assistance"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"  # Use gpt-3.5-turbo if gpt-4 not available
        self.conversations = {}  # Store conversations by session_id
        self.max_history = 20  # Keep last 20 messages for better context
        self.connected = self._test_connection()
        
    def _test_connection(self) -> bool:
        """Test if OpenAI API is accessible"""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set")
            return False
        
        # Actually test the connection
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            
            # Synchronous test for initialization
            import requests
            response = requests.post(
                self.api_url,
                headers=headers,
                json=test_payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ OpenAI API connection successful")
                return True
            else:
                logger.error(f"❌ OpenAI API connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ OpenAI API connection error: {str(e)}")
            return False
        
    def _get_system_prompt(self, farmer_context: Dict) -> str:
        """Generate system prompt with farmer context"""
        # Get current time for context
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are CAVA, an advanced agricultural AI assistant with deep expertise in farming. 
Current date and time: {current_date} at {current_time}

You're talking to a farmer with these specific details:
- Location: {farmer_context.get('location', 'Slovenia')}
- Current Weather: {farmer_context.get('weather', 'Unknown')}
- Temperature: {farmer_context.get('temperature', 'Unknown')}°C
- Humidity: {farmer_context.get('humidity', 'Unknown')}%
- Fields: {len(farmer_context.get('fields', []))} fields totaling {sum(f.get('hectares', 0) for f in farmer_context.get('fields', []))} hectares
- Active crops: {', '.join(set(f.get('crop', 'Unknown') for f in farmer_context.get('fields', [])))}

Your expertise includes:
- Crop management and cultivation techniques
- Weather impact on farming operations
- Pest and disease identification and treatment
- Precision irrigation and water management
- Optimal harvest timing and techniques
- Soil health, pH balance, and fertilization
- Sustainable farming practices
- Agricultural technology and innovation

IMPORTANT: 
- Be conversational, friendly, and vary your responses
- Ask specific questions about their crops and current challenges
- Provide practical, actionable advice tailored to their situation
- Reference their specific fields and crops when relevant
- Never repeat the same response twice
- Show personality and genuine interest in their farming success"""

        if farmer_context.get('fields'):
            prompt += "\n\nDetailed field information:\n"
            for field in farmer_context.get('fields', []):
                prompt += f"- {field['name']}: {field['crop']} ({field['hectares']} ha) - Last task: {field.get('last_task', 'Unknown')}\n"
                
        return prompt
    
    async def send_message(self, session_id: str, message: str, farmer_context: Dict) -> Dict:
        """Send message to OpenAI and get response"""
        try:
            # CONSTITUTIONAL LOGGING - Track all LLM usage
            logger.info(f"🏛️ CONSTITUTIONAL LLM CALL: session={session_id}, message_length={len(message)}")
            
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
                logger.warning(f"⚠️ NO API KEY - Using fallback for session {session_id}")
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
                        "temperature": 0.85,  # Higher for more varied responses
                        "max_tokens": 300,
                        "presence_penalty": 0.6,  # Avoid repetitive topics
                        "frequency_penalty": 0.3,  # Encourage diverse vocabulary
                        "top_p": 0.9  # Use nucleus sampling for creativity
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data['choices'][0]['message']['content']
                    
                    # Log successful LLM response
                    logger.info(f"✅ LLM RESPONSE: session={session_id}, response_length={len(ai_response)}, model={self.model}")
                    
                    # Check for duplicate response
                    if history and len(history) >= 2 and history[-1].get("content") == ai_response:
                        # Force a different response
                        logger.warning("Duplicate response detected, regenerating...")
                        messages.append({"role": "system", "content": "The previous response was identical. Please provide a completely different response with new information or perspective."})
                        
                        retry_response = await client.post(
                            self.api_url,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": self.model,
                                "messages": messages,
                                "temperature": 0.95,  # Even higher for retry
                                "max_tokens": 300,
                                "presence_penalty": 0.8,
                                "frequency_penalty": 0.5
                            },
                            timeout=30.0
                        )
                        
                        if retry_response.status_code == 200:
                            retry_data = retry_response.json()
                            ai_response = retry_data['choices'][0]['message']['content']
                    
                    # Update conversation history
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": ai_response})
                    
                    # Keep only last N messages
                    self.conversations[session_id] = history[-self.max_history:]
                    
                    return {
                        "response": ai_response,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model,
                        "connected": True
                    }
                elif response.status_code == 401:
                    logger.error("OpenAI API authentication failed - check API key")
                    return {
                        "response": "I'm having trouble connecting to my AI service. Please check that the OpenAI API key is configured correctly.",
                        "timestamp": datetime.now().isoformat(),
                        "model": "error",
                        "connected": False,
                        "error": "Authentication failed"
                    }
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return await self._get_mock_response(message, farmer_context)
                    
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            return {
                "response": "I'm having trouble connecting to the internet. Please check your connection and try again.",
                "timestamp": datetime.now().isoformat(),
                "model": "error",
                "connected": False,
                "error": "Connection failed"
            }
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "response": f"I encountered an error: {str(e)}. Please make sure the OpenAI API key is configured correctly.",
                "timestamp": datetime.now().isoformat(),
                "model": "error",
                "connected": False,
                "error": str(e)
            }
    
    async def _get_mock_response(self, message: str, farmer_context: Dict) -> Dict:
        """Generate varied mock responses when API is unavailable"""
        message_lower = message.lower()
        
        # Multiple response options for variety
        weather_responses = [
            "Looking at your local weather patterns, I see we have variable conditions ahead. The hourly forecast shows some interesting changes - have you checked the wind speeds for any planned spraying?",
            "The weather's looking quite dynamic in your area. With your fields, you might want to pay special attention to the precipitation forecast. What specific weather concerns do you have today?",
            "I notice the forecast shows changing conditions. For your crops, timing will be crucial. Are you planning any field operations in the next 24-48 hours?"
        ]
        
        harvest_responses = [
            "Harvest timing is critical for your crops. Based on typical patterns, you'll want to monitor moisture levels closely. What stage are your fields at currently?",
            "For successful harvesting, dry conditions are essential. Have you been tracking the maturity indicators in your fields? I can help you plan the optimal timing.",
            "Harvest decisions depend on many factors. With your field sizes, you might need to stagger the harvest. What's your current harvest plan?"
        ]
        
        general_responses = [
            "That's an interesting question! With your farming operation, there are several angles to consider. Could you tell me more about your specific situation?",
            "I'd be happy to help with that. Given your fields and crops, what specific challenges are you facing today?",
            "Great question! Every farm is unique. What particular aspect would be most helpful for your operation right now?"
        ]
        
        # Select appropriate response category
        if "weather" in message_lower:
            response = random.choice(weather_responses)
        elif "harvest" in message_lower:
            response = random.choice(harvest_responses)
        elif "hello" in message_lower or "hi" in message_lower:
            response = f"Hello! I'm CAVA, your agricultural assistant. I see you're managing {len(farmer_context.get('fields', []))} fields. What can I help you with today?"
        else:
            response = random.choice(general_responses)
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "mock",
            "connected": False
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