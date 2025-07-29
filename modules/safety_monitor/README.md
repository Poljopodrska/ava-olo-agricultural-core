# Zero-Regression Safety Monitoring System

## Overview
This is a completely isolated monitoring system that provides read-only health checks for AVA OLO. It cannot affect the main application's operation.

## Key Safety Features
1. **READ-ONLY Database Access**: Connection string enforces read-only mode
2. **Complete Isolation**: No imports from existing AVA OLO modules
3. **Fail-Safe Design**: If monitoring fails, main app continues unaffected
4. **No Authentication Required**: Public health endpoints (safe because read-only)
5. **Removable**: Can be deleted entirely without any impact

## Endpoints

### Health Dashboard
- **URL**: `/health-monitor`
- **Type**: HTML Dashboard
- **Auto-refresh**: Every 30 seconds
- **Shows**: Overall status, health checks, system metrics

### Health API
- **URL**: `/api/v1/safety/health`
- **Type**: JSON API
- **Returns**: System health data
- **Cache**: 30-second cache to prevent overload

## Database Safety
The monitor uses PostgreSQL's read-only transaction mode:
```python
'options': '-c default_transaction_read_only=on'
```

Any attempt to write will fail with:
```
ERROR: cannot execute INSERT in a read-only transaction
```

## Health Checks Performed
1. **Database Connectivity**: Basic connection test
2. **Table Existence**: Verifies critical tables exist
3. **Recent Activity**: Checks for recent registrations
4. **Connection Pool**: Monitors database connections
5. **System Metrics**: Counts farmers, registrations, etc.

## Automated Monitoring
The `health_checker.py` script can run continuously:
```bash
# Single check
python modules/safety_monitor/health_checker.py --once

# Continuous monitoring (every 5 minutes)
python modules/safety_monitor/health_checker.py
```

Logs are written to:
- `/tmp/ava_health_log.json` - Continuous log
- `/tmp/health_summary_YYYY-MM-DD.json` - Daily summaries

## Zero-Regression Guarantee
This monitoring system:
- Makes NO modifications to existing code (only additions at end of main.py)
- Uses NO shared imports or dependencies
- Performs NO database writes
- Has NO impact on performance (cached, async)
- Can be completely removed by deleting this folder and 2 endpoints

## Testing
```bash
# Test existing endpoints still work
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/register

# Test new monitoring (doesn't affect above)
curl http://localhost:8080/health-monitor
curl http://localhost:8080/api/v1/safety/health
```

## Emergency Removal
If needed, completely remove monitoring:
1. Delete `/modules/safety_monitor/` folder
2. Remove the two endpoints from end of main.py
3. System continues unchanged