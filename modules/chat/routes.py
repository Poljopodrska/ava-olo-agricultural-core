#!/usr/bin/env python3
"""
Secure LLM Chat - v3.4.8 AWS Secrets
Direct OpenAI connection using AWS SSM Parameter Store
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import os
import logging
from datetime import datetime

from modules.chat.openai_key_manager import get_openai_client, key_manager

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
    """Common chat handler using secure AWS SSM key retrieval"""
    
    # Log for debugging
    logger.info(f"SECURE LLM CHAT: {request.message}")
    
    try:
        # Get OpenAI client using secure key management
        client = get_openai_client()
        
        if not client:
            logger.error("Could not create OpenAI client - key not available")
            return {
                "response": "AI service temporarily unavailable. Please try again later.",
                "error": True,
                "error_type": "key_unavailable",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info("Using OpenAI client with secure key from AWS SSM")
        
        # Direct OpenAI call
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
            "response": f"AI Error: {str(e)}",
            "error": True,
            "error_type": "openai_api_error", 
            "timestamp": datetime.now().isoformat()
        }

@router.get("/status")
async def llm_status():
    """Check if OpenAI is properly configured using secure key management"""
    
    # Check if key is available
    api_key = key_manager.get_api_key()
    source = "env" if os.getenv("OPENAI_API_KEY") else "aws_ssm"
    
    return {
        "openai_configured": bool(api_key),
        "key_prefix": api_key[:10] if api_key else None,
        "key_length": len(api_key) if api_key else 0,
        "key_source": source,
        "test_mode": "aws_secrets_v3.4.8",
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

@router.get("/debug/all-env")
async def debug_all_env():
    """Show ALL environment variables (sanitized)"""
    import os
    
    all_env = {}
    for key, value in os.environ.items():
        if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
            all_env[key] = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else "***"
        else:
            all_env[key] = value
    
    return {
        "total_env_vars": len(all_env),
        "has_openai_key": "OPENAI_API_KEY" in os.environ,
        "all_vars": all_env,
        "task_arn": os.getenv("ECS_CONTAINER_METADATA_URI_V4", "not_in_ecs"),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test")
async def test_llm():
    """Quick test endpoint using secure key management"""
    return key_manager.test_connection()

@router.get("/aws-test")
async def test_aws_integration():
    """Test AWS SSM integration specifically"""
    try:
        import boto3
        
        # Test SSM access
        ssm = boto3.client('ssm', region_name='us-east-1')
        
        # Try to get the parameter (without decryption to test access)
        response = ssm.get_parameter(
            Name='/ava-olo/openai-api-key',
            WithDecryption=False  # Just test access
        )
        
        return {
            "aws_ssm_access": True,
            "parameter_exists": True,
            "parameter_name": response['Parameter']['Name'],
            "parameter_type": response['Parameter']['Type'],
            "last_modified": response['Parameter']['LastModifiedDate'].isoformat(),
            "version": response['Parameter']['Version']
        }
        
    except Exception as e:
        return {
            "aws_ssm_access": False,
            "error": str(e),
            "boto3_available": True
        }