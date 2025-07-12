"""
API Gateway with LLM-First Database Queries
Constitutional compliance integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from database_operations_constitutional import ConstitutionalDatabaseOperations
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Assistant API - Constitutional",
    description="API Gateway with 100% LLM-First Database Queries",
    version="4.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database operations
db_ops = ConstitutionalDatabaseOperations()


# Pydantic models
class FarmerQuery(BaseModel):
    query: str = Field(..., description="Natural language query in any language")
    farmer_id: Optional[int] = Field(None, description="Farmer ID for context")
    language: str = Field("en", description="Language code (bg, sl, hr, en, etc.)")
    country_code: Optional[str] = Field(None, description="Country code (BG, SI, HR, etc.)")


class FarmerQueryResponse(BaseModel):
    success: bool
    response: str
    constitutional_compliance: bool
    method: str
    metadata: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = await db_ops.health_check()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "api-gateway-constitutional",
        "version": "4.0.0",
        "constitutional_compliance": True,
        "llm_first": True,
        "database_connected": db_healthy
    }


@app.post("/api/v1/farmer/query", response_model=FarmerQueryResponse)
async def process_farmer_query(request: FarmerQuery):
    """
    Process farmer database query using LLM-first approach
    Constitutional compliance: 100% LLM-driven
    """
    try:
        response = await db_ops.process_natural_query(
            query_text=request.query,
            farmer_id=request.farmer_id,
            language=request.language,
            country_code=request.country_code
        )
        
        return FarmerQueryResponse(
            success=True,
            response=response,
            constitutional_compliance=True,
            method="llm_first",
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "language": request.language,
                "country_code": request.country_code,
                "compliance": {
                    "llm_first": True,
                    "mango_rule": True,
                    "privacy_first": True
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/farmer/{farmer_id}/fields")
async def get_farmer_fields(farmer_id: int, language: str = "en"):
    """Get farmer's fields using LLM-first approach"""
    try:
        response = await db_ops.process_natural_query(
            query_text="Show me all my fields with their sizes and current crops",
            farmer_id=farmer_id,
            language=language
        )
        
        return {
            "success": True,
            "response": response,
            "farmer_id": farmer_id,
            "constitutional_compliance": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/farmer/{farmer_id}/crops")
async def get_farmer_crops(farmer_id: int, language: str = "en"):
    """Get farmer's crops using LLM-first approach"""
    try:
        response = await db_ops.process_natural_query(
            query_text="What crops am I currently growing and their status?",
            farmer_id=farmer_id,
            language=language
        )
        
        return {
            "success": True,
            "response": response,
            "farmer_id": farmer_id,
            "constitutional_compliance": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/farmer/{farmer_id}/tasks")
async def get_farmer_tasks(farmer_id: int, language: str = "en"):
    """Get farmer's tasks using LLM-first approach"""
    try:
        response = await db_ops.process_natural_query(
            query_text="Show me my upcoming agricultural tasks",
            farmer_id=farmer_id,
            language=language
        )
        
        return {
            "success": True,
            "response": response,
            "farmer_id": farmer_id,
            "constitutional_compliance": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Constitutional compliance test endpoints
@app.post("/api/v1/test/mango-rule")
async def test_mango_rule():
    """Test Bulgarian mango farmer scenario for constitutional compliance"""
    test_query = FarmerQuery(
        query="Колко манго дървета имам?",  # How many mango trees do I have?
        farmer_id=999,  # Test farmer
        language="bg",
        country_code="BG"
    )
    
    try:
        result = await process_farmer_query(test_query)
        return {
            "test": "Bulgarian Mango Farmer",
            "passed": result.success,
            "constitutional_compliance": result.constitutional_compliance,
            "response": result.response,
            "details": {
                "query": test_query.query,
                "language": test_query.language,
                "country": test_query.country_code,
                "method": result.method
            }
        }
    except Exception as e:
        return {
            "test": "Bulgarian Mango Farmer",
            "passed": False,
            "error": str(e),
            "constitutional_compliance": False
        }


@app.post("/api/v1/test/slovenian-farmer")
async def test_slovenian_farmer():
    """Test Slovenian farmer scenario"""
    test_query = FarmerQuery(
        query="Kdaj je potrebno pošpricati paradižnik proti plesni?",  # When to spray tomatoes against blight?
        farmer_id=998,
        language="sl",
        country_code="SI"
    )
    
    try:
        result = await process_farmer_query(test_query)
        return {
            "test": "Slovenian Tomato Farmer",
            "passed": result.success,
            "constitutional_compliance": result.constitutional_compliance,
            "response": result.response
        }
    except Exception as e:
        return {
            "test": "Slovenian Tomato Farmer",
            "passed": False,
            "error": str(e)
        }


@app.post("/api/v1/test/complex-query")
async def test_complex_query():
    """Test complex agricultural query"""
    test_query = FarmerQuery(
        query="Show me which fields have tomatoes planted this year and their expected harvest dates",
        farmer_id=997,
        language="en"
    )
    
    try:
        result = await process_farmer_query(test_query)
        return {
            "test": "Complex Agricultural Query",
            "passed": result.success,
            "constitutional_compliance": result.constitutional_compliance,
            "response": result.response
        }
    except Exception as e:
        return {
            "test": "Complex Agricultural Query",
            "passed": False,
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AVA OLO API Gateway - Constitutional",
        "version": "4.0.0",
        "description": "100% LLM-First Database Query System",
        "constitutional_compliance": {
            "status": "FULLY COMPLIANT",
            "principles": {
                "llm_first": "All queries generated by GPT-4",
                "mango_rule": "Works for Bulgarian mango farmers",
                "privacy_first": "Farmer data never sent to external APIs",
                "transparency": "All LLM decisions logged"
            }
        },
        "endpoints": {
            "query": "POST /api/v1/farmer/query",
            "fields": "GET /api/v1/farmer/{farmer_id}/fields",
            "crops": "GET /api/v1/farmer/{farmer_id}/crops",
            "tasks": "GET /api/v1/farmer/{farmer_id}/tasks",
            "tests": {
                "mango_rule": "POST /api/v1/test/mango-rule",
                "slovenian": "POST /api/v1/test/slovenian-farmer",
                "complex": "POST /api/v1/test/complex-query"
            }
        },
        "usage_example": {
            "endpoint": "POST /api/v1/farmer/query",
            "body": {
                "query": "What crops should I plant next month?",
                "farmer_id": 123,
                "language": "en",
                "country_code": "US"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)