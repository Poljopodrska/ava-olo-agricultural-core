"""
API Gateway - Standardized API layer for AVA OLO
All external communication goes through this gateway
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_router import LLMRouter, QueryType, DataSource
from core.database_operations import DatabaseOperations
from core.knowledge_search import KnowledgeSearch
from core.external_search import ExternalSearch
from core.language_processor import LanguageProcessor
from monitoring.business_dashboard import router as business_router

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Assistant API",
    description="API Gateway for Croatian Agricultural Virtual Assistant",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include business dashboard router
app.include_router(business_router, prefix="", tags=["business-dashboard"])

# Initialize core modules
router = LLMRouter()
db_ops = DatabaseOperations()
knowledge = KnowledgeSearch()
external = ExternalSearch()
language = LanguageProcessor()

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query in any language")
    farmer_id: Optional[int] = Field(None, description="Farmer ID for context")
    wa_phone_number: Optional[str] = Field(None, description="WhatsApp number")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class QueryResponse(BaseModel):
    success: bool
    answer: str
    query_type: str
    confidence: float
    sources: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FieldRequest(BaseModel):
    farmer_id: int
    field_name: str
    field_size: float
    field_location: Optional[str] = None
    soil_type: Optional[str] = None

class CropRequest(BaseModel):
    field_id: int
    crop_name: str
    variety: Optional[str] = None
    planting_date: Optional[str] = None
    expected_harvest_date: Optional[str] = None

class TaskRequest(BaseModel):
    farmer_id: int
    field_id: Optional[int] = None
    task_type: str
    task_description: str
    task_date: Optional[str] = None

# Main query endpoint
@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Main endpoint for processing agricultural queries
    """
    try:
        start_time = datetime.now()
        
        # Process language and extract entities
        processed = await language.process_query(request.query)
        
        # Route query to appropriate handlers
        routing_decision = await router.route_query(
            request.query,
            {
                "farmer_id": request.farmer_id,
                "processed_query": processed,
                **request.context
            }
        )
        
        # Execute query based on routing
        answer_data = await _execute_query(
            routing_decision,
            request,
            processed
        )
        
        # Generate natural language response
        answer = await language.generate_response(
            request.query,
            answer_data,
            processed["language"]
        )
        
        # Save conversation if farmer_id provided
        if request.farmer_id:
            await db_ops.save_conversation(request.farmer_id, {
                "wa_phone_number": request.wa_phone_number,
                "question": request.query,
                "answer": answer,
                "language": processed["language"],
                "topic": routing_decision["query_type"],
                "confidence_score": routing_decision["confidence"]
            })
        
        # Log LLM operation
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        await db_ops.log_llm_operation({
            "operation_type": "query",
            "input_text": request.query,
            "output_text": answer,
            "model_used": "gpt-4",
            "tokens_used": 0,  # Would calculate actual tokens
            "latency_ms": latency_ms,
            "success": True,
            "error_message": None
        })
        
        return QueryResponse(
            success=True,
            answer=answer,
            query_type=routing_decision["query_type"],
            confidence=routing_decision["confidence"],
            sources=answer_data.get("sources", []),
            entities=processed["entities"],
            metadata={
                "language": processed["language"],
                "processing_time_ms": latency_ms,
                "data_sources": routing_decision["data_sources"]
            }
        )
        
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _execute_query(routing: Dict[str, Any], 
                        request: QueryRequest,
                        processed: Dict[str, Any]) -> Dict[str, Any]:
    """Execute query based on routing decision"""
    
    results = {}
    
    # Check each data source
    if DataSource.DATABASE.value in routing["data_sources"]:
        if request.farmer_id:
            # Get farmer context
            farmer_info = await db_ops.get_farmer_info(request.farmer_id)
            fields = await db_ops.get_farmer_fields(request.farmer_id)
            results["farmer_data"] = {
                "info": farmer_info,
                "fields": fields
            }
    
    if DataSource.KNOWLEDGE_BASE.value in routing["data_sources"]:
        # Search knowledge base
        if routing["query_type"] == QueryType.PEST_CONTROL.value:
            # Special handling for pesticide queries
            chemical = processed["entities"].get("chemical")
            crop = processed["entities"].get("crop")
            if chemical:
                kb_results = await knowledge.search_pesticide_info(chemical, crop)
                results["pesticide_info"] = kb_results
        else:
            # General knowledge search
            kb_results = await knowledge.search(request.query)
            results["knowledge"] = kb_results
    
    if DataSource.EXTERNAL_SEARCH.value in routing["data_sources"]:
        # Search external sources
        ext_results = await external.search(request.query)
        results["external"] = ext_results
    
    return results

# Field management endpoints
@app.post("/api/v1/fields/create")
async def create_field(request: FieldRequest):
    """Create a new field for farmer"""
    try:
        field_id = await db_ops.create_field(request.farmer_id, request.dict())
        if field_id:
            return {"success": True, "field_id": field_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create field")
    except Exception as e:
        logger.error(f"Field creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fields/{farmer_id}")
async def get_farmer_fields(farmer_id: int):
    """Get all fields for a farmer"""
    try:
        fields = await db_ops.get_farmer_fields(farmer_id)
        return {"success": True, "fields": fields}
    except Exception as e:
        logger.error(f"Get fields error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Crop management endpoints
@app.post("/api/v1/crops/plant")
async def plant_crop(request: CropRequest):
    """Plant a crop in a field"""
    try:
        success = await db_ops.add_crop_to_field(request.field_id, request.dict())
        if success:
            return {"success": True, "message": "Crop planted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to plant crop")
    except Exception as e:
        logger.error(f"Plant crop error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Task logging endpoint
@app.post("/api/v1/tasks/log")
async def log_task(request: TaskRequest):
    """Log a farm task"""
    try:
        task_id = await db_ops.log_farm_task(request.farmer_id, request.dict())
        if task_id:
            return {"success": True, "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to log task")
    except Exception as e:
        logger.error(f"Task logging error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """System health check"""
    try:
        # Check all components
        db_health = await db_ops.health_check()
        ext_health = await external.health_check()
        
        all_healthy = db_health and ext_health
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "healthy" if db_health else "unhealthy",
                "external_search": "healthy" if ext_health else "unhealthy",
                "knowledge_base": "healthy",  # Assumed always available
                "llm_router": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# All farmers list endpoint
@app.get("/api/v1/farmers")
async def get_all_farmers(limit: int = 100):
    """Get list of all farmers for UI selection"""
    try:
        farmers = await db_ops.get_all_farmers(limit)
        return {"success": True, "farmers": farmers}
    except Exception as e:
        logger.error(f"Get all farmers error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Farmer info endpoint
@app.get("/api/v1/farmers/{farmer_id}")
async def get_farmer(farmer_id: int):
    """Get farmer information"""
    try:
        farmer = await db_ops.get_farmer_info(farmer_id)
        if farmer:
            return {"success": True, "farmer": farmer}
        else:
            raise HTTPException(status_code=404, detail="Farmer not found")
    except Exception as e:
        logger.error(f"Get farmer error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Conversation history endpoint
@app.get("/api/v1/conversations/farmer/{farmer_id}")
async def get_conversations(farmer_id: int, limit: int = 10):
    """Get recent conversations for farmer"""
    try:
        conversations = await db_ops.get_recent_conversations(farmer_id, limit)
        return {"success": True, "conversations": conversations}
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Conversations for approval (agronomic dashboard)
@app.get("/api/v1/conversations/approval")
async def get_conversations_for_approval():
    """Get conversations grouped by approval status"""
    try:
        conversations = await db_ops.get_conversations_for_approval()
        return {"success": True, "conversations": conversations}
    except Exception as e:
        logger.error(f"Get approval conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Single conversation details
@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: int):
    """Get detailed conversation information"""
    try:
        conversation = await db_ops.get_conversation_details(conversation_id)
        if conversation:
            return {"success": True, "conversation": conversation}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Get conversation details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Weather endpoint
@app.get("/api/v1/weather/{location}")
async def get_weather(location: str, days: int = 7):
    """Get weather forecast for location"""
    try:
        weather = await external.get_weather_forecast(location, days)
        return weather
    except Exception as e:
        logger.error(f"Weather fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Market prices endpoint
@app.get("/api/v1/prices/{commodity}")
async def get_prices(commodity: str, market: str = "Croatia"):
    """Get market prices for commodity"""
    try:
        prices = await external.get_market_prices(commodity, market)
        return prices
    except Exception as e:
        logger.error(f"Price fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)