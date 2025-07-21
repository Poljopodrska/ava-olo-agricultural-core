"""
AVA OLO Agronomic Dashboard Module
Implements conversation approval system for agricultural experts
"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
from modules.core.database_manager import get_db_manager
from modules.core.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/agronomic", tags=["agronomic_dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def agronomic_dashboard(request: Request):
    """Main agronomic dashboard with conversation approval system"""
    db_manager = get_db_manager()
    
    # Get all conversations with approval status
    conversations = {"unapproved": [], "approved": []}
    
    try:
        # Query to get all conversations with approval status
        query = """
        SELECT 
            c.id as conversation_id,
            c.farmer_id,
            f.name as farmer_name,
            c.timestamp,
            c.message,
            c.response,
            c.approved,
            c.approval_timestamp,
            c.approved_by
        FROM conversations c
        JOIN farmers f ON c.farmer_id = f.id
        ORDER BY c.approved ASC, c.timestamp DESC
        LIMIT 100
        """
        
        result = await db_manager.execute_query(query)
        
        if result and result.get('success'):
            rows = result.get('data', [])
            for row in rows:
                conversation = {
                    'id': row[0],
                    'farmer_id': row[1],
                    'farmer_name': row[2],
                    'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else '',
                    'message': row[4] or '',
                    'response': row[5] or '',
                    'approved': row[6],
                    'approval_timestamp': row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                    'approved_by': row[8]
                }
                
                # Get preview (last 2-3 lines of conversation)
                message_lines = conversation['message'].split('\n')[-3:]
                conversation['preview'] = '\n'.join(message_lines)
                
                if conversation['approved']:
                    conversations['approved'].append(conversation)
                else:
                    conversations['unapproved'].append(conversation)
    
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
    
    return templates.TemplateResponse("agronomic_dashboard.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": None
    })

@router.get("/conversation/{conversation_id}", response_class=HTMLResponse)
async def get_conversation_details(request: Request, conversation_id: int):
    """Get detailed view of a specific conversation"""
    db_manager = get_db_manager()
    
    # Get all conversations for sidebar
    conversations = {"unapproved": [], "approved": []}
    selected_conversation = None
    
    try:
        # First get all conversations for sidebar
        all_query = """
        SELECT 
            c.id as conversation_id,
            c.farmer_id,
            f.name as farmer_name,
            c.timestamp,
            c.message,
            c.response,
            c.approved,
            c.approval_timestamp,
            c.approved_by
        FROM conversations c
        JOIN farmers f ON c.farmer_id = f.id
        ORDER BY c.approved ASC, c.timestamp DESC
        LIMIT 100
        """
        
        all_result = await db_manager.execute_query(all_query)
        
        if all_result and all_result.get('success'):
            rows = all_result.get('data', [])
            for row in rows:
                conversation = {
                    'id': row[0],
                    'farmer_id': row[1],
                    'farmer_name': row[2],
                    'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else '',
                    'message': row[4] or '',
                    'response': row[5] or '',
                    'approved': row[6],
                    'approval_timestamp': row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                    'approved_by': row[8]
                }
                
                # Get preview
                message_lines = conversation['message'].split('\n')[-3:]
                conversation['preview'] = '\n'.join(message_lines)
                
                if conversation['id'] == conversation_id:
                    selected_conversation = conversation
                
                if conversation['approved']:
                    conversations['approved'].append(conversation)
                else:
                    conversations['unapproved'].append(conversation)
        
        # Get full conversation history for selected conversation
        if selected_conversation:
            history_query = """
            SELECT 
                timestamp,
                message,
                response,
                approved
            FROM conversations
            WHERE farmer_id = %s
            ORDER BY timestamp ASC
            """
            
            history_result = await db_manager.execute_query(
                history_query, 
                (selected_conversation['farmer_id'],)
            )
            
            if history_result and history_result.get('success'):
                history = []
                for row in history_result.get('data', []):
                    history.append({
                        'timestamp': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '',
                        'message': row[1] or '',
                        'response': row[2] or '',
                        'approved': row[3]
                    })
                selected_conversation['history'] = history
    
    except Exception as e:
        logger.error(f"Error fetching conversation details: {str(e)}")
    
    return templates.TemplateResponse("agronomic_dashboard.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": selected_conversation
    })

@router.post("/approve/{conversation_id}", response_class=JSONResponse)
async def approve_conversation(conversation_id: int):
    """Approve a specific conversation"""
    db_manager = get_db_manager()
    
    try:
        query = """
        UPDATE conversations
        SET approved = true,
            approval_timestamp = CURRENT_TIMESTAMP,
            approved_by = 'agronomist'
        WHERE id = %s
        """
        
        result = await db_manager.execute_query(query, (conversation_id,))
        
        if result and result.get('success'):
            return {"success": True, "message": "Conversation approved successfully"}
        else:
            return {"success": False, "message": "Failed to approve conversation"}
    
    except Exception as e:
        logger.error(f"Error approving conversation: {str(e)}")
        return {"success": False, "message": str(e)}

@router.post("/answer/{conversation_id}", response_class=JSONResponse)
async def answer_conversation(conversation_id: int, answer: str = Form(...)):
    """Send a custom answer to a specific conversation"""
    db_manager = get_db_manager()
    
    try:
        # Get farmer_id for this conversation
        get_farmer_query = """
        SELECT farmer_id FROM conversations WHERE id = %s
        """
        farmer_result = await db_manager.execute_query(get_farmer_query, (conversation_id,))
        
        if farmer_result and farmer_result.get('success') and farmer_result.get('data'):
            farmer_id = farmer_result.get('data')[0][0]
            
            # Insert new conversation with the answer
            insert_query = """
            INSERT INTO conversations (farmer_id, message, response, approved, approval_timestamp, approved_by)
            VALUES (%s, %s, %s, true, CURRENT_TIMESTAMP, 'agronomist')
            """
            
            result = await db_manager.execute_query(
                insert_query, 
                (farmer_id, f"Manual response to conversation {conversation_id}", answer)
            )
            
            if result and result.get('success'):
                return {"success": True, "message": "Answer sent successfully"}
            else:
                return {"success": False, "message": "Failed to send answer"}
        else:
            return {"success": False, "message": "Conversation not found"}
    
    except Exception as e:
        logger.error(f"Error sending answer: {str(e)}")
        return {"success": False, "message": str(e)}

@router.post("/send_general_message", response_class=JSONResponse)
async def send_general_message(farmer_id: int = Form(...), message: str = Form(...)):
    """Send a general message to a farmer"""
    db_manager = get_db_manager()
    
    try:
        # Insert new conversation with the general message
        insert_query = """
        INSERT INTO conversations (farmer_id, message, response, approved, approval_timestamp, approved_by)
        VALUES (%s, %s, %s, true, CURRENT_TIMESTAMP, 'agronomist')
        """
        
        result = await db_manager.execute_query(
            insert_query, 
            (farmer_id, "General message from agronomist", message)
        )
        
        if result and result.get('success'):
            return {"success": True, "message": "Message sent successfully"}
        else:
            return {"success": False, "message": "Failed to send message"}
    
    except Exception as e:
        logger.error(f"Error sending general message: {str(e)}")
        return {"success": False, "message": str(e)}