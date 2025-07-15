#!/usr/bin/env python3
"""
LangChain Memory-Based Registration System
Simple checklist approach with perfect memory
"""
import uuid
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# LangChain imports
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class RegistrationChatWithMemory:
    """
    Simple registration system using LangChain memory
    No complex logic - just a checklist to complete
    """
    
    def __init__(self, openai_api_key: str):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0.1,
            openai_api_key=openai_api_key
        )
        
        # Simple checklist for LLM to follow
        self.required_data = {
            "full_name": None,
            "wa_phone_number": None, 
            "password": None,
            "farm_name": None
        }
        
        # Track password confirmation state
        self.temp_password_for_confirmation = None
    
    async def process_message(self, user_input: str) -> Dict[str, Any]:
        """Process user message with LangChain memory"""
        
        try:
            # Create checklist status for LLM
            checklist_status = self._create_checklist_display()
            
            # Get conversation history from memory
            conversation_history = self._get_conversation_summary()
            
            # Create simple system prompt with checklist
            system_prompt = f"""
You are AVA, helping a farmer register. You have PERFECT MEMORY of our conversation.

REGISTRATION CHECKLIST - Fill these 4 items:
{checklist_status}

OUR CONVERSATION SO FAR:
{conversation_history}

USER JUST SAID: "{user_input}"

SIMPLE INSTRUCTIONS:
1. Look at the checklist above - what's still MISSING?
2. If user provided info for a missing item, acknowledge it happily
3. Ask for the NEXT missing item in a friendly way
4. For password: ask once, then ask them to type it again to confirm
5. When ALL items complete, welcome them!

EXAMPLES:
- If full_name missing and user says "Peter" → "Hi Peter! What's your last name?"
- If full_name missing and user says "Peter Smith" → "Nice to meet you Peter Smith! What's your WhatsApp number?"
- If phone missing → "What's your WhatsApp number? (include country code like +385...)"
- If password missing → "Create a password (at least 6 characters):"
- If confirming password → "Please type your password again to confirm:"

Be conversational but focused on completing the checklist!
"""
            
            # Get LLM response
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = await self.llm.apredict_messages([
                HumanMessage(content=system_prompt + f"\n\nUser: {user_input}")
            ])
            
            ava_response = response.content
            
            # Save to LangChain memory
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(ava_response)
            
            # Extract data from the conversation
            self._update_checklist_from_conversation(user_input, ava_response)
            
            # Check if registration is complete
            status = "COMPLETE" if self._is_registration_complete() else "collecting"
            
            return {
                "message": ava_response,
                "extracted_data": self.required_data.copy(),
                "status": status,
                "conversation_history": self._get_message_history(),
                "last_ava_message": ava_response,
                "memory_enabled": True
            }
            
        except Exception as e:
            logger.error(f"LangChain memory error: {str(e)}")
            return {
                "message": "Hi! What's your full name? (first and last name)",
                "extracted_data": {},
                "status": "collecting",
                "conversation_history": [],
                "last_ava_message": "Hi! What's your full name? (first and last name)",
                "error": str(e)
            }
    
    def _create_checklist_display(self) -> str:
        """Create visual checklist for LLM"""
        checklist = []
        
        for field, value in self.required_data.items():
            if value:
                checklist.append(f"✅ {field}: {value}")
            else:
                checklist.append(f"❌ {field}: MISSING")
        
        if self.temp_password_for_confirmation:
            checklist.append(f"🔄 password_confirmation: WAITING FOR CONFIRMATION")
        
        return "\n".join(checklist)
    
    def _get_conversation_summary(self) -> str:
        """Get conversation history from LangChain memory"""
        if not self.memory.chat_memory.messages:
            return "This is the start of our conversation."
        
        # Get last few messages for context
        messages = self.memory.chat_memory.messages[-6:]  # Last 6 messages
        conversation = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                conversation.append(f"AVA: {msg.content}")
        
        return "\n".join(conversation)
    
    def _get_message_history(self) -> list:
        """Get message history in standard format"""
        history = []
        
        for msg in self.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content, "timestamp": datetime.now().isoformat()})
            elif isinstance(msg, AIMessage):
                history.append({"role": "ava", "content": msg.content, "timestamp": datetime.now().isoformat()})
        
        return history
    
    def _update_checklist_from_conversation(self, user_input: str, ava_response: str):
        """Simple pattern matching to update checklist"""
        
        # Look for patterns in the conversation
        conversation_text = f"{user_input} {ava_response}".lower()
        
        # Extract full name from conversation
        if not self.required_data["full_name"]:
            # Look for name patterns
            words = user_input.strip().split()
            if len(words) == 1 and words[0].isalpha():
                # Single word - wait for last name
                pass
            elif len(words) >= 2 and all(word.isalpha() or '-' in word for word in words):
                # Multiple words that look like names
                self.required_data["full_name"] = user_input.strip()
        
        # Extract phone number
        if not self.required_data["wa_phone_number"] and '+' in user_input:
            # Simple phone pattern
            if user_input.strip().startswith('+') and len(user_input.strip()) > 8:
                self.required_data["wa_phone_number"] = user_input.strip()
        
        # Handle password logic
        if not self.required_data["password"]:
            if not self.temp_password_for_confirmation:
                # Check if this looks like a password (6+ chars, not a name/phone)
                if (len(user_input.strip()) >= 6 and 
                    not user_input.strip().startswith('+') and
                    not all(word.isalpha() for word in user_input.split()) and
                    'confirm' in ava_response.lower()):
                    self.temp_password_for_confirmation = user_input.strip()
            else:
                # Check password confirmation
                if user_input.strip() == self.temp_password_for_confirmation:
                    self.required_data["password"] = self.temp_password_for_confirmation
                    self.temp_password_for_confirmation = None
                else:
                    # Password mismatch - reset
                    self.temp_password_for_confirmation = None
        
        # Extract farm name (last item)
        if (self.required_data["full_name"] and 
            self.required_data["wa_phone_number"] and 
            self.required_data["password"] and 
            not self.required_data["farm_name"]):
            # This input is probably the farm name
            self.required_data["farm_name"] = user_input.strip()
    
    def _is_registration_complete(self) -> bool:
        """Check if all required data is collected"""
        return all(value is not None for value in self.required_data.values())


# Global memory storage for different conversations
_conversation_memories: Dict[str, RegistrationChatWithMemory] = {}

def get_conversation_memory(conversation_id: str, openai_api_key: str) -> RegistrationChatWithMemory:
    """Get or create memory for a conversation"""
    if conversation_id not in _conversation_memories:
        _conversation_memories[conversation_id] = RegistrationChatWithMemory(openai_api_key)
    return _conversation_memories[conversation_id]

def clear_conversation_memory(conversation_id: str):
    """Clear memory for a conversation"""
    if conversation_id in _conversation_memories:
        del _conversation_memories[conversation_id]