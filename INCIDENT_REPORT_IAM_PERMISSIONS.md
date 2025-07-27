# INCIDENT REPORT: Agricultural-Core Service Extended Outage Resolution
**Date**: 2025-07-27  
**Time**: 13:47 - 15:49 CET  
**Service**: Agricultural-Core (ECS)  
**Severity**: CRITICAL - Complete Service Outage  
**Duration**: Extended (days/weeks based on failed deployment count)  

## Executive Summary
The agricultural-core service experienced a complete outage for an extended period due to missing IAM permissions preventing ECS tasks from accessing AWS Secrets Manager. The issue was resolved by creating and attaching the `AVA-OLO-SecretsManagerAccess` IAM policy to the ECS Task Execution Role.

## Timeline of Events
- **Unknown Start Date**: Service began failing deployments (accumulated 17+ failures)
- **2025-07-27 14:28 CET**: Emergency investigation initiated
- **2025-07-27 14:47 CET**: Root cause identified - IAM permissions missing
- **2025-07-27 15:47 CET**: IAM policy created and attached
- **2025-07-27 15:49 CET**: Service successfully deployed and verified operational

## Root Cause Analysis
### Primary Issue
The ECS Task Execution Role (`ecsTaskExecutionRole`) lacked the `secretsmanager:GetSecretValue` permission required to retrieve database credentials and API keys from AWS Secrets Manager.

### Error Pattern
```
ResourceInitializationError: unable to pull secrets or registry auth: 
execution resource retrieval failed: unable to retrieve secret from asm: 
api error AccessDeniedException: User: arn:aws:sts::127679825789:assumed-role/ecsTaskExecutionRole/[task-id] 
is not authorized to perform: secretsmanager:GetSecretValue
```

### Impact
- **17+ consecutive deployment failures**
- **Complete service unavailability** for extended period
- **No farmer access** to agricultural features
- **All CAVA functionality offline**

## Resolution Steps
### 1. Created IAM Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/db-user-*",
                "arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/db-password-*",
                "arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/openai-api-key-*"
            ]
        }
    ]
}
```

### 2. Attached Policy to Role
```bash
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::127679825789:policy/AVA-OLO-SecretsManagerAccess
```

### 3. Forced New Deployment
```bash
aws ecs update-service \
  --cluster ava-olo-production \
  --service agricultural-core \
  --force-new-deployment
```

## Verification
- **Service Status**: 1/1 tasks running stable
- **Health Endpoint**: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/health (200 OK)
- **Version Running**: v3.5.6-error-fix-error-fix-070cc9bd
- **Deployment State**: COMPLETED
- **No Failed Tasks**: 0 failures post-fix

## Lessons Learned
1. **ECS Task Execution Roles require explicit Secrets Manager permissions** beyond the default policy
2. **CloudWatch logs are critical** for diagnosing permission issues
3. **Infrastructure issues can masquerade as code problems** - always check IAM first
4. **Extended outages accumulate failed deployments** making the issue appear worse than it is

## Prevention Measures
1. **Documentation Created**: AWS_IAM_REQUIREMENTS.md with complete setup guide
2. **Troubleshooting Added**: DEPLOYMENT_STANDARD.md updated with IAM section
3. **Emergency Procedures**: Step-by-step recovery process documented
4. **Version Tagged**: v3.5.21-iam-fix-stable for historic reference

## Action Items
- [ ] Enable deployment circuit breaker to prevent endless retry loops
- [ ] Set up CloudWatch alarms for failed task launches
- [ ] Review all ECS services for similar IAM issues
- [ ] Create automated IAM permission validation script

## Technical Details
- **IAM Policy ARN**: `arn:aws:iam::127679825789:policy/AVA-OLO-SecretsManagerAccess`
- **Task Definition**: ava-agricultural-task:86
- **ECS Cluster**: ava-olo-production
- **AWS Region**: us-east-1

## Business Impact
The Bulgarian mango farmer and all other users regained full access to:
- Agricultural feature registration
- CAVA chat functionality  
- Field management tools
- All core agricultural services

## Conclusion
This incident highlighted a critical gap in IAM permissions that prevented the agricultural-core service from functioning for an extended period. The fix was simple but the impact was severe. With proper documentation and preventive measures now in place, this issue should never recur.

---
**Report Generated**: 2025-07-27 16:15:00 CET  
**Report Author**: Claude Code (Emergency Response)  
**Status**: RESOLVED ✅