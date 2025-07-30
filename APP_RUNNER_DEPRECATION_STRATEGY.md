# App Runner Deprecation Strategy

## Overview
This document outlines the systematic approach to transition from App Runner to ECS-first architecture while maintaining App Runner as a safety backup.

## Current State
- **ECS**: Primary deployment target (production)
- **App Runner**: Running as backup for safety
- **Problem**: Codebase still references App Runner URLs

## ECS Endpoints (Primary)
- **Monitoring**: `http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com`
- **Agricultural**: `http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com` (ALB routes by path)

## App Runner Endpoints (Fallback)
- **Monitoring**: `https://bcibj8ws3x.us-east-1.awsapprunner.com`
- **Agricultural**: `https://ujvej9snpp.us-east-1.awsapprunner.com`

## Strategy: ECS-First with Graceful Fallback

### Phase 1: Configuration Layer ✅ COMPLETE
1. **Created `ecs_config.py`** - ECS-first endpoint management
2. **Updated `dev_db_helper.py`** - Uses ECS endpoints by default
3. **Health checking** - Automatic fallback if ECS is down

### Phase 2: Documentation Updates ✅ COMPLETE
1. **Updated DEV_DATABASE_ACCESS.md** - Shows ECS-first examples
2. **Created this deprecation strategy** - Clear transition plan

### Phase 3: Code Migration (NEXT)
1. **Update all hardcoded App Runner URLs**:
   - Replace direct URLs with `ecs_config` functions
   - Ensure automatic fallback works
   
2. **Update configuration files**:
   - Set ECS as default in environment variables
   - Add App Runner as backup configuration

### Phase 4: Testing and Validation
1. **Test ECS endpoints** with development database access
2. **Verify fallback mechanism** works when ECS is down
3. **Performance comparison** between ECS and App Runner

### Phase 5: Production Transition
1. **Deploy development endpoints to ECS**
2. **Update all references** to use ECS-first configuration
3. **Monitor for 48 hours** before considering App Runner shutdown

### Phase 6: App Runner Sunset (FUTURE)
1. **After 1 week of stable ECS operation**
2. **Graceful shutdown** of App Runner services
3. **Remove fallback code** (optional - can keep for resilience)

## Implementation Details

### ECS-First Helper Usage
```python
# Old way (hardcoded App Runner)
base_url = "https://bcibj8ws3x.us-east-1.awsapprunner.com"

# New way (ECS-first with fallback)
from ecs_config import get_dev_db_url
base_url = get_dev_db_url()
```

### Automatic Fallback Logic
1. **Try ECS endpoint first** (health check)
2. **If ECS fails**, automatically try App Runner
3. **If both fail**, return ECS anyway (primary)
4. **Cache health status** for 30 seconds to avoid repeated checks

### Configuration Environment Variables
```bash
# Force ECS usage
PREFER_ECS=true

# Force App Runner usage (emergency)
PREFER_ECS=false

# Development database key
DEV_ACCESS_KEY=temporary-dev-key-2025
```

## Benefits of This Approach

### ✅ Safety First
- App Runner remains running during transition
- Automatic failover if ECS has issues
- No service interruption

### ✅ Gradual Migration
- Update code incrementally
- Test each component
- Roll back easily if needed

### ✅ Future-Proof
- Easy to remove App Runner when ready
- Can keep fallback logic for resilience
- Clear deprecation path

## Risk Mitigation

### App Runner Costs
- **Current**: Running both systems temporarily
- **Mitigation**: Monitor costs, shut down after stable period
- **Timeline**: 1-2 weeks maximum overlap

### ECS Stability
- **Risk**: ECS might have deployment issues
- **Mitigation**: App Runner fallback provides continuity
- **Monitoring**: Health checks and alerts

### Code References
- **Risk**: Missing App Runner references in code
- **Mitigation**: Systematic search and replace
- **Validation**: Test all endpoints work with ECS

## Success Metrics

### Week 1: Migration Complete
- [ ] All code uses `ecs_config` functions
- [ ] ECS endpoints respond correctly
- [ ] Fallback mechanism tested

### Week 2: Stability Proven
- [ ] ECS uptime > 99.5%
- [ ] No fallback triggers
- [ ] Performance matches or exceeds App Runner

### Week 3: App Runner Sunset
- [ ] App Runner services stopped
- [ ] Cost reduction confirmed
- [ ] ECS-only operation successful

## Monitoring and Alerts

### Health Checks
- **ECS ALB**: Health check every 30 seconds
- **App Runner**: Backup health check
- **Fallback Triggers**: Log when App Runner is used

### Performance Metrics
- **Response times**: ECS vs App Runner comparison
- **Uptime**: Track both services
- **Error rates**: Monitor endpoint failures

### Cost Tracking
- **ECS costs**: Monitor after migration
- **App Runner costs**: Track during overlap period
- **Total savings**: Calculate after sunset

## Emergency Procedures

### If ECS Goes Down
1. **Automatic**: Fallback to App Runner (no action needed)
2. **Investigation**: Check ECS service health
3. **Communication**: Update team on status

### If Both Systems Down
1. **Emergency deployment** to App Runner
2. **Database investigation** via AWS Console
3. **Escalation** to AWS support if needed

### Rollback Plan
1. **Update ecs_config.py** to prefer App Runner
2. **Redeploy with App Runner primary**
3. **Fix ECS issues** while App Runner serves traffic

This strategy ensures a safe, gradual transition to ECS-first architecture while maintaining system reliability throughout the process.