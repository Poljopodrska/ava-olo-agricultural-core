#!/usr/bin/env python3
"""
Deployment API routes for AVA OLO Monitoring Dashboards
Handles deployment verification, health checks, and audit endpoints
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..core.config import VERSION, BUILD_ID, DEPLOYMENT_TIMESTAMP, get_current_service_version
from ..core.deployment_manager import get_deployment_manager, verify_deployment, get_deployment_info

router = APIRouter(prefix="/api/deployment", tags=["deployment"])

@router.get("/verify")
async def deployment_verify():
    """Verify deployment and return version information"""
    try:
        deployment_info = get_deployment_info()
        verification = verify_deployment()
        
        return JSONResponse({
            "status": "operational",
            "version": VERSION,
            "build_id": BUILD_ID,
            "deployment_timestamp": DEPLOYMENT_TIMESTAMP,
            "verification": verification,
            "deployment_info": deployment_info,
            "yellow_box_visible": True,
            "environment": "production" if os.getenv('AWS_EXECUTION_ENV') else "local"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "version": VERSION,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/health")
async def deployment_health():
    """Health check endpoint for deployment verification"""
    try:
        manager = get_deployment_manager()
        manifest_exists = manager._check_manifest_exists()
        
        return JSONResponse({
            "status": "healthy",
            "version": VERSION,
            "build_id": BUILD_ID,
            "service": "monitoring-dashboards",
            "timestamp": datetime.now().isoformat(),
            "manifest_exists": manifest_exists,
            "deployment_valid": True
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "version": VERSION
        }, status_code=503)

# Audit endpoints
audit_router = APIRouter(prefix="/api/audit", tags=["audit"])

@audit_router.get("/deployment")
async def audit_deployment():
    """Comprehensive deployment audit"""
    try:
        # Get deployment info
        deployment_info = get_deployment_info()
        
        # Check manifest
        manifest_path = Path("monitoring-dashboards_manifest.json")
        manifest_data = None
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest_data = json.load(f)
        
        # Check version files
        version_files = {}
        for file in ["version_history.json", "deployment_trigger.txt", "auto_cache_bust_*.txt"]:
            for path in Path(".").glob(file):
                version_files[str(path)] = {
                    "exists": True,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
        
        return JSONResponse({
            "deployment_info": deployment_info,
            "manifest": manifest_data,
            "version_files": version_files,
            "environment_vars": {
                "AWS_EXECUTION_ENV": os.getenv('AWS_EXECUTION_ENV', 'not_set'),
                "ENVIRONMENT": os.getenv('ENVIRONMENT', 'not_set'),
                "SERVICE_VERSION": os.getenv('SERVICE_VERSION', 'not_set')
            },
            "current_version": get_current_service_version(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@audit_router.get("/file-comparison")
async def audit_file_comparison():
    """Compare deployed files with expected structure"""
    try:
        expected_files = [
            "main.py",
            "requirements.txt",
            "database_operations.py",
            "database_pool.py",
            "modules/core/config.py",
            "modules/core/database_manager.py",
            "modules/core/deployment_manager.py",
            "modules/api/deployment_routes.py"
        ]
        
        file_status = {}
        for file_path in expected_files:
            path = Path(file_path)
            if path.exists():
                stat = path.stat()
                file_status[file_path] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_kb": round(stat.st_size / 1024, 2)
                }
            else:
                file_status[file_path] = {
                    "exists": False,
                    "error": "File not found"
                }
        
        # Check main.py size
        main_py_status = file_status.get("main.py", {})
        main_py_size_kb = main_py_status.get("size_kb", 0)
        
        return JSONResponse({
            "files": file_status,
            "main_py_size_kb": main_py_size_kb,
            "main_py_under_100kb": main_py_size_kb < 100,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@audit_router.get("/import-tree")
async def audit_import_tree():
    """Show module import structure"""
    try:
        import_tree = {
            "main.py": {
                "imports": [
                    "modules.api.deployment_routes",
                    "modules.api.database_routes",
                    "modules.api.health_routes",
                    "modules.api.business_routes",
                    "modules.core.config",
                    "modules.core.database_manager",
                    "modules.core.deployment_manager"
                ]
            },
            "modules": {
                "core": ["config.py", "database_manager.py", "deployment_manager.py"],
                "api": ["deployment_routes.py", "database_routes.py", "health_routes.py", "business_routes.py"]
            }
        }
        
        return JSONResponse({
            "import_tree": import_tree,
            "modularized": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@audit_router.get("/summary")
async def audit_summary():
    """Get deployment audit summary"""
    try:
        # Collect all audit data
        deployment_data = await audit_deployment()
        file_data = await audit_file_comparison()
        import_data = await audit_import_tree()
        
        # Parse responses
        deployment_json = json.loads(deployment_data.body)
        file_json = json.loads(file_data.body)
        import_json = json.loads(import_data.body)
        
        summary = {
            "version": VERSION,
            "build_id": BUILD_ID,
            "deployment_valid": deployment_json.get("deployment_info", {}).get("manifest_exists", False),
            "main_py_size_ok": file_json.get("main_py_under_100kb", False),
            "modularized": import_json.get("modularized", False),
            "checks_passed": {
                "deployment": "deployment_info" in deployment_json,
                "files": "files" in file_json,
                "imports": "import_tree" in import_json
            },
            "timestamp": datetime.now().isoformat()
        }
        
        summary["all_checks_passed"] = all(summary["checks_passed"].values())
        
        return JSONResponse(summary)
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)