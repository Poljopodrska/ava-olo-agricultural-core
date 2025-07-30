# AWS IAM Requirements for AVA OLO

## Critical IAM Policies Required

### ECS Task Execution Role
The ECS Task Execution Role MUST have the following policies:

1. **AmazonECSTaskExecutionRolePolicy** (AWS Managed)
2. **AVA-OLO-SecretsManagerAccess** (Custom Policy - REQUIRED)

## AVA-OLO-SecretsManagerAccess Policy

**Policy ARN**: `arn:aws:iam::127679825789:policy/AVA-OLO-SecretsManagerAccess`

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

## Why This Is Critical

### Historical Context
- **Date**: 2025-07-27
- **Impact**: Without this permission, ECS tasks cannot retrieve database passwords
- **Symptoms**: This caused 17+ deployment failures before being identified
- **Services Affected**: Both agricultural-core and monitoring-dashboards require this

### Failure Symptoms
When this policy is missing, you'll see:
```
ResourceInitializationError: unable to pull secrets or registry auth: 
execution resource retrieval failed: unable to retrieve secret from asm: 
service call has been retried 1 time(s): 
api error AccessDeniedException: User: arn:aws:sts::127679825789:assumed-role/ecsTaskExecutionRole/[TASK-ID] 
is not authorized to perform: secretsmanager:GetSecretValue on resource: [SECRET-ARN]
```

## Verification Commands

### Check if role has correct permissions:
```bash
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole --region us-east-1
```

### Verify specific policy exists:
```bash
aws iam get-policy --policy-arn arn:aws:iam::127679825789:policy/AVA-OLO-SecretsManagerAccess --region us-east-1
```

### Test secret access (from ECS task):
```bash
aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/db-user-hBjI7G --region us-east-1
```

## Required Secrets

### Database Credentials
- `arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/db-user-hBjI7G`
- `arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/db-password-dx40Ty`

### API Keys
- `arn:aws:secretsmanager:us-east-1:127679825789:secret:ava-olo/openai-api-key-Y9OSed`

## Emergency Recovery Procedure

If ECS tasks are failing to start with secrets errors:

1. **Check CloudWatch logs** for 'AccessDeniedException'
2. **Verify role policies**:
   ```bash
   aws iam list-attached-role-policies --role-name ecsTaskExecutionRole
   ```
3. **If missing, create and attach policy**:
   ```bash
   # Create policy (use JSON above)
   aws iam create-policy --policy-name AVA-OLO-SecretsManagerAccess --policy-document file://policy.json
   
   # Attach to role
   aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::127679825789:policy/AVA-OLO-SecretsManagerAccess
   ```
4. **Force new deployment**:
   ```bash
   aws ecs update-service --cluster ava-olo-production --service agricultural-core --force-new-deployment
   ```

## Security Notes

- This policy follows least privilege principle
- Only grants access to specific AVA-OLO secrets
- Uses wildcard suffixes to handle AWS secret versioning
- No additional permissions beyond secrets retrieval

## Maintenance

- Review policy quarterly
- Add new secrets to resource list as needed
- Monitor CloudWatch for access denied errors
- Document any changes in SYSTEM_CHANGELOG.md

---

**Last Updated**: 2025-07-27  
**Emergency Fix**: This documentation created after resolving 17+ deployment failures  
**Critical Importance**: Required for all ECS task startup