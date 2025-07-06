"""
Simple API Gateway Mock for Testing Integration
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    farmer_id: Optional[int] = None
    context: Dict[str, Any] = {}

@app.post("/api/v1/query")
async def process_query(request: QueryRequest):
    """Mock query processing"""
    
    # Simple mock responses based on query
    if "prosaro" in request.query.lower():
        return {
            "success": True,
            "answer": "Prosaro ima karenciju od 35 dana za pšenicu. To znači da nakon tretmana trebate čekati 35 dana prije žetve.",
            "metadata": {
                "query_type": "pest_control",
                "language": "hr",
                "confidence": 0.95,
                "source": "mock_knowledge_base"
            }
        }
    elif "test" in request.query.lower():
        return {
            "success": True,
            "answer": "✅ Modularni sustav AVA OLO radi ispravno! Vaše pitanje je uspješno proslijeđeno kroz API Gateway.",
            "metadata": {
                "query_type": "general",
                "language": "hr",
                "confidence": 1.0,
                "source": "mock_test"
            }
        }
    else:
        return {
            "success": True,
            "answer": f"Hvala na pitanju: '{request.query}'. Ovo je testni odgovor iz modularnog API Gateway-a.",
            "metadata": {
                "query_type": "general",
                "language": "hr",
                "confidence": 0.8,
                "source": "mock_general"
            }
        }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Mock API Gateway is running",
        "modules": {
            "llm_router": "healthy",
            "database": "mock",
            "knowledge_search": "mock",
            "language_processor": "healthy"
        }
    }

@app.get("/api/v1/business/summary")
async def business_summary():
    """Mock business dashboard"""
    return {
        "usage_metrics": {
            "total_queries": 42,
            "unique_users": 8,
            "daily_active_users": 3
        },
        "system_metrics": {
            "uptime_percentage": 99.5,
            "average_response_time": 1.2
        },
        "business_insights": {
            "farmer_adoption_rate": 75.0,
            "user_satisfaction": 4.5
        },
        "summary": {
            "system_health": "healthy",
            "growth_trend": "positive"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)