# AVA OLO Constitutional Design System - Deployment Instructions

## Overview
This deployment updates both the Agricultural Core and Monitoring Dashboard services with the new constitutional design system.

## Pre-Deployment Checklist
- [x] Constitutional design system created in `/shared/design-system/`
- [x] Services updated with new design: `agricultural_core_constitutional.py` and `monitoring_api_constitutional.py`
- [x] Dockerfiles created: `Dockerfile.agricultural-constitutional` and `Dockerfile.monitoring-constitutional`
- [x] Task definitions prepared
- [x] Deployment scripts ready

## Deployment Steps

### Option 1: Full Deployment (with Docker)

1. **Build and Push Docker Images**
   ```bash
   # Run from a machine with Docker installed
   chmod +x deploy-constitutional.sh
   ./deploy-constitutional.sh
   ```

### Option 2: ECS Deployment Only (without Docker build)

If Docker images are already built and pushed:

1. **Make deployment script executable**
   ```bash
   chmod +x deploy-ecs-constitutional.sh
   ```

2. **Run ECS deployment**
   ```bash
   ./deploy-ecs-constitutional.sh
   ```

### Option 3: Manual Deployment

1. **Build Docker Images**
   ```bash
   # Agricultural Core
   docker build -f Dockerfile.agricultural-constitutional -t ava-olo/agricultural-core:v2.5.0-constitutional .
   
   # Monitoring API
   docker build -f Dockerfile.monitoring-constitutional -t ava-olo/monitoring-dashboards:v2.5.0-constitutional .
   ```

2. **Push to ECR**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 127679825789.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag and push Agricultural Core
   docker tag ava-olo/agricultural-core:v2.5.0-constitutional 127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest
   docker push 127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/agricultural-core:latest
   
   # Tag and push Monitoring
   docker tag ava-olo/monitoring-dashboards:v2.5.0-constitutional 127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/monitoring-dashboards:latest
   docker push 127679825789.dkr.ecr.us-east-1.amazonaws.com/ava-olo/monitoring-dashboards:latest
   ```

3. **Register Task Definitions**
   ```bash
   aws ecs register-task-definition --cli-input-json file://task-definition-agricultural-constitutional.json --region us-east-1
   aws ecs register-task-definition --cli-input-json file://task-definition-monitoring-constitutional.json --region us-east-1
   ```

4. **Update ECS Services**
   ```bash
   # Force new deployment for both services
   aws ecs update-service --cluster ava-olo-production --service agricultural-core --force-new-deployment --region us-east-1
   aws ecs update-service --cluster ava-olo-production --service monitoring-dashboards --force-new-deployment --region us-east-1
   ```

## Post-Deployment Verification

1. **Check Service Status**
   ```bash
   aws ecs describe-services --cluster ava-olo-production --services agricultural-core monitoring-dashboards --region us-east-1
   ```

2. **Test Endpoints**
   - Business Dashboard: http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/business-dashboard
   - Health Check: http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/health
   - Monitoring: http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/

3. **Verify Constitutional Design**
   - [ ] AVA OLO logo visible (atomic structure)
   - [ ] Olive green color scheme (#6B7D46)
   - [ ] Version number displayed (top right)
   - [ ] All text ≥ 18px
   - [ ] Enter key works on forms
   - [ ] Mobile responsive design

4. **Check Database Connection**
   - Verify farmer count shows real data (4 farmers)
   - Not hardcoded "16" anymore

## Rollback Instructions

If needed, revert to previous task definition:
```bash
# Rollback agricultural-core to revision 4
aws ecs update-service --cluster ava-olo-production --service agricultural-core --task-definition ava-agricultural-task:4 --region us-east-1

# Rollback monitoring-dashboards
aws ecs update-service --cluster ava-olo-production --service monitoring-dashboards --task-definition ava-monitoring-task:PREVIOUS_REVISION --region us-east-1
```

## Important Files
- Design System: `/shared/design-system/`
- Agricultural Core: `agricultural_core_constitutional.py`
- Monitoring API: `monitoring_api_constitutional.py`
- Dockerfiles: `Dockerfile.agricultural-constitutional`, `Dockerfile.monitoring-constitutional`
- Task Definitions: `task-definition-agricultural-constitutional.json`, `task-definition-monitoring-constitutional.json`

## Support
Check CloudWatch logs for any issues:
- Agricultural: `/ecs/ava-agricultural`
- Monitoring: `/ecs/ava-monitoring`