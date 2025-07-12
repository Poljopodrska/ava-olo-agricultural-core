"""
API Gateway with Country-Based Localization
Constitutional Amendment #13 Integration Example

This shows how to integrate the localization system into the API Gateway
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the new localization modules from core
from core.llm_router_with_localization import LocalizedLLMRouter, LLMRouterAdapter
from core.country_detector import CountryDetector
from core.localization_handler import LocalizationHandler
from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agricultural Assistant API - Localized",
    description="API Gateway with Constitutional Amendment #13 - Country-Based Localization",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
db_ops = DatabaseOperations()
country_detector = CountryDetector()
localization_handler = LocalizationHandler()
router_adapter = LLMRouterAdapter()

# Enhanced Pydantic models for API with localization
class LocalizedQueryRequest(BaseModel):
    query: str = Field(..., description="User query in any language")
    whatsapp_number: str = Field(..., description="WhatsApp number with country code")
    farmer_id: Optional[int] = Field(None, description="Farmer ID for context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class LocalizedQueryResponse(BaseModel):
    success: bool
    answer: str
    query_type: str
    confidence: float
    country_detected: str
    language_used: str
    information_sources: List[str]
    metadata: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway-localized",
        "version": "3.0.0",
        "constitutional_amendment": 13,
        "features": ["country-detection", "localization", "information-hierarchy"]
    }

@app.post("/api/v1/query/localized", response_model=LocalizedQueryResponse)
async def process_localized_query(request: LocalizedQueryRequest):
    """
    Process query with full country-based localization
    Implements Constitutional Amendment #13
    """
    try:
        # Step 1: Detect country from WhatsApp number
        country_info = country_detector.get_country_info(request.whatsapp_number)
        logger.info(f"Detected country: {country_info['country_code']} from {request.whatsapp_number}")
        
        # Step 2: Process query with localization
        response = await router_adapter.process_message(
            message=request.query,
            phone_number=request.whatsapp_number,
            farmer_id=request.farmer_id
        )
        
        # Step 3: Get additional context for response
        context = router_adapter.get_context_for_farmer(request.whatsapp_number)
        
        return LocalizedQueryResponse(
            success=True,
            answer=response,
            query_type="agricultural",
            confidence=0.95,
            country_detected=country_info['country_code'],
            language_used=context['language'],
            information_sources=["database", "country-specific", "global"],
            metadata={
                "country_name": country_info['country_name'],
                "languages_available": country_info['languages'],
                "timestamp": datetime.utcnow().isoformat(),
                "constitutional_compliance": True
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing localized query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/country/detect/{phone_number}")
async def detect_country(phone_number: str):
    """
    Detect country from WhatsApp number
    Useful for testing country detection
    """
    try:
        country_info = country_detector.get_country_info(phone_number)
        return {
            "success": True,
            "phone_number": phone_number,
            "country_code": country_info['country_code'],
            "country_name": country_info['country_name'],
            "languages": country_info['languages'],
            "detection_method": country_info['detection_method']
        }
    except Exception as e:
        logger.error(f"Error detecting country: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test/mango")
async def test_mango_compliance():
    """
    Test the Bulgarian mango farmer scenario
    Constitutional compliance test endpoint
    """
    bulgarian_query = LocalizedQueryRequest(
        query="Кога да бера манго?",  # When to harvest mango?
        whatsapp_number="+359123456789",
        farmer_id=123
    )
    
    try:
        result = await process_localized_query(bulgarian_query)
        return {
            "test": "bulgarian_mango_farmer",
            "passed": True,
            "response": result.answer,
            "country": result.country_detected,
            "language": result.language_used,
            "constitutional_compliance": "PASSED"
        }
    except Exception as e:
        return {
            "test": "bulgarian_mango_farmer",
            "passed": False,
            "error": str(e),
            "constitutional_compliance": "FAILED"
        }

@app.get("/api/v1/farmers/{farmer_id}/context")
async def get_farmer_context(farmer_id: int):
    """
    Get localization context for a specific farmer
    """
    try:
        # Get farmer from database
        farmer_data = await db_ops.get_farmer_by_id(farmer_id)
        if not farmer_data:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Get localization context
        whatsapp_number = farmer_data.get('whatsapp_number')
        if not whatsapp_number:
            return {
                "success": False,
                "message": "Farmer has no WhatsApp number registered"
            }
        
        context = router_adapter.get_context_for_farmer(whatsapp_number)
        
        return {
            "success": True,
            "farmer_id": farmer_id,
            "whatsapp_number": whatsapp_number,
            "localization_context": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting farmer context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Example usage documentation
@app.get("/")
async def root():
    """Root endpoint with usage examples"""
    return {
        "service": "AVA OLO API Gateway - Localized",
        "version": "3.0.0",
        "constitutional_amendment": 13,
        "description": "Country-based localization for agricultural assistance",
        "usage_examples": {
            "detect_country": "GET /api/v1/country/detect/+386123456789",
            "process_query": {
                "endpoint": "POST /api/v1/query/localized",
                "body": {
                    "query": "When to plant tomatoes?",
                    "whatsapp_number": "+386123456789",
                    "farmer_id": 123
                }
            },
            "test_mango": "POST /api/v1/test/mango",
            "farmer_context": "GET /api/v1/farmers/123/context"
        },
        "supported_countries": "200+ countries via phone number detection",
        "information_hierarchy": ["FARMER_SPECIFIC", "COUNTRY_SPECIFIC", "GLOBAL"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)