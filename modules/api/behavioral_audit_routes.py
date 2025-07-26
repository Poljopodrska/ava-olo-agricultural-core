#!/usr/bin/env python3
"""
Behavioral Audit Routes - API endpoints for CAVA behavioral testing
Tests real conversation behaviors, not just component functionality
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

from modules.cava.behavioral_audit import CAVABehavioralAudit, run_quick_mango_test

router = APIRouter(prefix="/api/v1/cava/behavioral", tags=["cava-behavioral-audit"])

class AuditResponse(BaseModel):
    status: str
    timestamp: str
    data: Dict[str, Any]

@router.post("/audit/full")
async def run_full_behavioral_audit():
    """
    Run complete behavioral audit with 8 realistic conversation tests
    Tests actual memory behavior, not just storage functionality
    """
    
    print("🧪 Starting full CAVA behavioral audit...")
    
    try:
        audit = CAVABehavioralAudit()
        results = await audit.run_full_behavioral_audit()
        
        return AuditResponse(
            status="completed",
            timestamp=datetime.now().isoformat(),
            data={
                "audit_results": results,
                "summary": {
                    "total_score": results["overall_score"],
                    "max_score": results["max_score"],
                    "percentage": results["percentage"],
                    "memory_quality": results["memory_quality"],
                    "tests_run": len(results["tests"]),
                    "tests_passed": len([t for t in results["tests"].values() if t.get("final_score", 0) >= t.get("weight", 10) * 0.6])
                },
                "interpretation": {
                    "excellent": results["percentage"] >= 85,
                    "good": 70 <= results["percentage"] < 85,
                    "fair": 55 <= results["percentage"] < 70,
                    "poor": 40 <= results["percentage"] < 55,
                    "failing": results["percentage"] < 40,
                    "production_ready": results["percentage"] >= 64
                }
            }
        )
        
    except Exception as e:
        print(f"❌ Behavioral audit failed: {str(e)}")
        return AuditResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "error": str(e),
                "recommendation": "Check CAVA system status and try again"
            }
        )

@router.post("/audit/quick")
async def run_quick_behavioral_test():
    """
    Run quick Bulgarian mango test - the core MANGO TEST scenario
    Fast verification of basic memory functionality
    """
    
    print("🥭 Running quick Bulgarian mango test...")
    
    try:
        result = await run_quick_mango_test()
        
        return AuditResponse(
            status="completed",
            timestamp=datetime.now().isoformat(),
            data={
                "test_result": result,
                "mango_test_passed": result["passed"],
                "memory_working": result["memory_working"],
                "score": result["result"].get("score", 0),
                "max_score": 15,
                "percentage": (result["result"].get("score", 0) / 15) * 100,
                "quick_assessment": "PASS" if result["passed"] else "FAIL"
            }
        )
        
    except Exception as e:
        print(f"❌ Quick mango test failed: {str(e)}")
        return AuditResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "error": str(e),
                "mango_test_passed": False,
                "memory_working": False
            }
        )

@router.get("/audit/status")
async def get_behavioral_audit_status():
    """
    Get current status of behavioral audit system
    Shows if audit can run and what it tests
    """
    
    try:
        # Check if we can create audit instance
        audit = CAVABehavioralAudit()
        
        status_info = {
            "audit_available": True,
            "test_scenarios": [
                {
                    "name": "Bulgarian Mango Memory",
                    "description": "Core MANGO TEST - exotic crop/country memory",
                    "weight": 15,
                    "critical": True
                },
                {
                    "name": "Croatian Corn Continuity",
                    "description": "Memory persistence across gaps",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "German Wheat Weather",
                    "description": "Contextual advice based on farm details",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "Italian Tomato Timeline", 
                    "description": "Temporal memory across crop cycle",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "Polish Potato Problem",
                    "description": "Problem-solving continuity",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "Spanish Sunflower Scale",
                    "description": "Farm size memory and recommendations",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "French Fruit Fertilizer",
                    "description": "Specific recommendation memory",
                    "weight": 10,
                    "critical": False
                },
                {
                    "name": "Dutch Dairy Details",
                    "description": "Complex operation memory",
                    "weight": 5,
                    "critical": False
                }
            ],
            "total_possible_score": 80,
            "pass_threshold": 64,  # 80% required
            "cannot_be_gamed": "Tests actual conversation behavior, not just storage",
            "mango_rule_compliant": "Tests universal scalability with exotic combinations"
        }
        
        return AuditResponse(
            status="available",
            timestamp=datetime.now().isoformat(),
            data=status_info
        )
        
    except Exception as e:
        return AuditResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "audit_available": False,
                "error": str(e),
                "recommendation": "Check CAVA system components"
            }
        )

@router.post("/test/individual/{test_name}")
async def run_individual_test(test_name: str):
    """
    Run individual behavioral test by name
    Useful for debugging specific memory scenarios
    """
    
    print(f"🧪 Running individual test: {test_name}")
    
    try:
        audit = CAVABehavioralAudit()
        
        # Map test names to functions
        test_functions = {
            "bulgarian_mango": audit.test_bulgarian_mango_memory,
            "croatian_corn": audit.test_croatian_corn_continuity,
            "german_wheat": audit.test_german_wheat_weather,
            "italian_tomato": audit.test_italian_tomato_timeline,
            "polish_potato": audit.test_polish_potato_problem,
            "spanish_sunflower": audit.test_spanish_sunflower_scale,
            "french_fruit": audit.test_french_fruit_fertilizer,
            "dutch_dairy": audit.test_dutch_dairy_details
        }
        
        if test_name.lower() not in test_functions:
            raise HTTPException(
                status_code=400, 
                detail=f"Test '{test_name}' not found. Available: {list(test_functions.keys())}"
            )
        
        test_func = test_functions[test_name.lower()]
        result = await test_func()
        
        return AuditResponse(
            status="completed",
            timestamp=datetime.now().isoformat(),
            data={
                "test_name": test_name,
                "result": result,
                "score": result.get("score", 0),
                "success": result.get("score", 0) >= 6,  # 60% threshold
                "error": result.get("error")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return AuditResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "test_name": test_name,
                "error": str(e),
                "result": None
            }
        )

@router.get("/compare/component-vs-behavioral")
async def compare_audit_types():
    """
    Compare component audit vs behavioral audit results
    Shows the difference between storage and actual memory usage
    """
    
    try:
        # Get current component audit results
        from modules.api.cava_audit_routes import get_cava_audit_status
        component_audit = await get_cava_audit_status()
        
        # Run quick behavioral test
        behavioral_result = await run_quick_mango_test()
        
        comparison = {
            "component_audit": {
                "score": component_audit.get("score", 0),
                "max_score": component_audit.get("max_score", 60),
                "percentage": component_audit.get("percentage", 0),
                "focus": "Tests if components store and retrieve data"
            },
            "behavioral_audit": {
                "score": behavioral_result["result"].get("score", 0),
                "max_score": 15,
                "percentage": (behavioral_result["result"].get("score", 0) / 15) * 100,
                "focus": "Tests if memory is actually used in conversations"
            },
            "comparison": {
                "component_higher": component_audit.get("percentage", 0) > (behavioral_result["result"].get("score", 0) / 15) * 100,
                "behavioral_working": behavioral_result["memory_working"],
                "gap_detected": abs(component_audit.get("percentage", 0) - (behavioral_result["result"].get("score", 0) / 15) * 100) > 20,
                "interpretation": "Component audit tests storage; behavioral audit tests usage"
            },
            "recommendations": []
        }
        
        # Add recommendations based on comparison
        if comparison["comparison"]["component_higher"] and not comparison["comparison"]["behavioral_working"]:
            comparison["recommendations"].extend([
                "Components store data but don't use it in conversations",
                "Check if context is properly passed to LLM",
                "Verify conversation history inclusion in prompts"
            ])
        elif comparison["comparison"]["behavioral_working"] and component_audit.get("percentage", 0) < 50:
            comparison["recommendations"].extend([
                "Memory works but component audit shows issues",
                "May be using fallback mechanisms",
                "Check component audit for storage optimization"
            ])
        else:
            comparison["recommendations"].append("Both audits align - system working as expected")
        
        return AuditResponse(
            status="completed",
            timestamp=datetime.now().isoformat(),
            data=comparison
        )
        
    except Exception as e:
        return AuditResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            data={
                "error": str(e),
                "recommendation": "Check both audit systems are available"
            }
        )