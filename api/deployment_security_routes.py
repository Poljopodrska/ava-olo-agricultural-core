#!/usr/bin/env python3
"""
Deployment Security API Routes
Provides endpoints to verify deployment source and security
"""

from fastapi import APIRouter
from modules.core.git_verification import get_deployment_source, deployment_info

router = APIRouter(prefix="/api/deployment", tags=["deployment-security"])

@router.get("/source")
async def deployment_source():
    """Get deployment source information"""
    return get_deployment_source()

@router.get("/audit")
async def deployment_audit():
    """Complete deployment security audit"""
    source = get_deployment_source()
    
    # Additional audit information
    audit = {
        "deployment": source['deployment_source'],
        "security": source['security'],
        "audit": {
            "passed": source['security']['from_github_actions'],
            "git_traceable": source['security']['traceable_to_git'],
            "risk_level": "LOW" if source['security']['from_github_actions'] else "CRITICAL",
            "compliance": "COMPLIANT" if source['security']['from_github_actions'] else "NON_COMPLIANT"
        },
        "recommendations": [] if source['security']['from_github_actions'] else [
            "This deployment bypassed Git!",
            "Investigate how this deployment occurred",
            "Review security procedures",
            "Consider blocking non-Git deployments"
        ],
        "timestamp": source['timestamp']
    }
    
    return audit

@router.get("/verify")
async def verify_deployment():
    """Quick verification endpoint"""
    source = get_deployment_source()
    return {
        "secure": source['security']['from_github_actions'],
        "github_sha": source['deployment_source']['github_sha'],
        "warning": source['security']['warning']
    }