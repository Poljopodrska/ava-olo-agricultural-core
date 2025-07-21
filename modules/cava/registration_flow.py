#!/usr/bin/env python3
"""
CAVA Registration Flow
Handles conversational registration for new farmers
"""
from typing import Dict, Optional, Tuple
import re
from datetime import datetime
import asyncio

class RegistrationFlow:
    """Manages the conversational registration flow"""
    
    STAGES = {
        "greeting": {
            "prompts": [
                "👋 Hello! I'm CAVA, your AVA OLO agricultural assistant.",
                "Welcome to AVA OLO! I'll help you create your farmer account.",
                "Let's get you registered! I'll guide you through a few simple questions."
            ],
            "next_stage": "name"
        },
        "name": {
            "prompts": [
                "What's your name? 🌱",
                "May I have your name, please?",
                "Let's start with your name:"
            ],
            "validation": "name",
            "field": "name",
            "next_stage": "whatsapp"
        },
        "whatsapp": {
            "prompts": [
                "📱 What's your WhatsApp number? (Include country code, e.g., +359123456789)",
                "Please share your WhatsApp number with country code:",
                "What WhatsApp number should we use for your account?"
            ],
            "validation": "whatsapp",
            "field": "whatsapp_number",
            "next_stage": "email"
        },
        "email": {
            "prompts": [
                "📧 What's your email address?",
                "Please provide your email:",
                "What email should we use for important notifications?"
            ],
            "validation": "email",
            "field": "email",
            "next_stage": "password"
        },
        "password": {
            "prompts": [
                "🔐 Please create a password (at least 8 characters):",
                "Choose a secure password for your account:",
                "Create a password you'll remember (8+ characters):"
            ],
            "validation": "password",
            "field": "password",
            "next_stage": "confirm_password"
        },
        "confirm_password": {
            "prompts": [
                "🔐 Please type your password again to confirm:",
                "Confirm your password:",
                "One more time - enter your password again:"
            ],
            "validation": "confirm_password",
            "field": "confirm_password",
            "next_stage": "complete"
        },
        "complete": {
            "prompts": [
                "🎉 Perfect! Your account is ready. Click 'Complete Registration' to start farming with AVA OLO!",
                "✅ All set! You're registered. Click 'Complete Registration' to access your dashboard!",
                "🌾 Welcome to AVA OLO! Click 'Complete Registration' to begin your journey!"
            ]
        }
    }
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def get_or_create_session(self, farmer_id: str) -> Dict:
        """Get existing session or create new one"""
        if farmer_id not in self.sessions:
            self.sessions[farmer_id] = {
                "stage": "greeting",
                "data": {},
                "history": [],
                "created_at": datetime.utcnow(),
                "attempts": {}
            }
        return self.sessions[farmer_id]
    
    def validate_input(self, validation_type: str, value: str, session: Dict) -> Tuple[bool, Optional[str]]:
        """Validate user input based on type"""
        if validation_type == "name":
            if len(value.strip()) < 2:
                return False, "Name must be at least 2 characters long"
            if not re.match(r'^[a-zA-Z\s\-\'\.]+$', value):
                return False, "Please use only letters, spaces, hyphens, and apostrophes"
            return True, None
        
        elif validation_type == "whatsapp":
            # Remove all non-digits
            digits_only = re.sub(r'\D', '', value)
            
            # Check length
            if len(digits_only) < 10 or len(digits_only) > 15:
                return False, "WhatsApp number should be 10-15 digits with country code"
            
            # Should not start with 0
            if digits_only.startswith('0'):
                return False, "Please include country code (e.g., +359 for Bulgaria)"
                
            return True, None
        
        elif validation_type == "email":
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(value):
                return False, "Please enter a valid email address"
            return True, None
        
        elif validation_type == "password":
            if len(value) < 8:
                return False, "Password must be at least 8 characters long"
            return True, None
        
        elif validation_type == "confirm_password":
            original_password = session["data"].get("password", "")
            if value != original_password:
                return False, "Passwords don't match. Please try again"
            return True, None
        
        return True, None
    
    def format_whatsapp_number(self, phone: str) -> str:
        """Format WhatsApp number to standard format"""
        digits_only = re.sub(r'\D', '', phone)
        
        # Add + prefix for international format
        if not digits_only.startswith('+'):
            return '+' + digits_only
        return digits_only
    
    async def process_message(self, farmer_id: str, message: str) -> Dict:
        """Process a message from the farmer"""
        session = self.get_or_create_session(farmer_id)
        
        # Add message to history
        session["history"].append({
            "type": "user",
            "message": message,
            "timestamp": datetime.utcnow()
        })
        
        current_stage = self.STAGES[session["stage"]]
        
        # If we're in greeting stage, just move to next
        if session["stage"] == "greeting":
            session["stage"] = current_stage["next_stage"]
            next_stage = self.STAGES[session["stage"]]
            response = next_stage["prompts"][0]
            
            session["history"].append({
                "type": "assistant",
                "message": response,
                "timestamp": datetime.utcnow()
            })
            
            return {
                "response": response,
                "registration_complete": False,
                "stage": session["stage"]
            }
        
        # If we're in complete stage, registration is done
        if session["stage"] == "complete":
            return {
                "response": "Your registration is complete! Click 'Complete Registration' to continue.",
                "registration_complete": True,
                "stage": "complete",
                "registration_data": session["data"]
            }
        
        # Validate input for current stage
        if "validation" in current_stage:
            is_valid, error_msg = self.validate_input(
                current_stage["validation"],
                message,
                session
            )
            
            if not is_valid:
                # Track attempts
                stage_key = session["stage"]
                session["attempts"][stage_key] = session["attempts"].get(stage_key, 0) + 1
                
                # Provide helpful error message
                if session["attempts"][stage_key] >= 3:
                    response = f"❌ {error_msg}\n\n💡 Need help? {current_stage['prompts'][1]}"
                else:
                    response = f"❌ {error_msg}\n\nPlease try again:"
                
                session["history"].append({
                    "type": "assistant",
                    "message": response,
                    "timestamp": datetime.utcnow()
                })
                
                return {
                    "response": response,
                    "registration_complete": False,
                    "stage": session["stage"],
                    "error": True
                }
        
        # Store valid data
        if "field" in current_stage:
            field_value = message.strip()
            
            # Special formatting for WhatsApp number
            if current_stage["field"] == "whatsapp_number":
                field_value = self.format_whatsapp_number(field_value)
            
            session["data"][current_stage["field"]] = field_value
        
        # Move to next stage
        session["stage"] = current_stage["next_stage"]
        
        # Generate response for next stage
        if session["stage"] in self.STAGES:
            next_stage = self.STAGES[session["stage"]]
            
            # Personalize response
            if session["stage"] == "whatsapp" and "name" in session["data"]:
                response = f"Nice to meet you, {session['data']['name']}! 📱 {next_stage['prompts'][0]}"
            elif session["stage"] == "complete":
                name = session["data"].get("name", "")
                response = f"🎉 Congratulations {name}! {next_stage['prompts'][0]}"
            else:
                response = next_stage["prompts"][0]
        else:
            response = "Registration complete!"
        
        session["history"].append({
            "type": "assistant",
            "message": response,
            "timestamp": datetime.utcnow()
        })
        
        return {
            "response": response,
            "registration_complete": session["stage"] == "complete",
            "stage": session["stage"],
            "progress": self._calculate_progress(session["stage"])
        }
    
    def _calculate_progress(self, stage: str) -> int:
        """Calculate registration progress percentage"""
        stage_order = ["greeting", "name", "whatsapp", "email", "password", "confirm_password", "complete"]
        try:
            index = stage_order.index(stage)
            return int((index / (len(stage_order) - 1)) * 100)
        except ValueError:
            return 0
    
    def get_session_data(self, farmer_id: str) -> Optional[Dict]:
        """Get registration data for a session"""
        if farmer_id in self.sessions:
            return self.sessions[farmer_id]["data"]
        return None
    
    def clear_session(self, farmer_id: str):
        """Clear a session after registration"""
        if farmer_id in self.sessions:
            del self.sessions[farmer_id]