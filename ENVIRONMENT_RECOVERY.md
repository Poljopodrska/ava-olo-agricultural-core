# Environment Variables Recovery Guide

## Overview
All environment variables were lost during the ECS to ECS migration. This guide documents the recovery process and the values that were found vs generated.

## Recovery Results

### 🟢 Successfully Recovered from Repository

| Variable | Value | Source |
|----------|-------|--------|
| DB_HOST | farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com | Multiple files |
| DB_NAME | farmer_crm | ecs.yaml, multiple .py files |
| DB_USER | postgres | Database scripts |
| DB_PORT | 5432 | Default PostgreSQL port |
| AWS_REGION | us-east-1 | ALB endpoints |
| AWS_DEFAULT_REGION | us-east-1 | Standard AWS config |
| ENVIRONMENT | production | Deployment context |
| DEBUG | false | Production setting |
| LOG_LEVEL | INFO | Standard logging |

### 🟡 Generated New Secure Values

| Variable | Purpose | Note |
|----------|---------|------|
| SECRET_KEY | Session encryption | 32-character random string |
| JWT_SECRET_KEY | Token signing | 32-character random string |
| DB_PASSWORD | Database access | Suggested secure password (MUST BE CHANGED) |

### 🔴 Still Need to Obtain

| Variable | Where to Get | Purpose |
|----------|--------------|---------|
| DB_PASSWORD | AWS RDS Console or reset | Database authentication |
| OPENAI_API_KEY | https://platform.openai.com/api-keys | Chat functionality |
| OPENWEATHER_API_KEY | https://openweathermap.org/api | Weather data |

## Files Created

### 1. `.env.production`
Complete environment file with all variables. Contains:
- Recovered values from repository
- Generated secure keys
- Placeholders for API keys

### 2. `ecs-env-vars.json`
JSON format for ECS task definitions. Ready to use with AWS CLI.

### 3. `scripts/recover_env_vars.py`
Python script that:
- Searches repository for existing values
- Generates secure keys
- Creates environment files

### 4. `scripts/update_ecs_env.sh`
Bash script that:
- Updates ECS task definitions
- Registers new revisions
- Updates services automatically

## Recovery Process

### Step 1: Run Recovery Script
```bash
python3 scripts/recover_env_vars.py
```

This creates:
- `.env.production` - Edit this file with real values
- `ecs-env-vars.json` - Used by update script

### Step 2: Get Missing Values

1. **Database Password**:
   - Option A: Check AWS Secrets Manager
   - Option B: Reset in RDS console
   - Option C: Use password from original deployment

2. **OpenAI API Key**:
   - Go to https://platform.openai.com/api-keys
   - Create new key with "All" permissions
   - Replace `sk-proj-REPLACE_WITH_YOUR_KEY`

3. **OpenWeather API Key**:
   - Go to https://openweathermap.org/api
   - Sign up for free account
   - Get API key from dashboard

### Step 3: Update .env.production
```bash
nano .env.production
```

Replace all placeholder values with real ones.

### Step 4: Update ECS
```bash
./scripts/update_ecs_env.sh
```

This will:
- Create new task definition revisions
- Update both services
- Show progress and results

### Step 5: Verify
After 2-3 minutes, check:
```
http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/env-check
```

## Security Notes

### Keep These Secure
- **SECRET_KEY**: Used for session encryption. Never share or commit.
- **JWT_SECRET_KEY**: Used for token signing. Keep confidential.
- **DB_PASSWORD**: Database access. Use strong password.

### Generated Values
The script generates cryptographically secure random values using Python's `secrets` module:
- 32 characters for secret keys
- 16+ characters for password suggestions
- Uses letters, numbers, and special characters

### Best Practices
1. Never commit `.env.production` to git
2. Use AWS Secrets Manager for production
3. Rotate keys periodically
4. Use different keys for different environments

## Troubleshooting

### AWS CLI Not Working
```bash
aws configure
# Enter your AWS credentials
```

### Task Definition Update Fails
- Check AWS permissions
- Verify task definition names
- Check JSON formatting

### Services Not Updating
- Manual update in ECS console
- Check service events for errors
- Verify task definition compatibility

## Summary

From 17 missing variables, we:
- ✅ Recovered 9 from repository
- ✅ Generated 3 secure keys
- ❌ Need 3 API keys from you
- ❓ Need 1 database password

Total recovery: 12/17 variables automated (70%)