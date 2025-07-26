"""
OpenAI Configuration Routes - Manual setup and diagnostic endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from modules.core.openai_detective import OpenAIKeyDetective
import openai
import os

router = APIRouter()

class APIKeyConfig(BaseModel):
    api_key: str

@router.get("/api/v1/openai/investigate")
async def investigate_openai_key():
    """Comprehensive OpenAI key investigation"""
    report = OpenAIKeyDetective.investigate()
    return report

@router.post("/api/v1/openai/configure")
async def configure_openai_temporarily(config: APIKeyConfig):
    """Temporarily configure OpenAI key (until restart)"""
    if not config.api_key.startswith("sk-"):
        raise HTTPException(400, "Invalid API key format")
    
    try:
        # Test the key
        openai.api_key = config.api_key
        test = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        # If successful, set it
        os.environ["OPENAI_API_KEY"] = config.api_key
        
        return {
            "status": "success",
            "message": "OpenAI key configured temporarily",
            "warning": "This is temporary - add to ECS task definition for permanent fix",
            "test_successful": True
        }
        
    except openai.error.AuthenticationError:
        raise HTTPException(401, "Invalid API key")
    except Exception as e:
        raise HTTPException(500, f"Configuration failed: {str(e)}")

@router.get("/api/v1/openai/test")
async def test_openai_connection():
    """Test current OpenAI configuration"""
    try:
        if not openai.api_key and not os.getenv("OPENAI_API_KEY"):
            # Try recovery
            if not OpenAIKeyDetective.attempt_recovery():
                return {
                    "status": "not_configured",
                    "error": "No API key found",
                    "investigation": OpenAIKeyDetective.investigate()
                }
        
        # Test connection
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'AVA is working'"}],
            max_tokens=10
        )
        
        return {
            "status": "working",
            "response": response.choices[0].message.content,
            "model": "gpt-3.5-turbo"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__,
            "investigation": OpenAIKeyDetective.investigate()
        }