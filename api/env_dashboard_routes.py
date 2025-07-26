#!/usr/bin/env python3
"""
ENV Dashboard API Routes
Provides endpoints for environment variable monitoring and verification
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime
import os
from pathlib import Path

from modules.env_scanner import ENVScanner
from modules.env_verifier import ENVVerifier

router = APIRouter(prefix="/api/env", tags=["env-dashboard"])

# Cache for scan results (refresh every 5 minutes)
_scan_cache = {
    'last_scan': None,
    'results': None
}

@router.get("/scan")
async def scan_required_envs():
    """Scan codebase for all required ENV variables"""
    global _scan_cache
    
    # Check cache (5 minute TTL)
    if _scan_cache['last_scan']:
        time_diff = (datetime.utcnow() - _scan_cache['last_scan']).total_seconds()
        if time_diff < 300 and _scan_cache['results']:  # 5 minutes
            return {
                **_scan_cache['results'],
                'from_cache': True,
                'cache_age_seconds': int(time_diff)
            }
    
    # Perform fresh scan
    scanner = ENVScanner()
    report = scanner.get_env_usage_report()
    
    result = {
        "required_envs": report['env_list'],
        "count": report['total_envs'],
        "scan_time": datetime.utcnow().isoformat(),
        "usage_map": report['usage_map'],
        'from_cache': False
    }
    
    # Update cache
    _scan_cache['last_scan'] = datetime.utcnow()
    _scan_cache['results'] = result
    
    return result

@router.get("/verify/{service}")
async def verify_service_envs(service: str):
    """Verify ENVs for specific service"""
    valid_services = ['agricultural-core', 'monitoring-dashboards']
    
    if service not in valid_services:
        raise HTTPException(status_code=400, detail=f"Invalid service. Must be one of: {valid_services}")
    
    scanner = ENVScanner()
    verifier = ENVVerifier()
    
    required = scanner.get_all_required_envs()
    results = verifier.verify_all_envs(required, service)
    
    # Add critical missing ENVs
    if results['missing_aws']:
        results['critical_missing'] = verifier.get_critical_missing_envs(results['missing_aws'])
    
    return results

@router.get("/dashboard-data")
async def env_dashboard_data():
    """Complete ENV status for dashboard"""
    scanner = ENVScanner()
    verifier = ENVVerifier()
    
    required = scanner.get_all_required_envs()
    
    # Verify both services
    agricultural_status = verifier.verify_all_envs(required, 'agricultural-core')
    monitoring_status = verifier.verify_all_envs(required, 'monitoring-dashboards')
    
    # Calculate overall status
    both_green = agricultural_status['status'] == 'GREEN' and monitoring_status['status'] == 'GREEN'
    any_red = agricultural_status['status'] == 'RED' or monitoring_status['status'] == 'RED'
    
    overall_status = 'GREEN' if both_green else ('RED' if any_red else 'YELLOW')
    
    # Find common missing ENVs
    common_missing = list(set(agricultural_status['missing_aws']) & set(monitoring_status['missing_aws']))
    
    return {
        "agricultural": agricultural_status,
        "monitoring": monitoring_status,
        "overall_status": overall_status,
        "common_missing": common_missing,
        "last_scan": datetime.utcnow().isoformat(),
        "bulgarian_mango_test": {
            "status": overall_status,
            "message": "All systems configured! 🥭" if overall_status == 'GREEN' else "Configuration incomplete - check missing ENVs!"
        }
    }

@router.get("/missing-summary")
async def get_missing_env_summary():
    """Get a summary of all missing environment variables"""
    scanner = ENVScanner()
    verifier = ENVVerifier()
    
    required = scanner.get_all_required_envs()
    
    # Check both services
    agricultural = verifier.verify_all_envs(required, 'agricultural-core')
    monitoring = verifier.verify_all_envs(required, 'monitoring-dashboards')
    
    # Combine missing ENVs
    all_missing = list(set(agricultural['missing_aws'] + monitoring['missing_aws']))
    critical_missing = verifier.get_critical_missing_envs(all_missing)
    
    return {
        "total_missing": len(all_missing),
        "critical_missing": critical_missing,
        "non_critical_missing": [env for env in all_missing if env not in critical_missing],
        "by_service": {
            "agricultural-core": agricultural['missing_aws'],
            "monitoring-dashboards": monitoring['missing_aws']
        },
        "recommendations": _get_env_recommendations(critical_missing)
    }

def _get_env_recommendations(missing_envs: list) -> list:
    """Get recommendations for missing ENVs"""
    recommendations = []
    
    for env in missing_envs:
        if env.startswith('DB_') or env.startswith('DATABASE_'):
            recommendations.append(f"Add {env} to ECS task definition or Secrets Manager for database access")
        elif env == 'OPENAI_API_KEY':
            recommendations.append("Add OPENAI_API_KEY to Secrets Manager for AI features (Constitutional requirement)")
        elif env.startswith('AWS_'):
            recommendations.append(f"Configure {env} in ECS task role or task definition")
        elif 'SECRET' in env or 'KEY' in env:
            recommendations.append(f"Store {env} in AWS Secrets Manager and reference in task definition")
        else:
            recommendations.append(f"Add {env} to ECS task definition environment variables")
    
    return recommendations

# Dashboard HTML endpoint
@router.get("/dashboard", response_class=HTMLResponse)
async def env_dashboard():
    """Serve the ENV dashboard HTML"""
    dashboard_path = Path("static/dashboards/env-dashboard.html")
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    else:
        # Return inline HTML if file doesn't exist
        return HTMLResponse(_get_dashboard_html())

def _get_dashboard_html():
    """Generate dashboard HTML"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ENV Status Dashboard - AVA OLO</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .status-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-green { 
            background: #4CAF50; 
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
        }
        .status-yellow { 
            background: #FFC107; 
            color: black;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
        }
        .status-red { 
            background: #F44336; 
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
        }
        .env-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); 
            gap: 10px;
            margin-top: 10px;
        }
        .env-item {
            padding: 8px;
            background: #f8f8f8;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }
        .missing { 
            color: #F44336; 
            font-weight: bold; 
        }
        .critical {
            background-color: #ffebee;
            border: 1px solid #F44336;
        }
        .service-section {
            margin-bottom: 30px;
        }
        h1, h2, h3 {
            color: #333;
        }
        .refresh-button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            float: right;
        }
        .refresh-button:hover {
            background: #1976D2;
        }
        .timestamp {
            color: #666;
            font-size: 12px;
        }
        .bulgarian-test {
            background: #e8f5e9;
            border: 2px solid #4CAF50;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .bulgarian-test.failed {
            background: #ffebee;
            border-color: #F44336;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>Environment Variables Status Dashboard
            <button class="refresh-button" onclick="updateDashboard()">Refresh</button>
        </h1>
        
        <div id="bulgarian-test" class="bulgarian-test">
            <h3>Bulgarian Mango Farmer Test</h3>
            <p>Checking configuration status...</p>
        </div>
        
        <div id="dashboard-content">
            <div class="status-card">
                <p>Loading environment variable status...</p>
            </div>
        </div>
    </div>
    
    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/env/dashboard-data');
                const data = await response.json();
                
                // Update Bulgarian test
                const bulgarianDiv = document.getElementById('bulgarian-test');
                const isPassing = data.overall_status === 'GREEN';
                bulgarianDiv.className = isPassing ? 'bulgarian-test' : 'bulgarian-test failed';
                bulgarianDiv.innerHTML = `
                    <h3>🥭 Bulgarian Mango Farmer Test</h3>
                    <div class="status-${data.overall_status.toLowerCase()}">
                        ${data.bulgarian_mango_test.status}
                    </div>
                    <p>${data.bulgarian_mango_test.message}</p>
                `;
                
                // Build main dashboard content
                let html = `
                    <div class="status-card">
                        <h2>Overall Status</h2>
                        <div class="status-${data.overall_status.toLowerCase()}">
                            ${data.overall_status}
                        </div>
                        <p class="timestamp">Last scan: ${new Date(data.last_scan).toLocaleString()}</p>
                    </div>
                `;
                
                // Agricultural Core Service
                html += `
                    <div class="status-card service-section">
                        <h2>Agricultural Core Service</h2>
                        <div class="status-${data.agricultural.status.toLowerCase()}">
                            ${data.agricultural.status} - ${data.agricultural.status_message}
                        </div>
                        <p>
                            Total Required: ${data.agricultural.total_required} | 
                            AWS Configured: ${data.agricultural.aws_found} | 
                            Coverage: ${data.agricultural.aws_coverage_percentage}%
                        </p>
                `;
                
                if (data.agricultural.missing_aws.length > 0) {
                    html += `
                        <h4 class="missing">Missing Environment Variables (${data.agricultural.missing_aws.length}):</h4>
                        <div class="env-grid">
                    `;
                    for (const env of data.agricultural.missing_aws) {
                        const isCritical = data.agricultural.critical_missing && 
                                         data.agricultural.critical_missing.includes(env);
                        html += `<div class="env-item ${isCritical ? 'critical' : ''}">${env}</div>`;
                    }
                    html += '</div>';
                }
                html += '</div>';
                
                // Monitoring Dashboards Service
                html += `
                    <div class="status-card service-section">
                        <h2>Monitoring Dashboards Service</h2>
                        <div class="status-${data.monitoring.status.toLowerCase()}">
                            ${data.monitoring.status} - ${data.monitoring.status_message}
                        </div>
                        <p>
                            Total Required: ${data.monitoring.total_required} | 
                            AWS Configured: ${data.monitoring.aws_found} | 
                            Coverage: ${data.monitoring.aws_coverage_percentage}%
                        </p>
                `;
                
                if (data.monitoring.missing_aws.length > 0) {
                    html += `
                        <h4 class="missing">Missing Environment Variables (${data.monitoring.missing_aws.length}):</h4>
                        <div class="env-grid">
                    `;
                    for (const env of data.monitoring.missing_aws) {
                        const isCritical = data.monitoring.critical_missing && 
                                         data.monitoring.critical_missing.includes(env);
                        html += `<div class="env-item ${isCritical ? 'critical' : ''}">${env}</div>`;
                    }
                    html += '</div>';
                }
                html += '</div>';
                
                // Common missing
                if (data.common_missing.length > 0) {
                    html += `
                        <div class="status-card">
                            <h3 class="missing">Common Missing Variables (${data.common_missing.length})</h3>
                            <p>These environment variables are missing from both services:</p>
                            <div class="env-grid">
                    `;
                    for (const env of data.common_missing) {
                        html += `<div class="env-item critical">${env}</div>`;
                    }
                    html += '</div></div>';
                }
                
                document.getElementById('dashboard-content').innerHTML = html;
                
            } catch (error) {
                document.getElementById('dashboard-content').innerHTML = `
                    <div class="status-card">
                        <h3 class="missing">Error loading dashboard data</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        // Initial load
        updateDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
"""