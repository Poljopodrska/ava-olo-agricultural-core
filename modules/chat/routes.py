#!/usr/bin/env python3
"""
Simple Direct LLM Chat - v3.4.5 Test
Direct OpenAI connection with no complexity
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatRequest(BaseModel):
    """Simple chat request"""
    message: str
    farmer_id: str = "test"

@router.post("")
async def direct_llm_chat(request: ChatRequest):
    """Direct OpenAI test - no CAVA, no complexity"""
    return await handle_chat(request)

@router.post("/message")
async def direct_llm_chat_message(request: Request):
    """Handle /message endpoint used by dashboard"""
    body = await request.json()
    chat_request = ChatRequest(
        message=body.get("content", ""),
        farmer_id=body.get("farmer_id", "test")
    )
    return await handle_chat(chat_request)

async def handle_chat(request: ChatRequest):
    """Common chat handler"""
    
    # Log for debugging
    logger.info(f"DIRECT LLM TEST: {request.message}")
    logger.info(f"OpenAI Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")
    
    try:
        # Get API key explicitly
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment!")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        logger.info(f"Using OpenAI key: {api_key[:10]}...")
        
        # Direct OpenAI call with explicit key
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful agricultural assistant for AVA OLO. Keep responses concise and helpful."},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        llm_response = response.choices[0].message.content
        logger.info(f"LLM responded: {llm_response[:100]}...")
        
        return {
            "response": llm_response,
            "llm_test": True,
            "model": "gpt-4",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return {
            "response": f"LLM Error: {str(e)}",
            "error": True,
            "openai_key_exists": bool(os.getenv("OPENAI_API_KEY")),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/status")
async def llm_status():
    """Check if OpenAI is properly configured"""
    key = os.getenv("OPENAI_API_KEY", "")
    return {
        "openai_configured": bool(key),
        "key_prefix": key[:10] if key else None,
        "key_length": len(key),
        "test_mode": "direct_llm_v3.4.6",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/env-check")
async def check_environment():
    """Debug endpoint to verify environment variables"""
    import os
    
    # Check various possible key names
    possible_keys = [
        "OPENAI_API_KEY",
        "OPENAI_KEY", 
        "OPENAI_API_TOKEN",
        "openai_api_key"
    ]
    
    found_keys = {}
    for key_name in possible_keys:
        value = os.getenv(key_name, "")
        if value:
            found_keys[key_name] = f"{value[:7]}...{value[-4:]}" if len(value) > 15 else "SHORT_KEY"
    
    # Check all env vars starting with OPENAI
    openai_vars = {k: f"{v[:10]}..." for k, v in os.environ.items() if k.startswith("OPENAI")}
    
    return {
        "found_keys": found_keys,
        "openai_vars": openai_vars,
        "env_count": len(os.environ),
        "path": os.getenv("PATH", "").split(":")[0],
        "aws_region": os.getenv("AWS_DEFAULT_REGION", "not_set"),
        "ecs_container": os.getenv("ECS_CONTAINER_METADATA_URI_V4", "not_ecs")
    }

@router.get("/test")
async def test_llm():
    """Quick test endpoint"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'LLM working!' and the current time."}],
            max_tokens=50
        )
        return {
            "test": "success",
            "response": response.choices[0].message.content,
            "model": "gpt-4"
        }
    except Exception as e:
        return {
            "test": "failed",
            "error": str(e),
            "key_exists": bool(os.getenv("OPENAI_API_KEY")),
            "key_length": len(os.getenv("OPENAI_API_KEY", ""))
        }