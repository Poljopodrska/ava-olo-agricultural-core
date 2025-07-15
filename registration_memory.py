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
            
            # Constitutional system prompt with data awareness
            system_prompt = f"""
You are AVA, constitutional agricultural assistant with PERFECT DATA AWARENESS.

{checklist_status}

OUR CONVERSATION SO FAR:
{conversation_history}

USER JUST SAID: "{user_input}"

CONSTITUTIONAL INTELLIGENCE:
1. ANALYZE the checklist above - what data do you ALREADY HAVE vs STILL NEED?
2. NEVER re-ask for data marked with ✅ [COLLECTED]
3. If user provides new data, acknowledge and update mentally
4. Ask ONLY for the NEXT missing item from the checklist
5. Be smart - if you have "Peter" and they say "Knaflič", you now have full name "Peter Knaflič"

SMART EXAMPLES:
- Have "Peter", user says "Knaflič" → "Nice to meet you Peter Knaflič! What's your WhatsApp number?"
- Already have name+phone, user gives anything → "Thanks! Now create a password:"
- Have everything → "🎉 Welcome to AVA OLO!"

CRITICAL: Look at the checklist. Don't ask for data you already have!
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
        """Create constitutional visual checklist for LLM"""
        checklist = []
        
        # Constitutional data awareness format
        checklist.append("DATA COLLECTION CHECKLIST:")
        
        for field, value in self.required_data.items():
            if value:
                checklist.append(f"✅ {field}: {value} [COLLECTED]")
            else:
                checklist.append(f"❌ {field}: STILL NEEDED")
        
        if self.temp_password_for_confirmation:
            checklist.append(f"🔄 password_confirmation: WAITING FOR CONFIRMATION")
        
        checklist.append("\nCRITICAL RULES:")
        checklist.append("- NEVER ask for data you already have (marked with ✅)")
        checklist.append("- ONLY ask for the NEXT missing item (marked with ❌)")
        checklist.append("- If ALL data collected → complete registration")
        
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
        """Constitutional intelligent data extraction"""
        
        # Extract full name with smart combination logic
        if not self.required_data["full_name"]:
            words = user_input.strip().split()
            
            # Check if this completes a partial name from memory
            name_from_memory = self._extract_partial_name_from_memory()
            
            if name_from_memory and len(words) == 1 and words[0].isalpha():
                # Complete the name: "Peter" + "Knaflič" = "Peter Knaflič"
                self.required_data["full_name"] = f"{name_from_memory} {words[0]}"
            elif len(words) >= 2 and all(word.replace('-', '').isalpha() for word in words):
                # Full name provided at once
                self.required_data["full_name"] = user_input.strip()
        
        # Extract phone number
        if not self.required_data["wa_phone_number"] and '+' in user_input:
            phone = user_input.strip()
            if phone.startswith('+') and len(phone) > 8:
                self.required_data["wa_phone_number"] = phone
        
        # Constitutional password handling
        if not self.required_data["password"]:
            if not self.temp_password_for_confirmation:
                # First password entry
                if (len(user_input.strip()) >= 6 and 
                    not user_input.strip().startswith('+') and
                    not all(word.isalpha() for word in user_input.split())):
                    self.temp_password_for_confirmation = user_input.strip()
            else:
                # Password confirmation
                if user_input.strip() == self.temp_password_for_confirmation:
                    self.required_data["password"] = self.temp_password_for_confirmation
                    self.temp_password_for_confirmation = None
                else:
                    self.temp_password_for_confirmation = None
        
        # Extract farm name (when other data is complete)
        if (self.required_data["full_name"] and 
            self.required_data["wa_phone_number"] and 
            self.required_data["password"] and 
            not self.required_data["farm_name"] and
            len(user_input.strip()) > 0):
            self.required_data["farm_name"] = user_input.strip()
    
    def _extract_partial_name_from_memory(self) -> Optional[str]:
        """Extract partial first name from conversation memory"""
        for msg in self.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                words = msg.content.strip().split()
                if len(words) == 1 and words[0].isalpha() and len(words[0]) > 1:
                    # Found a single name word - likely first name
                    return words[0]
        return None
    
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