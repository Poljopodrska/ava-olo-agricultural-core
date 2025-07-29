"""
Safety Monitor - Zero Regression Read-Only Monitoring
NO IMPORTS from existing AVA OLO modules - complete isolation
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, Optional
import traceback

logger = logging.getLogger(__name__)

class SafetyMonitor:
    """
    Completely isolated monitoring system
    Read-only database access
    No dependencies on existing code
    """
    
    def __init__(self):
        # Own database configuration - READ ONLY
        self.db_config = {
            'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            'database': os.getenv('DB_NAME', 'farmer_crm'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432'),
            'options': '-c default_transaction_read_only=on'  # ENFORCE READ-ONLY
        }
        
        # Health check results cache
        self._last_check = None
        self._last_check_time = None
        self._cache_duration = 30  # seconds
        
    def check_system_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        Returns JSON-serializable health status
        """
        # Use cache if recent
        if self._last_check_time:
            elapsed = (datetime.now(timezone.utc) - self._last_check_time).total_seconds()
            if elapsed < self._cache_duration and self._last_check:
                return self._last_check
        
        health_status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {
                'database': self._check_database(),
                'farmers': self._check_farmers_table(),
                'registrations': self._check_recent_registrations(),
                'system_tables': self._check_system_tables(),
                'connection_pool': self._check_connection_pool()
            },
            'metrics': {
                'total_farmers': self._count_farmers(),
                'registrations_today': self._count_registrations_today(),
                'last_registration': self._get_last_registration_time(),
                'database_size': self._get_database_size()
            },
            'monitor_version': '1.0.0',
            'app_version': os.getenv('APP_VERSION', '3.5.29')
        }
        
        # Determine overall status
        critical_checks = ['database', 'farmers', 'system_tables']
        failures = [check for check in critical_checks 
                   if health_status['checks'].get(check, {}).get('status') != 'healthy']
        
        if failures:
            health_status['overall_status'] = 'UNHEALTHY'
        elif any(v.get('status') == 'warning' for v in health_status['checks'].values()):
            health_status['overall_status'] = 'DEGRADED'
        
        # Cache the result
        self._last_check = health_status
        self._last_check_time = datetime.now(timezone.utc)
        
        return health_status
    
    def _check_database(self) -> Dict[str, Any]:
        """Check basic database connectivity"""
        start_time = datetime.now(timezone.utc)
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'message': f'Database connection failed: {str(e)}'
            }
    
    def _check_farmers_table(self) -> Dict[str, Any]:
        """Check if farmers table is accessible"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'farmers'
            """)
            exists = cursor.fetchone()[0] > 0
            cursor.close()
            conn.close()
            
            return {
                'status': 'healthy' if exists else 'unhealthy',
                'table_exists': exists,
                'message': 'Farmers table accessible' if exists else 'Farmers table not found'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'table_exists': False,
                'message': f'Failed to check farmers table: {str(e)}'
            }
    
    def _check_recent_registrations(self) -> Dict[str, Any]:
        """Check for recent farmer registrations"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check registrations in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM farmers 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'healthy',
                'registrations_24h': count,
                'message': f'{count} registrations in last 24 hours'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'registrations_24h': None,
                'message': f'Could not check registrations: {str(e)}'
            }
    
    def _check_system_tables(self) -> Dict[str, Any]:
        """Check critical system tables"""
        critical_tables = ['farmers', 'chats', 'llm_interactions', 'llm_debug_log']
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            missing_tables = []
            for table in critical_tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table,))
                if cursor.fetchone()[0] == 0:
                    missing_tables.append(table)
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'healthy' if not missing_tables else 'unhealthy',
                'missing_tables': missing_tables,
                'checked_tables': critical_tables,
                'message': 'All critical tables present' if not missing_tables else f'Missing tables: {missing_tables}'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'missing_tables': None,
                'message': f'Failed to check system tables: {str(e)}'
            }
    
    def _check_connection_pool(self) -> Dict[str, Any]:
        """Check database connection pool health"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check active connections
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = %s AND state = 'active'
            """, (self.db_config['database'],))
            active_connections = cursor.fetchone()[0]
            
            # Check max connections
            cursor.execute("SHOW max_connections")
            max_connections = int(cursor.fetchone()[0])
            
            cursor.close()
            conn.close()
            
            usage_percent = (active_connections / max_connections) * 100
            
            return {
                'status': 'healthy' if usage_percent < 80 else 'warning',
                'active_connections': active_connections,
                'max_connections': max_connections,
                'usage_percent': round(usage_percent, 2),
                'message': f'Connection pool at {usage_percent:.1f}% capacity'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Could not check connection pool: {str(e)}'
            }
    
    def _count_farmers(self) -> Optional[int]:
        """Count total farmers"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM farmers")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count
        except:
            return None
    
    def _count_registrations_today(self) -> Optional[int]:
        """Count registrations today"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM farmers 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count
        except:
            return None
    
    def _get_last_registration_time(self) -> Optional[str]:
        """Get timestamp of last registration"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(created_at) FROM farmers
            """)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return result[0].isoformat()
            return None
        except:
            return None
    
    def _get_database_size(self) -> Optional[str]:
        """Get database size"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(%s))
            """, (self.db_config['database'],))
            size = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return size
        except:
            return None
    
    def render_dashboard(self) -> str:
        """Render HTML dashboard"""
        health_data = self.check_system_health()
        
        # Determine status colors
        status_colors = {
            'HEALTHY': '#4CAF50',
            'DEGRADED': '#ff9800',
            'UNHEALTHY': '#f44336'
        }
        
        overall_color = status_colors.get(health_data['overall_status'], '#757575')
        
        # Generate check boxes HTML
        check_boxes_html = ""
        for check_name, check_data in health_data['checks'].items():
            status = check_data.get('status', 'unknown')
            color = '#4CAF50' if status == 'healthy' else '#f44336' if status == 'unhealthy' else '#ff9800'
            message = check_data.get('message', 'No data')
            
            check_boxes_html += f"""
            <div class="health-box" style="background-color: {color};">
                <h3>{check_name.replace('_', ' ').title()}</h3>
                <p>{status.upper()}</p>
                <small>{message}</small>
            </div>
            """
        
        # Generate metrics HTML
        metrics_html = ""
        for metric_name, metric_value in health_data['metrics'].items():
            display_name = metric_name.replace('_', ' ').title()
            value = metric_value if metric_value is not None else 'N/A'
            metrics_html += f"""
            <div class="metric-item">
                <strong>{display_name}:</strong> {value}
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AVA OLO Safety Monitor</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                }}
                .overall-status {{
                    background-color: {overall_color};
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .checks-container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin: 20px 0;
                }}
                .health-box {{
                    flex: 1;
                    min-width: 200px;
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .health-box h3 {{
                    margin: 0 0 10px 0;
                }}
                .health-box p {{
                    margin: 5px 0;
                    font-weight: bold;
                }}
                .health-box small {{
                    font-size: 12px;
                    opacity: 0.9;
                }}
                .metrics-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric-item {{
                    padding: 5px 0;
                }}
                .timestamp {{
                    text-align: right;
                    color: #666;
                    font-size: 14px;
                    margin: 10px 0;
                }}
                .info {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <h1>🛡️ AVA OLO Safety Monitor</h1>
            
            <div class="info">
                <strong>Zero-Regression Monitoring System</strong><br>
                This is a read-only monitoring layer that cannot affect system operation.<br>
                Auto-refreshes every 30 seconds. Version: {health_data.get('app_version', 'Unknown')}
            </div>
            
            <div class="overall-status">
                <h2>Overall System Status: {health_data['overall_status']}</h2>
                <p>Last checked: {health_data['timestamp']}</p>
            </div>
            
            <h2>System Health Checks</h2>
            <div class="checks-container">
                {check_boxes_html}
            </div>
            
            <h2>System Metrics</h2>
            <div class="metrics-container">
                {metrics_html}
            </div>
            
            <div class="timestamp">
                Monitor Version: {health_data.get('monitor_version', '1.0.0')} | 
                App Version: {health_data.get('app_version', 'Unknown')} |
                Page will refresh in <span id="countdown">30</span> seconds
            </div>
            
            <script>
                // Countdown timer
                let seconds = 30;
                setInterval(function() {{
                    seconds--;
                    document.getElementById('countdown').textContent = seconds;
                    if (seconds <= 0) seconds = 30;
                }}, 1000);
            </script>
        </body>
        </html>
        """
        
        return html