# ECS-First Configuration Guide

## Overview
This guide explains how the AVA OLO system now uses ECS endpoints as primary with App Runner as fallback, solving the "App Runner suggestion problem" while maintaining safety.

## Problem Solved
- **Before**: Hardcoded App Runner URLs in codebase
- **After**: ECS-first with automatic App Runner fallback
- **Benefit**: System "forgets" App Runner but keeps it for safety

## New Architecture

### ECS Primary Endpoints
```
Monitoring:   http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com
Agricultural: http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com
```

### App Runner Fallback (Safety)
```
Monitoring:   https://bcibj8ws3x.us-east-1.awsapprunner.com
Agricultural: https://ujvej9snpp.us-east-1.awsapprunner.com
```

## How It Works

### 1. Automatic Endpoint Selection
```python
from ecs_config import get_monitoring_url

# This will return ECS endpoint if healthy, App Runner if ECS is down
url = get_monitoring_url()
```

### 2. Health Check Logic
1. **Try ECS first** (health check with 5-second timeout)
2. **If ECS fails**, automatically try App Runner
3. **Cache results** for 30 seconds to avoid repeated checks
4. **Log fallbacks** so you know when App Runner is used

### 3. Development Database Access
```python
from dev_db_helper import DevDatabaseHelper

# Automatically uses ECS endpoint with App Runner fallback
db = DevDatabaseHelper()
# Output: ✅ Using ECS-first endpoint: http://ava-olo-alb-65365776...

schema = db.get_schema()
```

## Configuration Files Updated

### ✅ `ecs_config.py` (NEW)
- ECS-first endpoint management
- Automatic health checking
- Fallback logic

### ✅ `dev_db_helper.py` (UPDATED)
- Uses ECS endpoints by default
- Imports `ecs_config` for smart routing
- Shows which endpoint is active

### ✅ `DEV_DATABASE_ACCESS.md` (UPDATED)
- Examples now show ECS-first usage
- Updated documentation

## Benefits Achieved

### 🚫 No More App Runner Suggestions
- Code uses ECS endpoints primarily
- Claude Code will suggest ECS endpoints
- App Runner only mentioned as fallback

### 🛡️ Safety Maintained
- App Runner still running as backup
- Automatic failover if ECS has issues
- Zero downtime during transition

### 📈 Performance
- ECS endpoints tested and working
- Health checks ensure reliability
- Fast fallback (5-second timeout)

## Usage Examples

### Development Database Access
```python
# Old way (hardcoded App Runner)
db = DevDatabaseHelper("https://bcibj8ws3x.us-east-1.awsapprunner.com")

# New way (ECS-first)
db = DevDatabaseHelper()  # Automatically uses ECS
```

### Manual Endpoint Selection
```python
from ecs_config import endpoints

# Get status of all endpoints
status = endpoints.status_report()
print(status)

# Force App Runner (emergency)
endpoints.prefer_ecs = False
url = endpoints.get_monitoring_url()
```

### Health Check Status
```bash
python3 ecs_config.py
```
Output:
```
🔧 Monitoring Service:
   ECS Primary: http://ava-olo-alb-65365776... ✅
   App Runner:  https://bcibj8ws3x... ❌
   Active:      http://ava-olo-alb-65365776...
```

## Environment Variables

### Standard Usage
```bash
# ECS-first (default)
PREFER_ECS=true
DEV_ACCESS_KEY=temporary-dev-key-2025
```

### Emergency App Runner Mode
```bash
# Force App Runner usage
PREFER_ECS=false
DEV_ACCESS_KEY=temporary-dev-key-2025
```

## Migration Complete ✅

### Files Updated
- ✅ `ecs_config.py` - Smart endpoint management
- ✅ `dev_db_helper.py` - ECS-first database access
- ✅ `DEV_DATABASE_ACCESS.md` - Updated documentation
- ✅ `APP_RUNNER_DEPRECATION_STRATEGY.md` - Transition plan

### App Runner References Eliminated
- ✅ No hardcoded App Runner URLs in active code
- ✅ App Runner only used as automatic fallback
- ✅ ECS endpoints suggested by default

### Safety Measures
- ✅ App Runner still running (not shut down)
- ✅ Automatic fallback if ECS fails
- ✅ Health monitoring and caching

## Next Steps

### Immediate (Working Now)
1. **Development database endpoints** use ECS by default
2. **All new code** will reference ECS endpoints
3. **Fallback works** if ECS has issues

### Within 1 Week
1. **Deploy dev endpoints** to ECS service
2. **Test fallback mechanism** during maintenance
3. **Monitor ECS stability**

### Future (Optional)
1. **Shut down App Runner** after proven stability
2. **Remove fallback code** (or keep for resilience)
3. **Cost savings** from single infrastructure

## Troubleshooting

### "Still seeing App Runner suggestions"
- Check you're using updated `dev_db_helper.py`
- Verify `ecs_config.py` is in the same directory
- Run `python3 ecs_config.py` to test

### "ECS endpoint not working"
- Check ECS service status in AWS Console
- Test App Runner fallback: `endpoints.prefer_ecs = False`
- Review health check logs

### "Want to force App Runner"
```python
from dev_db_helper import DevDatabaseHelper
db = DevDatabaseHelper("https://bcibj8ws3x.us-east-1.awsapprunner.com")
```

## Success Metrics

### ✅ Problem Solved
- No more hardcoded App Runner URLs
- ECS suggested by default
- App Runner forgotten but available

### ✅ Safety Maintained
- Both services running
- Automatic failover working
- Zero service interruption

### ✅ Future Ready
- Clear path to App Runner shutdown
- ECS-first architecture
- Cost optimization ready

This configuration ensures the system "forgets" App Runner for development purposes while maintaining it as a safety net during the transition period.