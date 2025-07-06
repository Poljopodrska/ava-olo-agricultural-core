"""
AVA OLO Agronomic Dashboard Service - Port 8003
Updated to redirect to new Agronomic Approval Dashboard on port 8007
"""
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agronomic Dashboard",
    description="Expert monitoring and intervention system for agricultural discussions",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

# Initialize database
db_ops = DatabaseOperations()

class AgronomicDashboard:
    """Dashboard for agricultural experts to monitor and approve conversations"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def get_pending_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversations that need expert review"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                results = session.execute(
                    text("""
                    SELECT id, farmer_id, wa_phone_number, question, answer, 
                           confidence_score, language, topic, created_at,
                           expert_approved, expert_notes
                    FROM ava_conversations 
                    WHERE expert_approved IS NULL OR confidence_score < 0.8
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()
                
                conversations = []
                for row in results:
                    conversations.append({
                        "id": row[0],
                        "farmer_id": row[1],
                        "wa_phone": row[2],
                        "question": row[3],
                        "answer": row[4],
                        "confidence": float(row[5]) if row[5] else 0.0,
                        "language": row[6],
                        "topic": row[7],
                        "created_at": row[8].isoformat() if row[8] else None,
                        "expert_approved": row[9],
                        "expert_notes": row[10],
                        "needs_review": row[9] is None or (row[5] and float(row[5]) < 0.8)
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error getting pending conversations: {str(e)}")
            return []
    
    async def approve_conversation(self, conversation_id: int, approved: bool, notes: str = "") -> bool:
        """Approve or reject a conversation"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                session.execute(
                    text("""
                    UPDATE ava_conversations 
                    SET expert_approved = :approved, expert_notes = :notes,
                        expert_reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = :conv_id
                    """),
                    {
                        "approved": approved,
                        "notes": notes,
                        "conv_id": conversation_id
                    }
                )
                session.commit()
                
                logger.info(f"Conversation {conversation_id} {'approved' if approved else 'rejected'} by expert")
                return True
                
        except Exception as e:
            logger.error(f"Error approving conversation: {str(e)}")
            return False
    
    async def update_answer(self, conversation_id: int, new_answer: str, expert_notes: str = "") -> bool:
        """Expert manually updates an answer"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                session.execute(
                    text("""
                    UPDATE ava_conversations 
                    SET answer = :new_answer, expert_approved = TRUE, 
                        expert_notes = :notes, expert_reviewed_at = CURRENT_TIMESTAMP,
                        expert_modified = TRUE
                    WHERE id = :conv_id
                    """),
                    {
                        "new_answer": new_answer,
                        "notes": expert_notes,
                        "conv_id": conversation_id
                    }
                )
                session.commit()
                
                logger.info(f"Expert updated answer for conversation {conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating answer: {str(e)}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics for experts"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Total conversations
                total_convs = session.execute(
                    text("SELECT COUNT(*) FROM ava_conversations")
                ).scalar()
                
                # Pending review
                pending = session.execute(
                    text("SELECT COUNT(*) FROM ava_conversations WHERE expert_approved IS NULL")
                ).scalar()
                
                # Low confidence
                low_confidence = session.execute(
                    text("SELECT COUNT(*) FROM ava_conversations WHERE confidence_score < 0.8")
                ).scalar()
                
                # Today's conversations
                today = session.execute(
                    text("SELECT COUNT(*) FROM ava_conversations WHERE DATE(created_at) = CURRENT_DATE")
                ).scalar()
                
                # Average confidence
                avg_confidence = session.execute(
                    text("SELECT AVG(confidence_score) FROM ava_conversations WHERE confidence_score IS NOT NULL")
                ).scalar()
                
                return {
                    "total_conversations": total_convs or 0,
                    "pending_review": pending or 0,
                    "low_confidence": low_confidence or 0,
                    "today_conversations": today or 0,
                    "avg_confidence": float(avg_confidence) if avg_confidence else 0.0,
                    "approval_rate": ((total_convs - pending) / total_convs * 100) if total_convs > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "total_conversations": 0,
                "pending_review": 0,
                "low_confidence": 0,
                "today_conversations": 0,
                "avg_confidence": 0.0,
                "approval_rate": 0.0
            }

# Initialize dashboard
dashboard = AgronomicDashboard()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main agronomic dashboard"""
    stats = await dashboard.get_statistics()
    conversations = await dashboard.get_pending_conversations(20)
    
    return templates.TemplateResponse("agronomic_dashboard.html", {
        "request": request,
        "stats": stats,
        "conversations": conversations
    })

@app.get("/api/conversations")
async def get_conversations(limit: int = 50):
    """API endpoint for conversations"""
    conversations = await dashboard.get_pending_conversations(limit)
    return {"conversations": conversations}

@app.post("/api/approve/{conversation_id}")
async def approve_conversation(conversation_id: int, approved: bool, notes: str = ""):
    """Approve or reject a conversation"""
    success = await dashboard.approve_conversation(conversation_id, approved, notes)
    
    if success:
        return {"success": True, "message": f"Conversation {'approved' if approved else 'rejected'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update conversation")

@app.post("/api/update-answer/{conversation_id}")
async def update_answer(conversation_id: int, new_answer: str, expert_notes: str = ""):
    """Expert updates an answer"""
    success = await dashboard.update_answer(conversation_id, new_answer, expert_notes)
    
    if success:
        return {"success": True, "message": "Answer updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update answer")

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    stats = await dashboard.get_statistics()
    return stats

@app.get("/health")
async def health_check():
    """Health check"""
    db_healthy = await db_ops.health_check()
    
    return {
        "service": "Agronomic Dashboard",
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
        "port": 8003,
        "purpose": "Expert monitoring and conversation approval"
    }

if __name__ == "__main__":
    import uvicorn
    print("🌾 Starting AVA OLO Agronomic Dashboard on port 8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)