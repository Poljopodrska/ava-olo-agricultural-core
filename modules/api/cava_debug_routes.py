#!/usr/bin/env python3
"""
CAVA Production Debug Routes
Comprehensive diagnostics to identify why context isn't working on AWS
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import inspect
import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from modules.core.database_manager import DatabaseManager

router = APIRouter(prefix="/api/v1/cava/debug", tags=["cava-debug"])

class DebugResponse(BaseModel):
    status: str
    timestamp: str
    data: Dict[str, Any]

@router.get("/endpoints")
async def debug_all_chat_endpoints():
    """Show all registered chat endpoints to find which one is actually being used"""
    try:
        from main import app
        
        routes = []
        chat_routes = []
        
        for route in app.routes:
            route_info = {
                "path": str(route.path),
                "methods": list(route.methods) if hasattr(route, 'methods') else [],
                "endpoint": str(route.endpoint) if hasattr(route, 'endpoint') else "unknown",
                "module": getattr(route.endpoint, '__module__', 'unknown') if hasattr(route, 'endpoint') else "unknown"
            }
            
            routes.append(route_info)
            
            # Focus on chat routes
            if "chat" in str(route.path).lower():
                chat_routes.append(route_info)
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data={
                "total_routes": len(routes),
                "chat_routes": chat_routes,
                "critical_issue": "Multiple /api/v1/chat endpoints found" if len([r for r in chat_routes if r["path"] == "/api/v1/chat"]) > 1 else None,
                "routes_preview": routes[:10]  # First 10 routes for context
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        )

@router.post("/trace-chat")
async def trace_chat_execution(phone: str = "+385991234567"):
    """Trace exactly what happens in a chat call step by step"""
    
    trace = {
        "steps": [],
        "errors": [],
        "context_found": False,
        "llm_called": False,
        "cava_active": False
    }
    
    try:
        db_manager = DatabaseManager()
        
        # Step 1: Test direct DB access
        try:
            async with db_manager.get_connection_async() as conn:
                await conn.execute("""
                    INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                    VALUES ($1, 'user', $2, NOW())
                """, phone, f"Debug trace message at {datetime.now().isoformat()}")
                
                trace["steps"].append("✅ Direct DB write works")
                
                # Check if message was stored
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM chat_messages WHERE wa_phone_number = $1
                """, phone)
                
                trace["steps"].append(f"✅ Messages in DB: {count}")
                
        except Exception as e:
            trace["errors"].append(f"❌ DB write failed: {str(e)}")
        
        # Step 2: Test CAVA memory retrieval
        try:
            from modules.cava.conversation_memory import CAVAMemory
            cava = CAVAMemory()
            
            context = await cava.get_conversation_context(phone)
            
            trace["context_found"] = len(context.get('messages', [])) > 0
            trace["steps"].append(f"✅ Context retrieval: {len(context.get('messages', []))} messages")
            trace["context_summary"] = context.get('context_summary', 'No summary')
            
            if context.get('messages'):
                trace["latest_message"] = context['messages'][-1].get('content', '')[:100]
            
            trace["cava_active"] = True
            
        except Exception as e:
            trace["errors"].append(f"❌ CAVA context retrieval failed: {str(e)}")
        
        # Step 3: Test enhanced context
        try:
            if trace["cava_active"]:
                enhanced_context = await cava.get_enhanced_context(phone)
                trace["steps"].append(f"✅ Enhanced context: {len(enhanced_context.get('stored_facts', []))} facts")
                trace["enhanced_summary"] = enhanced_context.get('context_summary', '')[:200]
        except Exception as e:
            trace["errors"].append(f"❌ Enhanced context failed: {str(e)}")
        
        # Step 4: Check chat endpoint code
        try:
            from modules.api import chat_routes
            
            # Get the source code of the chat endpoint
            source_code = inspect.getsource(chat_routes.chat_endpoint)
            
            trace["chat_module_file"] = getattr(chat_routes, '__file__', 'unknown')
            trace["has_cava_code"] = "get_enhanced_context" in source_code
            trace["has_old_fallback"] = "temporarily unavailable" in source_code.lower()
            trace["code_size"] = len(source_code)
            
            # Check for specific CAVA patterns
            cava_patterns = [
                "CAVAMemory",
                "get_enhanced_context", 
                "conversation_messages_for_llm",
                "store_extracted_facts",
                "context_summary"
            ]
            
            trace["cava_patterns_found"] = {
                pattern: pattern in source_code for pattern in cava_patterns
            }
            
            trace["steps"].append(f"✅ Chat endpoint code analyzed: {sum(trace['cava_patterns_found'].values())}/5 CAVA patterns found")
            
        except Exception as e:
            trace["errors"].append(f"❌ Code inspection failed: {str(e)}")
        
        # Step 5: Check OpenAI client
        try:
            from modules.chat.openai_key_manager import get_openai_client
            client = get_openai_client()
            trace["openai_available"] = client is not None
            trace["steps"].append(f"✅ OpenAI client: {'Available' if client else 'Not available'}")
        except Exception as e:
            trace["errors"].append(f"❌ OpenAI check failed: {str(e)}")
        
        return DebugResponse(
            status="success" if not trace["errors"] else "partial",
            timestamp=datetime.now().isoformat(),
            data=trace
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e), "trace": trace}
        )

@router.get("/active-modules")
async def check_active_modules():
    """Show which modules are actually loaded in memory"""
    try:
        cava_modules = {}
        
        modules_to_check = [
            "modules.cava.conversation_memory",
            "modules.api.chat_routes",
            "modules.cava.fact_extractor",
            "modules.chat.routes",  # Old conflicting module
            "main"
        ]
        
        for module_name in modules_to_check:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                cava_modules[module_name] = {
                    "loaded": True,
                    "file": getattr(module, '__file__', None),
                    "size": len(str(module)) if module else 0
                }
                
                # Check for specific functions if it's a CAVA module
                if "cava" in module_name.lower() or "chat" in module_name.lower():
                    functions = [name for name in dir(module) if not name.startswith('_')]
                    cava_modules[module_name]["functions"] = functions[:10]  # First 10 functions
            else:
                cava_modules[module_name] = {"loaded": False}
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data={
                "python_path": sys.path[:3],
                "working_directory": os.getcwd(),
                "cava_modules": cava_modules,
                "total_modules_loaded": len(sys.modules),
                "issue_detected": "modules.chat.routes" in [name for name, info in cava_modules.items() if info.get("loaded")]
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        )

@router.post("/test-memory-flow")
async def test_complete_memory_flow():
    """Test the complete memory flow end-to-end"""
    phone = f"+385991234{datetime.now().strftime('%S')}"  # Unique phone
    
    try:
        db_manager = DatabaseManager()
        results = []
        
        # Test scenario: Farmer talks about mangoes, then asks follow-up
        messages = [
            "Hello, I am a Bulgarian farmer and I grow mangoes on 3 hectares",
            "What fertilizer should I use for my mango trees?",
            "When is the best time to harvest mangoes in Bulgaria?"
        ]
        
        for i, msg in enumerate(messages):
            step_result = {
                "step": i + 1,
                "message": msg,
                "errors": []
            }
            
            try:
                # Store user message
                async with db_manager.get_connection_async() as conn:
                    await conn.execute("""
                        INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                        VALUES ($1, 'user', $2, NOW())
                    """, phone, msg)
                
                # Get context like chat endpoint would
                from modules.cava.conversation_memory import CAVAMemory
                cava = CAVAMemory()
                
                context = await cava.get_enhanced_context(phone)
                
                # Check what LLM would receive
                system_content = f"Context about this farmer: {context['context_summary']}"
                recent_messages = await cava.get_conversation_messages_for_llm(phone, limit=5)
                
                # Simulate LLM response
                response = f"Thank you for your question about {'mangoes' if 'mango' in context['context_summary'].lower() else 'farming'}. Based on your previous messages, I can help."
                
                # Store assistant response
                async with db_manager.get_connection_async() as conn:
                    await conn.execute("""
                        INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                        VALUES ($1, 'assistant', $2, NOW())
                    """, phone, response)
                
                step_result.update({
                    "context_has_history": len(context.get('messages', [])) > 0,
                    "context_summary": context['context_summary'],
                    "remembers_mangoes": "mango" in context['context_summary'].lower(),
                    "remembers_bulgaria": "bulgaria" in context['context_summary'].lower(),
                    "remembers_hectares": "hectare" in context['context_summary'].lower() or "3" in context['context_summary'],
                    "llm_messages_count": len(recent_messages),
                    "system_message": system_content[:100] + "..."
                })
                
            except Exception as e:
                step_result["errors"].append(str(e))
            
            results.append(step_result)
        
        # Final analysis
        final_context = await cava.get_enhanced_context(phone)
        
        memory_test = {
            "all_messages_stored": len(final_context.get('messages', [])) >= 6,  # 3 user + 3 assistant
            "context_complete": bool(final_context.get('context_summary')),
            "remembers_key_facts": all([
                "mango" in final_context['context_summary'].lower(),
                "bulgaria" in final_context['context_summary'].lower()
            ]),
            "memory_working": False
        }
        
        memory_test["memory_working"] = all([
            memory_test["all_messages_stored"],
            memory_test["context_complete"], 
            memory_test["remembers_key_facts"]
        ])
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data={
                "test_phone": phone,
                "step_results": results,
                "final_context_summary": final_context.get('context_summary', ''),
                "final_message_count": len(final_context.get('messages', [])),
                "memory_test": memory_test,
                "diagnosis": "Memory system works - issue must be in chat endpoint routing" if memory_test["memory_working"] else "Memory system has issues"
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        )

@router.get("/which-chat-active")
async def which_chat_endpoint_is_active():
    """Determine which chat endpoint is actually being used by checking handlers"""
    
    try:
        from main import app
        
        # Check all possible chat endpoints
        chat_endpoints = {}
        
        for route in app.routes:
            path = str(route.path)
            if "chat" in path.lower() and hasattr(route, 'endpoint'):
                
                # Get detailed info about the endpoint
                endpoint_info = {
                    "path": path,
                    "methods": list(route.methods) if hasattr(route, 'methods') else [],
                    "function_name": route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else "unknown",
                    "module": getattr(route.endpoint, '__module__', 'unknown'),
                    "endpoint_object": str(route.endpoint)
                }
                
                # Try to get source code size to differentiate
                try:
                    source = inspect.getsource(route.endpoint)
                    endpoint_info["source_size"] = len(source)
                    endpoint_info["has_cava"] = "CAVAMemory" in source or "get_enhanced_context" in source
                    endpoint_info["is_simple"] = len(source) < 1000
                except:
                    endpoint_info["source_size"] = 0
                    endpoint_info["has_cava"] = False
                    endpoint_info["is_simple"] = True
                
                chat_endpoints[path] = endpoint_info
        
        # Determine which is likely being used
        primary_chat = None
        for path, info in chat_endpoints.items():
            if path == "/api/v1/chat" and info.get("has_cava"):
                primary_chat = path
                break
        
        if not primary_chat:
            # Find any /api/v1/chat endpoint
            primary_chat = next((path for path in chat_endpoints.keys() if path == "/api/v1/chat"), None)
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data={
                "chat_endpoints": chat_endpoints,
                "primary_chat_endpoint": primary_chat,
                "likely_issue": "Multiple endpoints conflict" if len([p for p in chat_endpoints.keys() if "/chat" in p]) > 2 else None,
                "recommendation": f"UI probably calls {primary_chat}" if primary_chat else "No clear primary endpoint"
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        )

@router.post("/force-fix")
async def force_fix_chat_endpoint():
    """Emergency endpoint to force reload chat modules and fix routing"""
    
    try:
        import importlib
        
        fix_results = {
            "actions_taken": [],
            "modules_reloaded": [],
            "errors": []
        }
        
        # Step 1: Remove problematic modules from cache
        modules_to_reload = [
            "modules.api.chat_routes",
            "modules.cava.conversation_memory",
            "modules.cava.fact_extractor"
        ]
        
        for module_name in modules_to_reload:
            try:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    fix_results["modules_reloaded"].append(module_name)
                    fix_results["actions_taken"].append(f"Removed {module_name} from cache")
            except Exception as e:
                fix_results["errors"].append(f"Failed to remove {module_name}: {str(e)}")
        
        # Step 2: Force reload main modules
        try:
            from modules.api import chat_routes
            importlib.reload(chat_routes)
            fix_results["actions_taken"].append("Reloaded chat_routes module")
            
            # Check if CAVA code is now active
            source = inspect.getsource(chat_routes.chat_endpoint)
            has_cava_now = "get_enhanced_context" in source
            fix_results["cava_active_after_reload"] = has_cava_now
            
        except Exception as e:
            fix_results["errors"].append(f"Failed to reload chat_routes: {str(e)}")
        
        # Step 3: Check current state
        try:
            from main import app
            chat_routes_count = len([r for r in app.routes if "/chat" in str(r.path).lower()])
            fix_results["current_chat_routes"] = chat_routes_count
        except Exception as e:
            fix_results["errors"].append(f"Failed to check routes: {str(e)}")
        
        status = "success" if not fix_results["errors"] else "partial"
        
        return DebugResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            data={
                **fix_results,
                "recommendation": "ECS service restart required for permanent fix" if fix_results["errors"] else "Module reload successful",
                "next_steps": [
                    "Test /api/v1/chat endpoint",
                    "Run CAVA audit to verify improvement",
                    "Consider ECS service restart if issues persist"
                ]
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "error": str(e),
                "recommendation": "Manual intervention required"
            }
        )

@router.get("/aws-vs-local")
async def compare_aws_vs_local():
    """Compare AWS deployment vs local expectations"""
    
    try:
        comparison = {
            "environment": {},
            "modules": {},
            "database": {},
            "routing": {}
        }
        
        # Environment check
        comparison["environment"] = {
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "working_dir": os.getcwd(),
            "is_container": bool(os.getenv("ECS_CONTAINER_METADATA_URI_V4")),
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))
        }
        
        # Module loading check
        critical_modules = [
            "modules.api.chat_routes",
            "modules.cava.conversation_memory",
            "fastapi"
        ]
        
        for module in critical_modules:
            try:
                if module in sys.modules:
                    mod = sys.modules[module]
                    comparison["modules"][module] = {
                        "loaded": True,
                        "file": getattr(mod, '__file__', 'unknown'),
                        "size": len(str(mod))
                    }
                else:
                    comparison["modules"][module] = {"loaded": False}
            except:
                comparison["modules"][module] = {"error": "Could not inspect"}
        
        # Database check
        try:
            db_manager = DatabaseManager()
            async with db_manager.get_connection_async() as conn:
                # Check tables exist
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name IN ('chat_messages', 'farmer_facts', 'llm_usage_log')
                """)
                
                comparison["database"] = {
                    "connected": True,
                    "cava_tables": [row['table_name'] for row in tables],
                    "table_count": len(tables)
                }
                
                # Check for recent data
                recent_messages = await conn.fetchval("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """)
                comparison["database"]["recent_activity"] = recent_messages > 0
                
        except Exception as e:
            comparison["database"] = {"connected": False, "error": str(e)}
        
        # Routing check
        try:
            from main import app
            routes = [(str(r.path), str(r.endpoint)) for r in app.routes if "chat" in str(r.path).lower()]
            comparison["routing"] = {
                "chat_routes_found": len(routes),
                "routes": routes[:5]  # First 5
            }
        except Exception as e:
            comparison["routing"] = {"error": str(e)}
        
        return DebugResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            data={
                "comparison": comparison,
                "likely_issues": [
                    "Module import order different on AWS" if not comparison["modules"].get("modules.api.chat_routes", {}).get("loaded") else None,
                    "Database connection issues" if not comparison["database"].get("connected") else None,
                    "Route registration order" if comparison["routing"].get("chat_routes_found", 0) != 1 else None
                ],
                "aws_specific_notes": {
                    "container_env": comparison["environment"]["is_container"],
                    "expected_differences": [
                        "File paths will be different",
                        "Module loading order may vary", 
                        "Environment variables from ECS"
                    ]
                }
            }
        )
        
    except Exception as e:
        return DebugResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        )