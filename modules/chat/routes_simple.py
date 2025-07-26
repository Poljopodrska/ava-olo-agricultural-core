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
    
    # Log for debugging
    logger.info(f"DIRECT LLM TEST: {request.message}")
    logger.info(f"OpenAI Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")
    
    try:
        # Direct OpenAI call
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
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
        "test_mode": "direct_llm_v3.4.5",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test")
async def test_llm():
    """Quick test endpoint"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
            "key_exists": bool(os.getenv("OPENAI_API_KEY"))
        }