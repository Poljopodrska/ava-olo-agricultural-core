#!/usr/bin/env python3
"""
Git Deployment Verification Module
Ensures all deployments come from Git commits
"""

import os
import subprocess
from datetime import datetime

def get_git_commit_hash():
    """Get current Git commit hash from repository"""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ).decode().strip()
    except:
        return "GIT_NOT_AVAILABLE"

def get_deployment_source():
    """Get comprehensive deployment source information"""
    github_sha = os.getenv('GITHUB_SHA', 'NOT_FROM_GITHUB')
    github_ref = os.getenv('GITHUB_REF', 'UNKNOWN')
    github_actor = os.getenv('GITHUB_ACTOR', 'UNKNOWN')
    github_workflow = os.getenv('GITHUB_WORKFLOW', 'UNKNOWN')
    build_time = os.getenv('BUILD_TIME', 'UNKNOWN')
    
    # Security assessment
    from_github = github_sha != 'NOT_FROM_GITHUB'
    security_status = "SECURE" if from_github else "INSECURE"
    
    return {
        "deployment_source": {
            "github_sha": github_sha,
            "github_ref": github_ref,
            "github_actor": github_actor,
            "github_workflow": github_workflow,
            "build_time": build_time,
            "git_commit": get_git_commit_hash()
        },
        "security": {
            "from_github_actions": from_github,
            "status": security_status,
            "warning": None if from_github else "CRITICAL: Deployment bypassed Git!",
            "traceable_to_git": from_github
        },
        "timestamp": datetime.utcnow().isoformat()
    }

def verify_deployment_integrity():
    """Verify deployment came from authorized source"""
    source = get_deployment_source()
    
    if not source['security']['from_github_actions']:
        # Log security breach
        print("🚨 SECURITY ALERT: Deployment bypassed GitHub Actions!")
        print(f"   Source: {source}")
        
        # In production, this should:
        # 1. Send alerts to security team
        # 2. Log to security monitoring system
        # 3. Potentially refuse to start the service
    
    return source

# Auto-verify on module import
deployment_info = verify_deployment_integrity()