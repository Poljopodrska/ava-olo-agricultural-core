#!/usr/bin/env python3
"""
CAVA Chat Engine - OpenAI GPT-3.5 Integration
Implements intelligent agricultural conversations with GPT-3.5
Constitutional Amendment #15 Compliant - 95%+ LLM-generated intelligence
"""
import os
import logging
from typing import Dict, List, Optional
import httpx
import json
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class CAVAChatEngine:
    """CAVA chat engine powered by OpenAI GPT-3.5"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"  # Using GPT-3.5 as specified
        self.conversations = {}  # Store conversations by session_id
        self.max_history = 20  # Keep last 20 messages for context
        self.initialized = False
        self.connection_status = "not_checked"
        
    async def initialize(self) -> bool:
        """Initialize and test OpenAI connection"""
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set - CAVA cannot function")
            self.connection_status = "no_api_key"
            return False
            
        try:
            # Test connection with a minimal request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.initialized = True
                    self.connection_status = "connected"
                    logger.info(f"✅ CAVA connected to OpenAI {self.model}")
                    return True
                else:
                    self.connection_status = f"error_{response.status_code}"
                    logger.error(f"❌ OpenAI connection failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.connection_status = f"exception_{type(e).__name__}"
            logger.error(f"❌ OpenAI connection error: {str(e)}")
            return False
    
    def _get_system_prompt(self, farmer_context: Dict) -> str:
        """Generate CAVA system prompt with farmer context"""
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Extract farmer details
        farmer_name = farmer_context.get('farmer_name', 'Farmer')
        location = farmer_context.get('location', 'Slovenia')
        weather = farmer_context.get('weather', {})
        fields = farmer_context.get('fields', [])
        
        # Build field summary
        field_summary = []
        total_hectares = 0
        crops = set()
        
        for field in fields:
            hectares = field.get('hectares', 0)
            crop = field.get('crop', 'Unknown')
            total_hectares += hectares
            crops.add(crop)
            field_summary.append(f"- {field.get('name', 'Field')}: {hectares} ha of {crop}")
        
        prompt = f"""You are CAVA (Conversation Architecture for AVA), an advanced agricultural AI assistant with deep expertise in farming and agriculture. You are part of the AVA OLO system, providing intelligent farming advice to help farmers optimize their operations.

Current date and time: {current_date} at {current_time}

You're talking to {farmer_name} with these specific details:
- Location: {location}
- Current Weather: {weather.get('description', 'Unknown')}
- Temperature: {weather.get('temperature', 'Unknown')}°C
- Humidity: {weather.get('humidity', 'Unknown')}%
- Wind: {weather.get('wind_speed', 'Unknown')} m/s
- Fields: {len(fields)} fields totaling {total_hectares:.1f} hectares
- Active crops: {', '.join(crops) if crops else 'None registered'}

Field Details:
{chr(10).join(field_summary) if field_summary else 'No fields registered yet'}

Your expertise includes:
- Crop management and cultivation techniques
- Weather impact on farming operations
- Pest and disease identification and treatment
- Precision irrigation and water management
- Optimal harvest timing and techniques
- Soil health, pH balance, and fertilization
- Sustainable farming practices
- Agricultural technology and innovation
- Market timing and crop rotation strategies
- Organic farming methods

Communication style:
- Be conversational, friendly, and genuinely interested in their success
- Provide specific, actionable advice tailored to their situation
- Ask clarifying questions to better understand their challenges
- Reference their specific fields, crops, and local conditions
- Use farming terminology naturally
- Share relevant agricultural insights and tips
- Be encouraging and supportive of their farming efforts

Remember: You are CAVA, the intelligent heart of AVA OLO, dedicated to helping farmers succeed through advanced agricultural knowledge and personalized advice."""
        
        return prompt
    
    async def chat(self, session_id: str, message: str, farmer_context: Optional[Dict] = None) -> Dict:
        """Process a chat message with CAVA intelligence"""
        
        # Initialize if needed
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            return {
                "response": "I'm having trouble connecting to my knowledge base. Please check that the OpenAI API key is configured.",
                "error": "not_initialized",
                "connection_status": self.connection_status
            }
        
        # Initialize conversation history if needed
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Get system prompt with context
        system_prompt = self._get_system_prompt(farmer_context or {})
        
        # Build messages for API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in self.conversations[session_id][-self.max_history:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        try:
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
                        "temperature": 0.8,
                        "max_tokens": 500,
                        "presence_penalty": 0.6,  # Encourage variety
                        "frequency_penalty": 0.3   # Reduce repetition
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content']
                    
                    # Update conversation history
                    self.conversations[session_id].append({"role": "user", "content": message})
                    self.conversations[session_id].append({"role": "assistant", "content": ai_response})
                    
                    # Track token usage for monitoring
                    usage = result.get('usage', {})
                    
                    return {
                        "response": ai_response,
                        "session_id": session_id,
                        "model": self.model,
                        "tokens_used": usage.get('total_tokens', 0),
                        "success": True
                    }
                else:
                    error_msg = f"OpenAI API error: {response.status_code}"
                    logger.error(error_msg)
                    return {
                        "response": "I'm having trouble processing your request right now. Please try again.",
                        "error": error_msg,
                        "success": False
                    }
                    
        except httpx.TimeoutException:
            logger.error("OpenAI API timeout")
            return {
                "response": "The response is taking longer than expected. Please try again.",
                "error": "timeout",
                "success": False
            }
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {
                "response": "I encountered an error while processing your message. Please try again.",
                "error": str(e),
                "success": False
            }
    
    def get_status(self) -> Dict:
        """Get CAVA engine status"""
        return {
            "initialized": self.initialized,
            "connection_status": self.connection_status,
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "api_key_preview": self.api_key[:8] + "..." if self.api_key else "NOT_SET",
            "active_sessions": len(self.conversations),
            "total_messages": sum(len(msgs) for msgs in self.conversations.values())
        }
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, [])

# Singleton instance
_cava_engine = None

def get_cava_engine() -> CAVAChatEngine:
    """Get or create CAVA engine instance"""
    global _cava_engine
    if _cava_engine is None:
        _cava_engine = CAVAChatEngine()
    return _cava_engine

async def initialize_cava():
    """Initialize CAVA engine on startup"""
    engine = get_cava_engine()
    success = await engine.initialize()
    if success:
        logger.info("✅ CAVA Chat Engine initialized successfully")
    else:
        logger.error("❌ CAVA Chat Engine initialization failed")
    return success