from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    farmer_id: str = "1"
    language: str = "en"

# Simple responses for different languages
responses = {
    "en": {
        "greeting": "Hello! How can I help you with your farming today?",
        "weather": "The weather looks good for farming today.",
        "default": "I understand. How can I assist you further?"
    },
    "bg": {
        "greeting": "Здравейте! Как мога да ви помогна с земеделието днес?",
        "weather": "Времето изглежда добро за земеделие днес.",
        "default": "Разбирам. Как мога да ви помогна допълнително?"
    },
    "sl": {
        "greeting": "Pozdravljeni! Kako vam lahko pomagam pri kmetovanju danes?",
        "weather": "Vreme je videti dobro za kmetovanje danes.",
        "default": "Razumem. Kako vam lahko še pomagam?"
    }
}

@router.post("")
async def chat(request: ChatRequest):
    """Simple chat endpoint with language support"""
    message_lower = request.message.lower()
    lang = request.language if request.language in responses else "en"
    
    # Simple keyword matching
    if any(word in message_lower for word in ["hello", "hi", "здравей", "pozdravljeni"]):
        response = responses[lang]["greeting"]
    elif any(word in message_lower for word in ["weather", "време", "vreme"]):
        response = responses[lang]["weather"]
    else:
        response = responses[lang]["default"]
    
    return JSONResponse(content={
        "response": response,
        "farmer_id": request.farmer_id,
        "language": lang,
        "timestamp": datetime.now().isoformat()
    })

@router.get("/history")
async def get_chat_history(farmer_id: str = "1"):
    """Get chat history"""
    # Mock history
    return JSONResponse(content={
        "farmer_id": farmer_id,
        "messages": [
            {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "Hello! How can I help?", "timestamp": datetime.now().isoformat()}
        ]
    })