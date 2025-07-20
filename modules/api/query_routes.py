#!/usr/bin/env python3
"""
Query API routes for AVA OLO Agricultural Core
Handles agricultural queries and WhatsApp integration
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..core.config import VERSION, emergency_log

logger = logging.getLogger(__name__)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    farmer_id: str = "anonymous"
    language: str = "en"

class QueryResponse(BaseModel):
    response: str
    confidence: float = 0.95
    sources: List[str] = []

class WhatsAppQueryRequest(BaseModel):
    query: str

class WhatsAppQueryResponse(BaseModel):
    response: str
    farmer_id: str
    query_type: str = "agricultural"

class ConversationRequest(BaseModel):
    message: str
    farmer_id: str
    conversation_id: Optional[str] = None
    language: str = "en"

class ConversationResponse(BaseModel):
    response: str
    conversation_id: str
    message_count: int

router = APIRouter(tags=["queries"])

@router.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process agricultural query"""
    try:
        # Import language processor
        from implementation.language_processor import get_assistant_response
        
        # Get response from LLM
        response_text = await get_assistant_response(
            request.query,
            farmer_id=request.farmer_id,
            language=request.language
        )
        
        return QueryResponse(
            response=response_text,
            confidence=0.95,
            sources=["Agricultural Knowledge Base", "Local Farming Practices"]
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/farmer/whatsapp-query", response_model=WhatsAppQueryResponse)
async def process_whatsapp_query(request: WhatsAppQueryRequest):
    """Process WhatsApp query from farmer"""
    try:
        # Import language processor
        from implementation.language_processor import get_assistant_response
        
        # Generate farmer ID from WhatsApp (in production, this would come from WhatsApp metadata)
        farmer_id = f"whatsapp_{datetime.now().timestamp()}"
        
        # Get response
        response_text = await get_assistant_response(
            request.query,
            farmer_id=farmer_id,
            language="auto"  # Auto-detect language
        )
        
        return WhatsAppQueryResponse(
            response=response_text,
            farmer_id=farmer_id,
            query_type="agricultural"
        )
    except Exception as e:
        logger.error(f"WhatsApp query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/conversation/chat", response_model=ConversationResponse)
async def conversation_chat(request: ConversationRequest):
    """Handle conversational chat"""
    try:
        # Import conversation manager
        from implementation.conversation_manager import ConversationManager
        
        # Get or create conversation
        conv_manager = ConversationManager()
        conversation_id = request.conversation_id or f"conv_{request.farmer_id}_{datetime.now().timestamp()}"
        
        # Process message
        response = await conv_manager.process_message(
            message=request.message,
            farmer_id=request.farmer_id,
            conversation_id=conversation_id,
            language=request.language
        )
        
        # Get message count
        message_count = conv_manager.get_message_count(conversation_id)
        
        return ConversationResponse(
            response=response,
            conversation_id=conversation_id,
            message_count=message_count
        )
    except ImportError:
        # Fallback if conversation manager not available
        from implementation.language_processor import get_assistant_response
        
        response = await get_assistant_response(
            request.message,
            farmer_id=request.farmer_id,
            language=request.language
        )
        
        return ConversationResponse(
            response=response,
            conversation_id=request.conversation_id or "fallback",
            message_count=1
        )
    except Exception as e:
        logger.error(f"Conversation chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/web/query", response_class=HTMLResponse)
async def web_query(query: str = Form(...)):
    """Process query from web form"""
    try:
        # Import language processor
        from implementation.language_processor import get_assistant_response
        
        # Get response
        response = await get_assistant_response(query, farmer_id="web_user", language="en")
        
        # Return HTML response
        html = f"""
        <div class="response-container">
            <h3>Question:</h3>
            <p>{query}</p>
            <h3>Answer:</h3>
            <p>{response}</p>
            <button onclick="window.history.back()">Ask Another Question</button>
        </div>
        """
        
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"Web query failed: {e}")
        html = f"""
        <div class="error-container">
            <h3>Error:</h3>
            <p>Failed to process query: {str(e)}</p>
            <button onclick="window.history.back()">Go Back</button>
        </div>
        """
        return HTMLResponse(content=html, status_code=500)