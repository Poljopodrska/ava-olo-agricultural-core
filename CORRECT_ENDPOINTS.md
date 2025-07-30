# AVA OLO Official Endpoints

**Last Updated**: 2025-01-22  
**Status**: ✅ All services operational

## Production Endpoints

### 🌾 Agricultural Core (Farmer Portal)
- **URL**: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com
- **Purpose**: Main farmer portal for Bulgarian mango cooperative
- **Login**: WhatsApp number + password
- **Admin Access**: Use admin bypass button on login page
- **Current Version**: v3.3.20-env-recovery (deployment pending for v3.3.23)

### 📊 Monitoring Dashboards
- **URL**: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com
- **Purpose**: Internal monitoring and analytics dashboards
- **Access**: Internal use only
- **Current Version**: v3.3.13-clean

## API Endpoints

### System Health & Status
```bash
# Health check
curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health

# Environment check
curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check

# Debug services
curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/debug/services
```

### Authentication
```bash
# Sign in
POST http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/auth/signin
{
  "whatsapp": "+359...",
  "password": "..."
}

# Admin bypass (for testing)
POST http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/auth/admin-login
```

### Weather API
```bash
# Current weather for farmer
GET http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/weather/current-farmer

# Forecast for farmer location
GET http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/weather/forecast-farmer

# Hourly forecast
GET http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/weather/hourly-farmer
```

### Chat API (CAVA Assistant)
```bash
# Send message
POST http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/chat/message
{
  "content": "How is my mango crop doing?"
}

# Chat status
GET http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/chat/status
```

## AWS Infrastructure

### Application Load Balancers
| Service | ALB DNS | Status |
|---------|---------|--------|
| Agricultural | ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com | ✅ Active |
| Monitoring | ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com | ✅ Active |

### ECS Services
| Service | Cluster | Task Definition |
|---------|---------|-----------------|
| agricultural-core | ava-olo-production | ava-agricultural-task:7 |
| monitoring-dashboards | ava-olo-production | ava-monitoring-task:10 |

## Quick Test Commands

```bash
# Test agricultural service
curl -s http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ | grep version

# Test monitoring service  
curl -s http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/ | grep version

# Full system test
./scripts/test_all_endpoints.sh
```

## Troubleshooting

If endpoints are not accessible:
1. Check DNS resolution: `nslookup [alb-dns-name]`
2. Clear DNS cache: `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (Mac)
3. Try different DNS server: `nslookup [alb-dns-name] 8.8.8.8`
4. Check service status: `aws ecs describe-services --cluster ava-olo-production --services agricultural-core`

## Notes
- These are the correct, working endpoints as of January 2025
- The ALBs are internet-facing and accessible from anywhere
- No VPN required for access
- Services auto-scale based on load