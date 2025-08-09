# Redis Configuration for AVA OLO

## Redis Cluster Details
- **Cluster ID**: ava-redis-cluster
- **Endpoint**: ava-redis-cluster.rwoelf.0001.use1.cache.amazonaws.com
- **Port**: 6379
- **Instance Type**: cache.t3.micro
- **Engine**: Redis 7.0.7
- **Region**: us-east-1

## ECS Configuration
The following environment variables must be set in the ECS task definition:
```
REDIS_HOST=ava-redis-cluster.rwoelf.0001.use1.cache.amazonaws.com
REDIS_PORT=6379
```

## Task Definition
- **Current Revision**: 90 (as of 2025-08-09)
- **Environment Variables Added**:
  - REDIS_HOST
  - REDIS_PORT

## Purpose
Redis is used for caching farmer welcome packages to improve performance:
- Caches farmer data (fields, crops, tasks) with 4-hour TTL
- Reduces database queries by 6-10x
- Enables instant context loading for FAVA/CAVA

## Testing
Check Redis connection status:
```javascript
// In browser console at https://avaolo.com
fetch('https://avaolo.com/debug/redis/+393484446808')
  .then(r => r.json())
  .then(console.log);
```

## Maintenance
- Redis cluster auto-backups: Daily at 03:30-04:30 UTC
- Maintenance window: Monday 09:00-10:00 UTC
- No authentication enabled (relies on VPC security groups)