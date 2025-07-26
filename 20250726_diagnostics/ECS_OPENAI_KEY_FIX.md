# ECS OpenAI Key Configuration Fix

**CRITICAL**: The OpenAI API key must be added to ECS Task Definition to enable LLM registration

## 🔧 Manual Steps Required (AWS Console)

### 1. Go to ECS Task Definitions
1. Open AWS Console
2. Navigate to: ECS → Task Definitions
3. Find: `ava-agricultural-task`
4. Click on the task definition name

### 2. Create New Revision
1. Click "Create new revision"
2. Scroll to "Environment variables" section
3. Click "Add environment variable"

### 3. Add OpenAI Key
Add the following environment variable:
- **Name**: `OPENAI_API_KEY`
- **Value**: `[GET FROM .env.production FILE - starts with sk-proj-Op4v...]`
- **Value from**: Environment variable

⚠️ **IMPORTANT**: Copy the actual key from `.env.production` file line 18

### 4. Save Task Definition
1. Keep all other settings the same
2. Click "Create" to save new revision
3. Note the new revision number (e.g., ava-agricultural-task:15)

### 5. Update Service
1. Go to: ECS → Clusters → ava-olo-cluster
2. Find service: `ava-olo-agricultural-core`
3. Click "Update"
4. Under "Task definition", select the new revision
5. Check "Force new deployment"
6. Click "Update service"

### 6. Monitor Deployment
1. Go to "Events" tab
2. Wait for "service has reached a steady state"
3. Check "Tasks" tab - old tasks should stop, new ones start

## 🧪 Verification Commands

After deployment completes (2-3 minutes):

```bash
# Check if OpenAI key is now set
curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/registration/llm-status

# Should show:
# "openai_key_exists": true
# "critical_check": "🟢 READY"
```

```bash
# Test registration with LLM
curl -X POST http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test_llm", "message": "i want to register"}'

# Should return natural, varied response NOT hardcoded greeting
```

## 🚨 If Issues Persist

1. Check ECS task logs for errors
2. Verify the API key is valid (test locally first)
3. Ensure no typos in environment variable name
4. Check task has enough memory/CPU

## 📊 Expected Result

Once deployed:
- Registration will use OpenAI GPT-4 for responses
- Each "i want to register" gets unique, intelligent response
- Multi-language support works (Bulgarian, Spanish, etc.)
- No more hardcoded greetings