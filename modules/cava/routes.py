#!/usr/bin/env python3
"""
CAVA API Routes
Handles conversational AI endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging
import os
import re

from modules.cava.registration_flow import RegistrationFlow
from modules.cava.natural_registration import NaturalRegistrationFlow
from modules.cava.true_cava_registration import TrueCAVARegistration
from modules.cava.simple_chat import SimpleRegistrationChat
from modules.cava.pure_chat import PureChat
from modules.cava.enhanced_cava_registration import EnhancedCAVARegistration
from modules.cava.cava_registration_engine import get_cava_registration_engine
from modules.auth.routes import create_farmer_account, get_password_hash

# Import the WORKING LLM client from main chat
from modules.chat.openai_key_manager import get_openai_client

# Import version for debug info
from modules.core.config import VERSION

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["cava"])

# Initialize registration flow managers
registration_flow = RegistrationFlow()  # Keep old flow for compatibility
natural_registration = NaturalRegistrationFlow()  # New natural flow
true_cava = TrueCAVARegistration()  # True CAVA - no hardcoding
simple_chat = SimpleRegistrationChat()  # Step 1 - Simple chat only
pure_chat = PureChat()  # Pure chat - NO validation or hardcoding
enhanced_cava = EnhancedCAVARegistration()  # Enhanced CAVA with full validation

# Setup logging
logger = logging.getLogger(__name__)

# Registration sessions storage (in-memory for now)
registration_sessions = {}

def detect_question_type(llm_response: str) -> str:
    """Detect what the LLM is asking for based on its response"""
    response_lower = llm_response.lower()
    
    if "first name" in response_lower or "what's your name" in response_lower or "called" in response_lower:
        return "first_name"
    elif "last name" in response_lower or "surname" in response_lower or "family name" in response_lower:
        return "last_name"
    elif "whatsapp" in response_lower or "phone" in response_lower or "number" in response_lower:
        return "whatsapp"
    elif "password" in response_lower:
        return "password"
    else:
        return "unknown"

def extract_registration_data(user_message: str, last_question_type: str = "", collected_data: Dict[str, str] = None) -> Dict[str, str]:
    """Extract registration data based on conversation flow and what was just asked"""
    if collected_data is None:
        collected_data = {}
    
    extracted = {}
    message = user_message.strip()
    
    # Simple single-word responses to specific questions
    if last_question_type == "first_name" and not collected_data.get('first_name'):
        # User likely gave their first name
        words = message.split()
        if len(words) == 1 and words[0][0].isupper():
            extracted['first_name'] = words[0].capitalize()
        elif len(words) <= 2 and message[0].isupper():
            # Handle "My name is Peter" or just "Peter"
            name_match = re.search(r'(?:my name is |i am |call me )?([A-Z][a-zA-ZÀ-ÿ]+)', message, re.IGNORECASE)
            if name_match:
                extracted['first_name'] = name_match.group(1).capitalize()
    
    elif last_question_type == "last_name" and not collected_data.get('last_name'):
        # User likely gave their last name
        words = message.split()
        if len(words) == 1 and words[0][0].isupper():
            extracted['last_name'] = words[0].capitalize()
        elif len(words) <= 2:
            # Handle various last name formats
            name_match = re.search(r'([A-Z][a-zA-ZÀ-ÿčšžđćž]+)', message, re.IGNORECASE)
            if name_match:
                extracted['last_name'] = name_match.group(1).capitalize()
    
    elif last_question_type == "whatsapp" and not collected_data.get('whatsapp'):
        # Extract phone number
        phone_patterns = [
            r'\+\d{1,4}\s?\d{6,14}',  # +country code
            r'\d{9,15}',  # Simple number
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, message.replace(' ', '').replace('-', ''))
            if match:
                phone = match.group()
                if not phone.startswith('+'):
                    phone = '+359' + phone.lstrip('0')  # Default to Bulgaria
                extracted['whatsapp'] = phone
                break
    
    elif last_question_type == "password" and not collected_data.get('password'):
        # Extract password
        words = message.split()
        for word in words:
            if len(word) >= 8:
                extracted['password'] = word
                break
    
    # Fallback: Try to extract from common patterns regardless of question type
    if not extracted:
        # Look for explicit statements
        patterns = [
            (r"my name is ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
            (r"i am ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
            (r"call me ([A-Z][a-zA-ZÀ-ÿ]+)", 'first_name'),
        ]
        
        for pattern, field_type in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and not collected_data.get(field_type):
                extracted[field_type] = match.group(1).capitalize()
                break
    
    return extracted

def is_registration_complete(collected_data: Dict[str, str]) -> bool:
    """Check if all required fields are collected"""
    required_fields = ['first_name', 'last_name', 'whatsapp', 'password']
    return all(field in collected_data and collected_data[field] for field in required_fields)

def determine_registration_step(collected: Dict[str, str]) -> str:
    """Determine current registration step"""
    if not collected.get('first_name'):
        return "collecting_first_name"
    elif not collected.get('last_name'):
        return "collecting_last_name"
    elif not collected.get('whatsapp'):
        return "collecting_whatsapp"
    elif not collected.get('password'):
        return "collecting_password"
    else:
        return "registration_complete"

def get_next_action(collected: Dict[str, str]) -> str:
    """Get the next action to take"""
    if not collected.get('first_name'):
        return "Ask for their first name"
    elif not collected.get('last_name'):
        return "Ask for their last name"
    elif not collected.get('whatsapp'):
        return "Ask for their WhatsApp number with country code"
    elif not collected.get('password'):
        return "Ask them to create a password"
    else:
        return "Complete the registration"

def extract_question_type_from_message(message: str) -> str:
    """Extract what type of question was asked from a message"""
    msg_lower = message.lower()
    
    if any(phrase in msg_lower for phrase in ["first name", "your name", "may i have your name", "what's your name", "what is your name"]):
        return "first_name"
    elif any(phrase in msg_lower for phrase in ["last name", "surname", "family name"]):
        return "last_name"
    elif any(phrase in msg_lower for phrase in ["whatsapp", "phone", "number", "contact"]):
        return "whatsapp"
    elif any(phrase in msg_lower for phrase in ["password", "create a password", "choose a password"]):
        return "password"
    else:
        return "unknown"

def map_question_to_data_type(question_type: str) -> str:
    """Map question type to expected data type"""
    mapping = {
        "first_name": "first name",
        "last_name": "last name",
        "whatsapp": "WhatsApp number",
        "password": "password",
        "unknown": "response"
    }
    return mapping.get(question_type, "response")

def interpret_user_response(user_message: str, last_question_type: str) -> str:
    """Interpret what the user's response means"""
    if last_question_type == "first_name":
        return f"User is providing their first name: '{user_message}'"
    elif last_question_type == "last_name":
        return f"User is providing their last name: '{user_message}'"
    elif last_question_type == "whatsapp":
        return f"User is providing their WhatsApp number: '{user_message}'"
    elif last_question_type == "password":
        return "User is setting their password"
    else:
        return "User is responding to the conversation"

def generate_specific_instruction(collected: Dict[str, str], user_message: str) -> str:
    """Generate specific instruction for the LLM"""
    step = determine_registration_step(collected)
    
    if step == "collecting_first_name":
        return "Acknowledge their response as their first name and ask for their last name"
    elif step == "collecting_last_name":
        return "Acknowledge their response as their last name and ask for their WhatsApp number"
    elif step == "collecting_whatsapp":
        return "Acknowledge their WhatsApp number and ask them to create a password"
    elif step == "collecting_password":
        return "Acknowledge that their password is set and complete the registration"
    else:
        return "Complete the registration and welcome them"

@router.post("/registration/cava")
async def cava_registration_chat(request: Request) -> JSONResponse:
    """Handle CAVA registration chat messages using WORKING LLM from main chat"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "") or data.get("farmer_id", "")  # Accept both session_id and farmer_id
        language = data.get("language", "en")
        
        logger.info(f"🏛️ REGISTRATION LLM: message='{message}', session_id='{session_id}'")
        
        print("=" * 80)
        print("🚨 ACTUAL REGISTRATION ENDPOINT HIT - modules/cava/routes.py")
        print(f"📨 Request data: {data}")
        print(f"📨 Message: '{message}', Session ID: '{session_id}'")
        print("=" * 80)
        
        if not session_id:
            print("❌ ERROR: No session_id provided")
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Use the SAME working LLM client from main chat
        print("🔍 Step 1: Getting OpenAI client...")
        client = get_openai_client()
        
        if not client:
            print("❌ ERROR: Could not create OpenAI client")
            logger.error("Could not create OpenAI client for registration")
            return JSONResponse(
                status_code=500,
                content={
                    "response": "Registration system is temporarily unavailable. Please try again later.",
                    "error": True,
                    "error_type": "llm_unavailable"
                }
            )
        else:
            print("✅ OpenAI client created successfully")
        
        # Get or create session
        session = registration_sessions.get(session_id, {
            "messages": [],
            "collected_data": {},
            "language": language,
            "last_question_type": "unknown"
        })
        
        # Build messages for registration context with smart memory tracking
        collected = session.get("collected_data", {})
        
        # Create checkmark status for system prompt
        status_first = '✅ ' + collected.get('first_name', '') if collected.get('first_name') else '❌ NOT YET'
        status_last = '✅ ' + collected.get('last_name', '') if collected.get('last_name') else '❌ NOT YET'
        status_whatsapp = '✅ ' + collected.get('whatsapp', '') if collected.get('whatsapp') else '❌ NOT YET'
        status_password = '✅ SET' if collected.get('password') else '❌ NOT YET'
        
        # Get conversation context - with error handling
        try:
            current_step = determine_registration_step(collected)
            next_action = get_next_action(collected)
            
            # Get last bot and user messages
            last_bot_message = session["messages"][-2]["content"] if len(session["messages"]) >= 2 and session["messages"][-2]["role"] == "assistant" else "Hello! I'm AVA, here to help you register."
            last_user_message = message
            last_question_type = extract_question_type_from_message(last_bot_message)
            expected_data_type = map_question_to_data_type(last_question_type)
            interpretation = interpret_user_response(last_user_message, last_question_type)
            specific_instruction = generate_specific_instruction(collected, last_user_message)
        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            # Fallback values
            current_step = "unknown"
            next_action = "continue registration"
            last_bot_message = "Hello"
            last_user_message = message
            last_question_type = "unknown"
            expected_data_type = "response"
            interpretation = "User is responding"
            specific_instruction = "Continue with registration"
        
        # Create comprehensive system prompt with error handling
        try:
            system_content = f"""You are AVA, an agricultural assistant helping farmers register. You must collect registration information in a natural, conversational way.

🎯 YOUR MISSION: Collect these 4 pieces of information:
1. First name (given name, personal name)
2. Last name (family name, surname)
3. WhatsApp number (with country code)
4. Password (minimum 8 characters)

📋 CURRENT REGISTRATION STATUS:
- First name: {collected.get('first_name', '❌ NOT COLLECTED')}
- Last name: {collected.get('last_name', '❌ NOT COLLECTED')}
- WhatsApp: {collected.get('whatsapp', '❌ NOT COLLECTED')}
- Password: {'✅ SET' if collected.get('password') else '❌ NOT COLLECTED'}

🧠 UNDERSTANDING NAMES - CRITICAL RULES:
1. First name = Given name = Personal name (e.g., Peter, Maria, Raj, Yuki)
2. Last name = Family name = Surname (e.g., Smith, Knaflič, Patel, Yamamoto)
3. After asking "What is your first name?" → The response IS their first name
4. After asking "What is your last name?" → The response IS their last name
5. NEVER mix these up!

📝 CONVERSATION CONTEXT:
Last question you asked: {last_bot_message}
User's last response: {last_user_message}
What this means: {interpretation}

🌍 CULTURAL AWARENESS:
- Western format: [First] [Last] (Peter Knaflič)
- Asian format: [Last] [First] (Yamamoto Yuki) - but users will adapt to your questions
- Spanish/Portuguese: May have multiple surnames (García López)
- Single name cultures: Some use only one name
- If someone gives multiple names after you ask for "first name", take the first word
- If someone gives multiple names after you ask for "last name", take all as last name

💬 CONVERSATION RULES:
1. Ask for ONE piece of information at a time
2. Acknowledge what they gave you before asking the next
3. Use natural, warm language
4. If they ask off-topic questions, politely redirect: "I'd love to help with that after we complete your registration!"
5. Confirm understanding: "Great! So your [first/last] name is X"

🔄 REGISTRATION FLOW:
Current step: {current_step}
Next action: {next_action}

Step 1: If no first name → Ask: "What is your first name?"
Step 2: If no last name → Ask: "Thank you [first_name]! What is your last name?"
Step 3: If no WhatsApp → Ask: "What is your WhatsApp number? Please include country code (like +386)"
Step 4: If no password → Ask: "Please create a password (minimum 8 characters)"
Step 5: All collected → Say: "Registration complete! Welcome to AVA, [first_name]!"

⚠️ CRITICAL INSTRUCTIONS:
- You just asked for: {last_question_type}
- The user's response "{last_user_message}" is their: {expected_data_type}
- Extract and acknowledge this EXACT data type
- Do NOT re-interpret or second-guess

🚫 COMMON MISTAKES TO AVOID:
- Asking for the same information twice
- Confusing first and last names
- Not acknowledging what user provided
- Being too formal (remember, these are farmers!)
- Asking multiple questions at once

✅ GOOD EXAMPLES:
User: "Peter"
You: "Nice to meet you, Peter! What is your last name?"

User: "Knaflič"  
You: "Thank you, Peter Knaflič! What is your WhatsApp number? Please include your country code."

User: "can you help me grow mangoes?"
You: "I'd be happy to help with mango growing after we finish your registration! What is your WhatsApp number?"

❌ BAD EXAMPLES:
User: "Peter"
You: "What is your first name?" (Already gave it!)

User: "Knaflič"
You: "Thank you for your first name" (This was their last name!)

🎯 YOUR IMMEDIATE TASK:
Based on the conversation above, {specific_instruction}

Remember: Be warm, natural, and helpful. These are farmers who need assistance, not tech experts!

Respond in {language} if possible."""
        except Exception as e:
            logger.error(f"Error building comprehensive prompt: {e}")
            # Fallback to simple prompt
            system_content = f"""You are AVA's registration assistant helping farmers register.

CURRENT STATUS:
- First name: {status_first}
- Last name: {status_last}
- WhatsApp: {status_whatsapp}
- Password: {status_password}

Please collect the missing information one at a time. Be friendly and conversational.
For WhatsApp, require country code (+359, +386, etc.).
For password, require minimum 8 characters.

Respond in {language} if possible."""

        messages = [{"role": "system", "content": system_content}]
        
        # Add recent conversation history
        for msg in session["messages"][-6:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            print("🔍 Step 2: Calling OpenAI API...")
            print(f"   Model: gpt-3.5-turbo")
            print(f"   Messages count: {len(messages)}")
            
            # Call OpenAI using GPT-3.5-turbo for cost savings (15x cheaper than GPT-4)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4 for cost optimization
                messages=messages,
                temperature=0.7,
                max_tokens=300  # Reduced for efficiency
            )
            
            llm_response = response.choices[0].message.content
            print(f"✅ OpenAI API call successful")
            print(f"   Response: {llm_response[:200]}...")
            logger.info(f"✅ REGISTRATION LLM (GPT-3.5): {llm_response[:100]}...")
            
            # Add critical logging for debugging deployment issues
            logger.critical(f"🚨 PROMPT CHECK: Using comprehensive prompt: {'UNDERSTANDING NAMES' in system_content}")
            logger.critical(f"🚨 PROMPT LENGTH: {len(system_content)} chars")
            logger.critical(f"🚨 VERSION: {VERSION}")
            logger.critical(f"🚨 LAST USER MSG: '{message}'")
            logger.critical(f"🚨 DETECTED QUESTION TYPE: {last_question_type}")
            logger.critical(f"🚨 EXPECTED DATA TYPE: {expected_data_type}")
            
            # FIRST: Extract data from user input using previous question context
            previous_question_type = session.get("last_question_type", "unknown")
            collected_data = session.get("collected_data", {})
            extracted_data = extract_registration_data(message, previous_question_type, collected_data)
            
            # Update collected data with extracted information
            for field, value in extracted_data.items():
                if value and not collected_data.get(field):  # Only add if not already collected
                    collected_data[field] = value
                    logger.info(f"🎯 EXTRACTED {field}: {value} (was asking for: {previous_question_type})")
            
            # SECOND: Detect what the LLM is now asking for (for next user response)
            current_question_type = detect_question_type(llm_response)
            
            # Update session with new data
            session["messages"].append({"role": "user", "content": message})
            session["messages"].append({"role": "assistant", "content": llm_response})
            session["collected_data"] = collected_data
            session["last_question_type"] = current_question_type
            
            logger.info(f"🔄 FLOW: Asked for {previous_question_type} → Now asking for {current_question_type}")
            
            # Check if registration is complete
            is_complete = is_registration_complete(collected_data)
            
            # Save updated session
            registration_sessions[session_id] = session
            
            result = {
                "response": llm_response,
                "registration_complete": is_complete,
                "llm_used": True,
                "model_used": "gpt-3.5-turbo",
                "constitutional_compliance": True,
                "session_id": session_id,
                "collected_data": collected_data,
                "progress_percentage": (len([v for v in collected_data.values() if v]) / 4) * 100,
                "debug": {
                    "version": VERSION,
                    "prompt_type": "comprehensive" if "UNDERSTANDING NAMES" in system_content else "old",
                    "last_question_was": last_question_type,
                    "detected_as": current_question_type,
                    "prompt_length": len(system_content),
                    "has_comprehensive_prompt": "UNDERSTANDING NAMES" in system_content
                }
            }
            
            return JSONResponse(content=result)
            
        except Exception as e:
            print("=" * 80)
            print("❌ OPENAI API CALL FAILED")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            print("=" * 80)
            
            logger.error(f"Registration LLM error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "response": f"DEBUG: OpenAI call failed: {type(e).__name__}: {str(e)}",
                    "error": True,
                    "error_type": "llm_processing_error",
                    "error_details": str(e)
                }
            )
        
    except Exception as e:
        print("=" * 80)
        print("❌ MAIN EXCEPTION HANDLER")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        print("=" * 80)
        
        logger.error(f"CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": f"DEBUG: Main error: {type(e).__name__}: {str(e)}",
                "registration_complete": False,
                "error": True,
                "error_details": str(e),
                "error_type": type(e).__name__
            }
        )

@router.get("/registration/llm-test")
async def test_registration_llm():
    """Test if registration can use the same LLM as main chat"""
    try:
        client = get_openai_client()
        
        if not client:
            return {
                "test": "failed",
                "error": "Could not get OpenAI client",
                "same_as_chat": False
            }
        
        # Test with registration-like message
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a registration assistant. When someone says they want to register, ask for their first name."},
                {"role": "user", "content": "I want to register"}
            ],
            max_tokens=100
        )
        
        return {
            "test": "success",
            "response": response.choices[0].message.content,
            "model": "gpt-4",
            "same_as_chat": True,
            "client_source": "modules.chat.openai_key_manager"
        }
        
    except Exception as e:
        return {
            "test": "failed",
            "error": str(e),
            "same_as_chat": False
        }

@router.get("/registration/cava/session/{farmer_id}")
async def get_registration_session(farmer_id: str) -> JSONResponse:
    """Get current registration session status"""
    session_data = registration_flow.get_session_data(farmer_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active registration session"
        })
    
    # Don't expose password in response
    safe_data = {k: v for k, v in session_data.items() if k not in ["password", "confirm_password"]}
    
    return JSONResponse(content={
        "exists": True,
        "data": safe_data,
        "fields_collected": len(safe_data)
    })

@router.delete("/registration/cava/session/{farmer_id}")
async def clear_registration_session(farmer_id: str) -> JSONResponse:
    """Clear a registration session"""
    registration_flow.clear_session(farmer_id)
    
    return JSONResponse(content={
        "success": True,
        "message": "Registration session cleared"
    })

@router.post("/registration/cava/natural")
async def natural_registration_chat(request: Request) -> JSONResponse:
    """Handle natural CAVA registration chat messages"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through natural registration flow
        result = await natural_registration.process_message(session_id, message)
        
        # If registration is complete, prepare account creation data
        if result.get("registration_complete") and "collected_data" in result:
            collected = result["collected_data"]
            
            # Map collected fields to database fields
            registration_data = {
                "manager_name": collected.get("first_name", ""),
                "manager_last_name": collected.get("last_name", ""),
                "wa_phone_number": collected.get("whatsapp", "")
            }
            
            result["registration_data"] = registration_data
            # Note: Actual account creation should be done by the frontend
            # after user confirms and adds any additional required fields
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Natural CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True,
                "error_message": str(e)
            }
        )

@router.get("/registration/cava/natural/session/{session_id}")
async def get_natural_registration_session(session_id: str) -> JSONResponse:
    """Get current natural registration session status"""
    session_data = natural_registration.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active registration session"
        })
    
    missing_fields = natural_registration.get_missing_fields(session_data)
    
    return JSONResponse(content={
        "exists": True,
        "collected_data": session_data,
        "missing_fields": missing_fields,
        "registration_complete": len(missing_fields) == 0
    })

@router.delete("/registration/cava/natural/session/{session_id}")
async def clear_natural_registration_session(session_id: str) -> JSONResponse:
    """Clear a natural registration session"""
    natural_registration.clear_session(session_id)
    
    return JSONResponse(content={
        "success": True,
        "message": "Natural registration session cleared"
    })

@router.post("/registration/cava/true")
async def true_cava_registration(request: Request) -> JSONResponse:
    """Handle TRUE CAVA registration - pure LLM conversation"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through true CAVA
        result = await true_cava.process_message(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"True CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True
            }
        )

@router.get("/registration/cava/true/session/{session_id}")
async def get_true_cava_session(session_id: str) -> JSONResponse:
    """Get true CAVA session status"""
    session_data = true_cava.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active session"
        })
    
    return JSONResponse(content={
        "exists": True,
        "collected_data": session_data,
        "registration_complete": all(session_data.values())
    })

@router.post("/registration/cava/enhanced")
async def enhanced_cava_registration(request: Request) -> JSONResponse:
    """Enhanced CAVA registration with full validation and language support"""
    try:
        data = await request.json()
        
        # Extract required fields
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Process message through enhanced CAVA
        result = await enhanced_cava.process_message(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Enhanced CAVA registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "I'm having trouble understanding. Could you please try again?",
                "registration_complete": False,
                "error": True
            }
        )

@router.get("/registration/cava/enhanced/session/{session_id}")
async def get_enhanced_cava_session(session_id: str) -> JSONResponse:
    """Get enhanced CAVA session status"""
    session_data = enhanced_cava.get_session_data(session_id)
    
    if not session_data:
        return JSONResponse(content={
            "exists": False,
            "message": "No active session"
        })
    
    return JSONResponse(content={
        "exists": True,
        "session_data": session_data,
        "registration_complete": session_data.get("complete", False)
    })

@router.post("/registration/chat")
async def registration_chat(request: Request) -> JSONResponse:
    """Simple chat endpoint - Step 1 of CAVA registration"""
    try:
        data = await request.json()
        
        session_id = data.get("session_id", "")
        message = data.get("message", "").strip()
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Pure chat - NO validation or hardcoding
        result = await pure_chat.chat(session_id, message)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Registration chat error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "Sorry, I'm having trouble right now. Please try again.",
                "error": True
            }
        )

@router.get("/registration/debug")
async def debug_registration():
    """Debug endpoint to verify OpenAI API status - CONSTITUTIONAL REQUIREMENT"""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "openai_key_set": bool(openai_key),
        "key_prefix": openai_key[:10] if openai_key else None,
        "cava_mode": "llm" if openai_key else "fallback"
    }

@router.get("/registration/llm-status")
async def check_llm_status(request: Request):
    """DIAGNOSTIC: Check actual LLM engine status in production"""
    from modules.core.config import VERSION
    from datetime import datetime
    import sys
    
    # Check if engine is loaded
    engine_error = None
    try:
        from modules.cava.cava_registration_engine import get_cava_registration_engine
        engine_loaded = True
        try:
            engine = get_cava_registration_engine()
            engine_initialized = True
            engine_has_key = bool(engine.api_key)
        except Exception as e:
            engine_initialized = False
            engine_has_key = False
            engine_error = str(e)
    except Exception as e:
        engine_loaded = False
        engine_initialized = False
        engine_has_key = False
        engine_error = str(e)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "🚨_DIAGNOSTIC_REPORT": "LLM Registration Status",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "endpoint_path": str(request.url.path),
        "environment": {
            "openai_key_exists": bool(openai_key),
            "key_first_chars": openai_key[:7] if openai_key else None,
            "key_length": len(openai_key) if openai_key else 0,
            "python_path": sys.path[:3]  # First 3 paths
        },
        "engine_status": {
            "cava_engine_module_loaded": engine_loaded,
            "cava_engine_initialized": engine_initialized,
            "engine_has_api_key": engine_has_key,
            "engine_error": engine_error if not engine_initialized else None
        },
        "routes_loaded": {
            "registration_cava": any(r.path == "/api/v1/registration/cava" for r in router.routes),
            "registration_debug": any(r.path == "/api/v1/registration/debug" for r in router.routes),
            "registration_llm_status": True  # This endpoint
        },
        "critical_check": "🟢 READY" if (openai_key and engine_initialized) else "🔴 NOT READY"
    }

@router.get("/registration/debug-prompt")
async def debug_registration_prompt():
    """Show exactly what prompt is being sent to LLM"""
    import os
    from datetime import datetime
    
    # Create a test session to show what prompt would be generated
    test_session = {
        'collected_data': {'first_name': 'Peter'},
        'messages': [
            {'role': 'assistant', 'content': 'What is your last name?'},
            {'role': 'user', 'content': 'Knaflič'}
        ],
        'language': 'en',
        'last_question_type': 'last_name'
    }
    
    # Extract the test message
    message = "Knaflič"
    collected = test_session['collected_data']
    
    # Build the same prompt that would be used
    current_step = determine_registration_step(collected)
    next_action = get_next_action(collected)
    
    last_bot_message = test_session["messages"][-2]["content"] if len(test_session["messages"]) >= 2 else "Hello"
    last_user_message = message
    last_question_type = extract_question_type_from_message(last_bot_message)
    expected_data_type = map_question_to_data_type(last_question_type)
    interpretation = interpret_user_response(last_user_message, last_question_type)
    specific_instruction = generate_specific_instruction(collected, last_user_message)
    
    # Build the actual system prompt
    system_content = f"""You are AVA, an agricultural assistant helping farmers register. You must collect registration information in a natural, conversational way.

🎯 YOUR MISSION: Collect these 4 pieces of information:
1. First name (given name, personal name)
2. Last name (family name, surname)
3. WhatsApp number (with country code)
4. Password (minimum 8 characters)

📋 CURRENT REGISTRATION STATUS:
- First name: {collected.get('first_name', '❌ NOT COLLECTED')}
- Last name: {collected.get('last_name', '❌ NOT COLLECTED')}
- WhatsApp: {collected.get('whatsapp', '❌ NOT COLLECTED')}
- Password: {'✅ SET' if collected.get('password') else '❌ NOT COLLECTED'}

🧠 UNDERSTANDING NAMES - CRITICAL RULES:
1. First name = Given name = Personal name (e.g., Peter, Maria, Raj, Yuki)
2. Last name = Family name = Surname (e.g., Smith, Knaflič, Patel, Yamamoto)
3. After asking "What is your first name?" → The response IS their first name
4. After asking "What is your last name?" → The response IS their last name
5. NEVER mix these up!

📝 CONVERSATION CONTEXT:
Last question you asked: {last_bot_message}
User's last response: {last_user_message}
What this means: {interpretation}

🌍 CULTURAL AWARENESS:
- Western format: [First] [Last] (Peter Knaflič)
- Asian format: [Last] [First] (Yamamoto Yuki) - but users will adapt to your questions
- Spanish/Portuguese: May have multiple surnames (García López)
- Single name cultures: Some use only one name
- If someone gives multiple names after you ask for "first name", take the first word
- If someone gives multiple names after you ask for "last name", take all as last name

💬 CONVERSATION RULES:
1. Ask for ONE piece of information at a time
2. Acknowledge what they gave you before asking the next
3. Use natural, warm language
4. If they ask off-topic questions, politely redirect: "I'd love to help with that after we complete your registration!"
5. Confirm understanding: "Great! So your [first/last] name is X"

🔄 REGISTRATION FLOW:
Current step: {current_step}
Next action: {next_action}

Step 1: If no first name → Ask: "What is your first name?"
Step 2: If no last name → Ask: "Thank you [first_name]! What is your last name?"
Step 3: If no WhatsApp → Ask: "What is your WhatsApp number? Please include country code (like +386)"
Step 4: If no password → Ask: "Please create a password (minimum 8 characters)"
Step 5: All collected → Say: "Registration complete! Welcome to AVA, [first_name]!"

⚠️ CRITICAL INSTRUCTIONS:
- You just asked for: {last_question_type}
- The user's response "{last_user_message}" is their: {expected_data_type}
- Extract and acknowledge this EXACT data type
- Do NOT re-interpret or second-guess

🚫 COMMON MISTAKES TO AVOID:
- Asking for the same information twice
- Confusing first and last names
- Not acknowledging what user provided
- Being too formal (remember, these are farmers!)
- Asking multiple questions at once

✅ GOOD EXAMPLES:
User: "Peter"
You: "Nice to meet you, Peter! What is your last name?"

User: "Knaflič"  
You: "Thank you, Peter Knaflič! What is your WhatsApp number? Please include your country code."

User: "can you help me grow mangoes?"
You: "I'd be happy to help with mango growing after we finish your registration! What is your WhatsApp number?"

❌ BAD EXAMPLES:
User: "Peter"
You: "What is your first name?" (Already gave it!)

User: "Knaflič"
You: "Thank you for your first name" (This was their last name!)

🎯 YOUR IMMEDIATE TASK:
Based on the conversation above, {specific_instruction}

Remember: Be warm, natural, and helpful. These are farmers who need assistance, not tech experts!

Respond in en if possible."""
    
    # Get file modification time
    try:
        file_path = os.path.abspath(__file__)
        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
    except:
        file_modified = "Unable to determine"
    
    return {
        "🚨_DEBUG_INFO": "Registration Prompt Analysis",
        "prompt_length": len(system_content),
        "prompt_preview": system_content[:500] + "...",
        "full_prompt": system_content,
        "code_version": VERSION,
        "file_modified": file_modified,
        "contains_comprehensive": "UNDERSTANDING NAMES" in system_content,
        "prompt_type": "comprehensive" if "UNDERSTANDING NAMES" in system_content else "old",
        "test_scenario": {
            "collected": collected,
            "last_bot_message": last_bot_message,
            "user_response": last_user_message,
            "detected_question_type": last_question_type,
            "expected_data_type": expected_data_type,
            "interpretation": interpretation,
            "next_instruction": specific_instruction
        },
        "prompt_indicators": {
            "has_cultural_awareness": "CULTURAL AWARENESS" in system_content,
            "has_understanding_names": "UNDERSTANDING NAMES" in system_content,
            "has_good_examples": "GOOD EXAMPLES" in system_content,
            "has_immediate_task": "YOUR IMMEDIATE TASK" in system_content
        }
    }

@router.get("/registration/all-endpoints")
async def list_registration_endpoints():
    """DIAGNOSTIC: List all registration-related endpoints"""
    from main import app
    
    registration_endpoints = []
    for route in app.routes:
        if hasattr(route, 'path') and 'register' in str(route.path).lower():
            registration_endpoints.append({
                "path": str(route.path),
                "methods": list(route.methods) if hasattr(route, 'methods') else [],
                "name": route.name if hasattr(route, 'name') else None
            })
    
    return {
        "🔍_REGISTRATION_ENDPOINTS": "All endpoints containing 'register'",
        "endpoints": sorted(registration_endpoints, key=lambda x: x['path']),
        "total_count": len(registration_endpoints),
        "llm_endpoints": [
            "/api/v1/registration/cava",
            "/api/v1/chat/register",
            "/api/v1/registration/cava/enhanced"
        ],
        "diagnostic_endpoints": [
            "/api/v1/registration/debug",
            "/api/v1/registration/llm-status",
            "/api/v1/registration/all-endpoints"
        ]
    }