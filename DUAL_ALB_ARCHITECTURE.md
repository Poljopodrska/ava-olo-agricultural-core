# Dual ALB Architecture - Development Phase

## Overview
The AVA OLO system now uses a dual ALB architecture to separate customer-facing services from internal monitoring dashboards. This is currently in development phase with both ALBs publicly accessible.

## Architecture

### Customer-Facing ALB (ava-olo-farmers-alb)
- **URL**: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com
- **Purpose**: Serves the Agricultural Core service for farmers
- **Target Group**: ava-farmers-tg
- **Security**: Currently open (HTTP port 80 from 0.0.0.0/0)
- **Status**: ✅ ACTIVE and HEALTHY

### Internal ALB (ava-olo-internal-alb)  
- **URL**: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com
- **Purpose**: Serves the Monitoring Dashboards for internal team
- **Target Group**: ava-monitoring-internal-tg
- **Security**: Currently open (HTTP port 80 from 0.0.0.0/0) - TODO: Add IP restrictions
- **Status**: ✅ ACTIVE and HEALTHY

## Security Configuration

### Current State (Development)
- Both ALBs use security group: sg-049c14ab3436e6dc5
- Allow HTTP (port 80) from anywhere (0.0.0.0/0)
- ECS task security group (sg-09f3c006e540a39b2) allows traffic from both old and new ALB security groups

### TODO Before Production
1. Create restricted security group for internal ALB
2. Add IP whitelist for internal access:
   - Office IP ranges
   - Developer IPs  
   - VPN range
3. Enable SSL certificates on both ALBs
4. Add AWS WAF to farmers ALB
5. Update security groups to HTTPS only

## Service Endpoints

### Agricultural Core (Farmers ALB)
- Health: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/health
- Register: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/register
- API: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/*

### Monitoring Dashboards (Internal ALB)
- Health: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/api/v1/health
- Dashboards: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/dashboards/*
- Business Dashboard: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/business-dashboard

## Migration Status
- ✅ Created new ALBs and target groups
- ✅ Updated ECS services to use new target groups
- ✅ Fixed security group rules for health checks
- ✅ Both services accessible on new ALBs
- ⏳ Old shared ALB still active (can be decommissioned)
- ⏳ Applications may need configuration updates for new endpoints

## Implementation Date
Created: 2025-07-20

## Notes
- This is a development setup with both ALBs publicly accessible
- Security hardening required before production launch
- No real farmers are using the system yet
- Architectural separation achieved, ready for security implementation when needed