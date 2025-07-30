# Manual ECS Environment Variables Update

## Important Discovery
The `ava-agricultural-task` is using AWS Secrets Manager for sensitive values like DB_PASSWORD. This is more secure but requires different handling.

## Quick Manual Update Instructions

### 1. Update Secrets Manager (for Agricultural Task)
```bash
# Update the database password in Secrets Manager
aws secretsmanager update-secret \
  --secret-id ava-olo/database \
  --secret-string '{"DB_PASSWORD":"j2D8J4LH:~eFrUz>$:kkNT(P$Rq_"}' \
  --region us-east-1
```

### 2. Update Task Definitions via Console

#### For ava-agricultural-task:
1. Go to: https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions/ava-agricultural-task
2. Click "Create new revision"
3. Click on container name
4. In "Environment variables" section, add:
   - OPENAI_API_KEY = [REDACTED - Use actual API key]
   - OPENWEATHER_API_KEY = 53efe5a8c7ac5cad63b7b0419f5d3069
   - SECRET_KEY = 8tsHicCkKBHvwk51zNp80RY2uUZGTLAb
   - JWT_SECRET_KEY = pJnruaBvL9ZLvWqr7QLtvXv9F0xw1kO6
5. Keep existing secrets configuration for DB_PASSWORD
6. Create revision

#### For ava-monitoring-task:
1. Go to: https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions/ava-monitoring-task
2. Add ALL environment variables from ecs-env-vars.json

### 3. Update Services
1. Go to cluster: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ava-olo-production
2. Update each service to use the new task definition revision

## Environment Variables Summary

### API Keys (Add to Both Tasks):
- OPENAI_API_KEY = [REDACTED - Use actual API key]
- OPENWEATHER_API_KEY = 53efe5a8c7ac5cad63b7b0419f5d3069

### Security Keys (Add to Both Tasks):
- SECRET_KEY = 8tsHicCkKBHvwk51zNp80RY2uUZGTLAb
- JWT_SECRET_KEY = pJnruaBvL9ZLvWqr7QLtvXv9F0xw1kO6

### Database (Agricultural uses Secrets Manager, Monitoring needs all):
- DB_HOST = farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
- DB_NAME = farmer_crm
- DB_USER = postgres
- DB_PORT = 5432
- DB_PASSWORD = j2D8J4LH:~eFrUz>$:kkNT(P$Rq_

### AWS Config (Add to Both):
- AWS_REGION = us-east-1
- AWS_DEFAULT_REGION = us-east-1
- ENVIRONMENT = production
- DEBUG = false
- LOG_LEVEL = INFO

## Verification
After updating, check:
- http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check
- http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/api/v1/system/env-check