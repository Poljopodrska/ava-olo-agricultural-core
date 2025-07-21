"""
Deployment Status Dashboard Module
Provides real-time visibility into deployment pipeline health
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import boto3
import json
import subprocess
from ..core.feature_verification import get_feature_verification_report

router = APIRouter(prefix="/dashboards/deployment", tags=["deployment"])
api_router = APIRouter(prefix="/api/deployment", tags=["deployment-api"])

# AWS clients
ecs_client = boto3.client('ecs', region_name='us-east-1')
ecr_client = boto3.client('ecr', region_name='us-east-1')
codebuild_client = boto3.client('codebuild', region_name='us-east-1')
logs_client = boto3.client('logs', region_name='us-east-1')

# Service configurations
SERVICES = {
    "agricultural-core": {
        "github_repo": "Poljopodrska/ava-olo-agricultural-core",
        "ecr_repo": "ava-olo/agricultural-core",
        "ecs_service": "agricultural-core",
        "codebuild_project": "ava-agricultural-docker-build",
        "alb_url": "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com",
        "task_family": "ava-agricultural-task"
    },
    "monitoring-dashboards": {
        "github_repo": "Poljopodrska/ava-olo-monitoring-dashboards",
        "ecr_repo": "ava-olo/monitoring-dashboards",
        "ecs_service": "monitoring-dashboards",
        "codebuild_project": "ava-monitoring-docker-build",
        "alb_url": "http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com",
        "task_family": "ava-monitoring-task"
    }
}

async def get_github_version(repo: str) -> Dict[str, Any]:
    """Get latest version from GitHub"""
    try:
        # Get latest commit
        result = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            commit_hash = result.stdout.split()[0][:8]
            return {"commit": commit_hash, "status": "accessible"}
        return {"commit": "unknown", "status": "error", "error": result.stderr}
    except Exception as e:
        return {"commit": "unknown", "status": "error", "error": str(e)}

async def get_ecr_version(repo: str) -> Dict[str, Any]:
    """Get latest version from ECR"""
    try:
        response = ecr_client.describe_images(
            repositoryName=repo,
            filter={'tagStatus': 'TAGGED'}
        )
        
        if response['imageDetails']:
            # Sort by pushed date
            sorted_images = sorted(
                response['imageDetails'], 
                key=lambda x: x.get('imagePushedAt', datetime.min),
                reverse=True
            )
            latest = sorted_images[0]
            return {
                "tag": latest.get('imageTags', ['untagged'])[0],
                "pushed_at": latest.get('imagePushedAt', '').isoformat() if latest.get('imagePushedAt') else 'unknown',
                "digest": latest.get('imageDigest', '')[:12]
            }
        return {"tag": "none", "pushed_at": "never", "digest": ""}
    except Exception as e:
        return {"tag": "error", "error": str(e)}

async def get_ecs_version(service: str) -> Dict[str, Any]:
    """Get currently running version from ECS"""
    try:
        # Get service details
        response = ecs_client.describe_services(
            cluster='ava-olo-production',
            services=[service]
        )
        
        if not response['services']:
            return {"version": "service_not_found", "status": "error"}
        
        service_info = response['services'][0]
        
        # Get running tasks
        tasks_response = ecs_client.list_tasks(
            cluster='ava-olo-production',
            serviceName=service,
            desiredStatus='RUNNING'
        )
        
        running_count = len(tasks_response.get('taskArns', []))
        
        # Get ALB health
        alb_version = await check_alb_version(SERVICES[service]['alb_url'])
        
        return {
            "version": alb_version.get('version', 'unknown'),
            "running_tasks": running_count,
            "desired_tasks": service_info.get('desiredCount', 0),
            "deployments": len(service_info.get('deployments', [])),
            "status": service_info.get('status', 'unknown'),
            "task_definition": service_info.get('taskDefinition', '').split('/')[-1] if service_info.get('taskDefinition') else 'unknown'
        }
    except Exception as e:
        return {"version": "error", "error": str(e)}

async def check_alb_version(url: str) -> Dict[str, Any]:
    """Check version from ALB endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try multiple endpoints
            for endpoint in ['/version', '/health', '/api/deployment/verify']:
                try:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "version": data.get('version', 'unknown'),
                            "status": "healthy",
                            "endpoint": endpoint
                        }
                except:
                    continue
            return {"version": "unknown", "status": "no_valid_endpoint"}
    except Exception as e:
        return {"version": "error", "status": "unreachable", "error": str(e)}

async def get_codebuild_status(project: str) -> Dict[str, Any]:
    """Get latest CodeBuild status"""
    try:
        response = codebuild_client.list_builds_for_project(
            projectName=project,
            sortOrder='DESCENDING'
        )
        
        if not response.get('ids'):
            return {"status": "no_builds", "last_build": "never"}
        
        # Get details of latest build
        build_id = response['ids'][0]
        build_details = codebuild_client.batch_get_builds(ids=[build_id])
        
        if build_details['builds']:
            build = build_details['builds'][0]
            return {
                "status": build['buildStatus'],
                "last_build": build['startTime'].isoformat(),
                "duration": str(build.get('endTime', datetime.now()) - build['startTime']) if build.get('endTime') else "in_progress",
                "build_id": build_id.split(':')[-1]
            }
        return {"status": "unknown", "last_build": "error"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def count_failed_tasks(service: str, hours: int = 1) -> int:
    """Count failed ECS tasks in the last N hours"""
    try:
        # Get stopped tasks
        response = ecs_client.list_tasks(
            cluster='ava-olo-production',
            serviceName=service,
            desiredStatus='STOPPED',
            maxResults=100
        )
        
        if not response.get('taskArns'):
            return 0
        
        # Get task details
        tasks = ecs_client.describe_tasks(
            cluster='ava-olo-production',
            tasks=response['taskArns']
        )
        
        # Count recent failures
        cutoff_time = datetime.now(tasks['tasks'][0]['stoppedAt'].tzinfo) - timedelta(hours=hours)
        failed_count = 0
        
        for task in tasks['tasks']:
            if task.get('stoppedAt') and task['stoppedAt'] > cutoff_time:
                if task.get('stopCode') == 'TaskFailedToStart' or 'Error' in task.get('stoppedReason', ''):
                    failed_count += 1
        
        return failed_count
    except Exception as e:
        return -1  # Indicate error

def generate_deployment_alerts(status: Dict[str, Any]) -> list:
    """Generate alerts based on deployment status including feature failures"""
    alerts = []
    
    for service_name, service_status in status['services'].items():
        # NEW: Feature failure alerts (HIGHEST PRIORITY)
        feature_verification = service_status.get('feature_verification', {})
        if not feature_verification.get('all_features_working', True):
            # Extract failed features
            failed_features = []
            for feature_name, feature_data in feature_verification.get('features', {}).items():
                if feature_data.get('status') != 'healthy':
                    failed_features.append({
                        'name': feature_name,
                        'status': feature_data.get('status'),
                        'message': feature_data.get('message', 'Unknown failure')
                    })
            
            alerts.append({
                "severity": "critical",
                "service": service_name,
                "message": f"FEATURE FAILURES DETECTED - Deployment succeeded but features are broken!",
                "feature_type": "silent_failure",
                "failed_features": failed_features,
                "action": "Check feature verification dashboard for details"
            })
        
        # Version mismatch alert
        if service_status.get('ecr_version', {}).get('tag') != 'latest':
            if service_status.get('ecs_version', {}).get('version') != service_status.get('github_version', {}).get('commit'):
                alerts.append({
                    "severity": "warning",
                    "service": service_name,
                    "message": f"Version mismatch: GitHub has newer commits not deployed",
                    "details": {
                        "github": service_status.get('github_version', {}).get('commit'),
                        "running": service_status.get('ecs_version', {}).get('version')
                    }
                })
        
        # Failed tasks alert
        if service_status.get('failed_tasks_1h', 0) > 5:
            alerts.append({
                "severity": "critical",
                "service": service_name,
                "message": f"High failure rate: {service_status['failed_tasks_1h']} tasks failed in last hour",
                "action": "Check ECS logs and task definitions"
            })
        
        # Build failure alert
        if service_status.get('codebuild_status', {}).get('status') == 'FAILED':
            alerts.append({
                "severity": "critical",
                "service": service_name,
                "message": "Last CodeBuild failed - deployments blocked",
                "build_id": service_status.get('codebuild_status', {}).get('build_id')
            })
        
        # Service unhealthy alert
        if service_status.get('ecs_version', {}).get('running_tasks', 0) < service_status.get('ecs_version', {}).get('desired_tasks', 1):
            alerts.append({
                "severity": "warning",
                "service": service_name,
                "message": f"Service degraded: {service_status['ecs_version']['running_tasks']}/{service_status['ecs_version']['desired_tasks']} tasks running"
            })
    
    return alerts

@api_router.get("/status")
async def deployment_status():
    """Get comprehensive deployment status with feature verification"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "pipeline_health": {},
        "alerts": [],
        "features": {}  # NEW: Feature verification results
    }
    
    # Check each service
    for service_name, config in SERVICES.items():
        service_status = {}
        
        # Get versions from different sources
        service_status['github_version'] = await get_github_version(config['github_repo'])
        service_status['ecr_version'] = await get_ecr_version(config['ecr_repo'])
        service_status['ecs_version'] = await get_ecs_version(config['ecs_service'])
        service_status['codebuild_status'] = await get_codebuild_status(config['codebuild_project'])
        
        # Count failures
        service_status['failed_tasks_1h'] = await count_failed_tasks(config['ecs_service'], 1)
        service_status['failed_tasks_24h'] = await count_failed_tasks(config['ecs_service'], 24)
        
        # NEW: Verify features are actually working
        try:
            feature_report = await get_feature_verification_report(
                service_name.replace('-', '_'),  # Convert to module name format
                config['alb_url']
            )
            service_status['feature_verification'] = feature_report
            status['features'][service_name] = feature_report
            
            # Update deployment status based on BOTH mechanical success AND feature health
            mechanical_healthy = (
                service_status['ecs_version'].get('status') == 'ACTIVE' and
                service_status['ecs_version'].get('running_tasks', 0) >= service_status['ecs_version'].get('desired_tasks', 1) and
                service_status['failed_tasks_1h'] < 5 and
                service_status['codebuild_status'].get('status') in ['SUCCEEDED', 'IN_PROGRESS']
            )
            
            features_healthy = feature_report.get('all_features_working', False)
            
            # Only mark as healthy if BOTH deployment AND features are working
            all_healthy = mechanical_healthy and features_healthy
            
            if mechanical_healthy and not features_healthy:
                # This is the silent failure case - deployment succeeded but features broken
                service_status['deployment_status'] = 'DEGRADED'
                service_status['deployment_warning'] = 'Deployment successful but features not working correctly'
            else:
                service_status['deployment_status'] = 'HEALTHY' if all_healthy else 'UNHEALTHY'
                
        except Exception as e:
            # If feature verification fails, assume features are broken
            service_status['feature_verification'] = {
                'error': str(e),
                'all_features_working': False
            }
            service_status['deployment_status'] = 'DEGRADED'
            service_status['deployment_warning'] = f'Could not verify features: {str(e)}'
        
        status['services'][service_name] = service_status
    
    # Overall pipeline health includes feature health
    status['pipeline_health'] = {
        "all_services_healthy": all(s['deployment_status'] == 'HEALTHY' for s in status['services'].values()),
        "all_features_working": all(f.get('all_features_working', False) for f in status['features'].values()),
        "last_check": datetime.now().isoformat()
    }
    
    # Generate alerts including feature failures
    status['alerts'] = generate_deployment_alerts(status)
    
    return status

@api_router.post("/verify/{service}")
async def verify_deployment(service: str, expected_version: str):
    """Verify a specific deployment completed successfully INCLUDING feature verification"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    config = SERVICES[service]
    
    # Check ALB version
    alb_check = await check_alb_version(config['alb_url'])
    actual_version = alb_check.get('version', 'unknown')
    
    # Check ECS status
    ecs_status = await get_ecs_version(service)
    
    # Count recent failures
    failed_tasks = await count_failed_tasks(service, 1)
    
    # NEW: Verify features are working
    try:
        feature_report = await get_feature_verification_report(
            service.replace('-', '_'),
            config['alb_url']
        )
        features_working = feature_report.get('all_features_working', False)
    except Exception as e:
        feature_report = {'error': str(e), 'all_features_working': False}
        features_working = False
    
    # Deployment is only verified if version matches, tasks are running, AND features work
    mechanical_verified = (
        actual_version == expected_version and
        ecs_status.get('running_tasks', 0) >= ecs_status.get('desired_tasks', 0) and
        failed_tasks < 5
    )
    
    # IMPORTANT: True verification requires BOTH mechanical success AND feature health
    truly_verified = mechanical_verified and features_working
    
    result = {
        "service": service,
        "expected_version": expected_version,
        "actual_version": actual_version,
        "verified": truly_verified,  # This now includes feature verification
        "mechanical_deployment_success": mechanical_verified,
        "features_working": features_working,
        "feature_verification": feature_report,
        "ecs_status": ecs_status,
        "failed_tasks_1h": failed_tasks,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log verification failure with more detail
    if not truly_verified:
        if mechanical_verified and not features_working:
            print(f"SILENT DEPLOYMENT FAILURE DETECTED: {json.dumps(result, indent=2)}")
            print("WARNING: Deployment succeeded mechanically but features are broken!")
        else:
            print(f"DEPLOYMENT VERIFICATION FAILED: {json.dumps(result, indent=2)}")
    
    return result

@router.get("/", response_class=HTMLResponse)
async def deployment_dashboard():
    """Deployment monitoring dashboard UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Deployment Status Dashboard</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-system-v2.css">
        <style>
            body {
                font-family: var(--font-primary);
                margin: 0;
                padding: 20px;
                background: var(--color-bg-primary);
            }
            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .service-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .service-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .service-name {
                font-size: 24px;
                font-weight: bold;
                color: var(--color-agri-green);
            }
            .status-badge {
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 14px;
            }
            .status-healthy {
                background: #28a745;
                color: white;
            }
            .status-unhealthy {
                background: #dc3545;
                color: white;
            }
            .status-degraded {
                background: #ff9800;
                color: white;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .metric {
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                text-align: center;
            }
            .metric-label {
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 20px;
                font-weight: bold;
                color: #212529;
            }
            .alert {
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .alert-warning {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }
            .alert-critical {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .refresh-info {
                text-align: center;
                color: #6c757d;
                margin-top: 20px;
            }
            .version-mismatch {
                color: #dc3545;
                font-weight: bold;
            }
            .version-match {
                color: #28a745;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <h1>🚀 AVA OLO Deployment Status Dashboard</h1>
            
            <div id="alerts-container"></div>
            <div id="services-container">
                <div class="service-card">
                    <p style="text-align: center; color: #6c757d;">Loading deployment status...</p>
                </div>
            </div>
            
            <div class="refresh-info">
                Auto-refreshing every 30 seconds | Last update: <span id="last-update">-</span>
            </div>
        </div>
        
        <script>
            async function updateDashboard() {
                try {
                    const response = await fetch('/api/deployment/status');
                    const data = await response.json();
                    
                    // Update alerts
                    const alertsHtml = data.alerts.map(alert => `
                        <div class="alert alert-${alert.severity}">
                            <strong>${alert.service}:</strong> ${alert.message}
                            ${alert.details ? `<br><small>${JSON.stringify(alert.details)}</small>` : ''}
                        </div>
                    `).join('');
                    // Highlight feature failures prominently
                    const featureFailures = data.alerts.filter(a => a.feature_type === 'silent_failure');
                    if (featureFailures.length > 0) {
                        const featureAlertsHtml = featureFailures.map(alert => `
                            <div class="alert alert-critical" style="background: #ff1744; border: 2px solid #d50000;">
                                <strong>⚠️ ${alert.service}:</strong> ${alert.message}
                                <br><small>Failed features: ${alert.failed_features.map(f => f.name).join(', ')}</small>
                                <br><a href="/dashboards/features/" style="color: white; text-decoration: underline;">View Feature Status Dashboard →</a>
                            </div>
                        `).join('');
                        document.getElementById('alerts-container').innerHTML = featureAlertsHtml + alertsHtml;
                    } else {
                        document.getElementById('alerts-container').innerHTML = alertsHtml || '<p style="color: #28a745;">✅ No deployment issues detected</p>';
                    }
                    
                    // Update services
                    const servicesHtml = Object.entries(data.services).map(([name, service]) => `
                        <div class="service-card">
                            <div class="service-header">
                                <div class="service-name">${name}</div>
                                <div class="status-badge status-${service.deployment_status.toLowerCase()}">
                                    ${service.deployment_status}
                                    ${service.deployment_warning ? '<br><small>' + service.deployment_warning + '</small>' : ''}
                                </div>
                            </div>
                            
                            <div class="metrics-grid">
                                <div class="metric">
                                    <div class="metric-label">Running Version</div>
                                    <div class="metric-value">${service.ecs_version.version || 'Unknown'}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">ECR Latest</div>
                                    <div class="metric-value">${service.ecr_version.tag || 'Unknown'}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">Tasks</div>
                                    <div class="metric-value">${service.ecs_version.running_tasks || 0}/${service.ecs_version.desired_tasks || 0}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">Failed (1h)</div>
                                    <div class="metric-value ${service.failed_tasks_1h > 5 ? 'version-mismatch' : ''}">${service.failed_tasks_1h}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">Last Build</div>
                                    <div class="metric-value ${service.codebuild_status.status === 'FAILED' ? 'version-mismatch' : 'version-match'}">${service.codebuild_status.status || 'Unknown'}</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">Features</div>
                                    <div class="metric-value ${service.feature_verification && service.feature_verification.all_features_working ? 'version-match' : 'version-mismatch'}">
                                        ${service.feature_verification ? (service.feature_verification.all_features_working ? '✅ Working' : '❌ Failed') : '⚠️ Unknown'}
                                    </div>
                                </div>
                            </div>
                            
                            <div style="margin-top: 10px; font-size: 14px; color: #6c757d;">
                                GitHub: ${service.github_version.commit || 'Unknown'} | 
                                ECR pushed: ${service.ecr_version.pushed_at ? new Date(service.ecr_version.pushed_at).toLocaleString() : 'Unknown'}
                            </div>
                        </div>
                    `).join('');
                    
                    document.getElementById('services-container').innerHTML = servicesHtml;
                    document.getElementById('last-update').textContent = new Date().toLocaleString();
                    
                } catch (error) {
                    console.error('Failed to update dashboard:', error);
                    document.getElementById('services-container').innerHTML = '<div class="alert alert-critical">Failed to load deployment status</div>';
                }
            }
            
            // Initial load and refresh every 30 seconds
            updateDashboard();
            setInterval(updateDashboard, 30000);
        </script>
    </body>
    </html>
    """