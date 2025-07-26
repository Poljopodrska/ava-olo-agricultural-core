# Secure Deployment Instructions - Critical Fix 8a3408b

## 🔐 IMPORTANT: OpenAI API Key Configuration

The OpenAI API key MUST be set directly in AWS App Runner console for security.
GitHub will block any commits containing API keys.

### Step 1: Set OpenAI API Key in AWS

1. Go to AWS App Runner console
2. Find service: `ava-olo-agricultural-core`
3. Click "Update service"
4. Navigate to "Configure service" step
5. Add environment variable:
   - Name: `OPENAI_API_KEY`
   - Value: Copy from `.env.production` file
   - The key starts with: `sk-proj-Op4v...`

### Step 2: Verify Deployment

After setting the environment variable and deploying:

```bash
# Check if OpenAI key is configured
curl https://ava-olo-agricultural-core.us-east-1.awsapprunner.com/api/v1/registration/debug

# Should return:
{
  "openai_key_set": true,
  "key_prefix": "sk-proj-Op",
  "cava_mode": "llm"
}
```

### Step 3: Test Registration

```bash
# Test with English
curl -X POST https://ava-olo-agricultural-core.us-east-1.awsapprunner.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test123", "message": "I want to register"}'

# Test with Bulgarian
curl -X POST https://ava-olo-agricultural-core.us-east-1.awsapprunner.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test456", "message": "Искам да се регистрирам"}'
```

## 🚨 Critical Notes

1. **NEVER commit API keys to Git**
2. **ALWAYS set sensitive values in AWS console**
3. **The system will fail Constitutional compliance without OpenAI key**

## Environment Variables Required

Set these in AWS App Runner:

- `OPENAI_API_KEY`: Get from .env.production (starts with sk-proj-Op4v)
- `DB_HOST`: farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
- `DB_NAME`: farmer_crm
- `DB_USER`: postgres
- `DB_PASSWORD`: Get from secure storage
- `DB_PORT`: 5432

## Verification Script

Run after deployment:
```bash
python verify_deployment_8a3408b.py
```

This will check:
- Version contains commit hash
- Debug endpoint works
- Registration uses LLM
- No hardcoded responses