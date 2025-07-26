# EMERGENCY INFRASTRUCTURE REPORT
Generated: 2025-07-22 02:41:12

## SUMMARY
- Total ALBs found: 3
- Total ECS services: 3
- Total ECS services: 0
- Working endpoints found: 3

## WORKING ENDPOINTS

### ✅ ALB: ava-olo-farmers-alb
- URL: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/
- Status: HTTP 200

### ✅ ALB: ava-olo-internal-alb
- URL: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/
- Status: HTTP 200

### ✅ ALB: ch-alb
- URL: http://ch-alb-2140286266.us-east-1.elb.amazonaws.com/
- Status: HTTP 200

## INFRASTRUCTURE DETAILS

### Application Load Balancers

**ava-olo-farmers-alb**
- DNS: ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com
- State: active
- Target Groups: 1
- Healthy Targets: 1

**ava-olo-internal-alb**
- DNS: ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com
- State: active
- Target Groups: 1
- Healthy Targets: 1

**ch-alb**
- DNS: ch-alb-2140286266.us-east-1.elb.amazonaws.com
- State: active
- Target Groups: 1
- Healthy Targets: 1

### ECS Services

**agricultural-core** (Cluster: ava-olo-production)
- Status: ACTIVE
- Running: 1/1
- Task Definition: ava-agricultural-task:7

**monitoring-dashboards** (Cluster: ava-olo-production)
- Status: ACTIVE
- Running: 1/1
- Task Definition: ava-monitoring-task:10

**ch-production-service** (Cluster: ch-production)
- Status: ACTIVE
- Running: 1/1
- Task Definition: ch-production-task:2

## RECOVERY ACTIONS NEEDED
