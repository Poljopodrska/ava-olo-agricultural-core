# DIAGNOSTIC REPORT - v3.4.3-diagnostic

## 🚨 Issue: LLM Registration Not Working in Production

**Date**: 2025-07-26  
**Version**: v3.4.3-diagnostic  
**Reporter**: Claude Code

---

## 🔍 Diagnostic Changes Made

### 1. Enhanced Logging in Registration Endpoint

Added critical logging to `/api/v1/registration/cava`:
```python
logger.critical(f"🚨 REGISTRATION ENDPOINT CALLED: message='{message}', session_id='{session_id}'")
logger.critical(f"🔑 OPENAI_KEY_STATUS: exists={bool(os.getenv('OPENAI_API_KEY'))}, length={len(os.getenv('OPENAI_API_KEY', ''))}")
logger.critical(f"📍 REQUEST_PATH: {request.url.path}")
```

### 2. New Diagnostic Endpoints

#### `/api/v1/registration/llm-status`
Returns:
- OpenAI key status
- CAVA engine loading status
- Engine initialization errors
- Critical readiness check

#### `/api/v1/registration/all-endpoints`
Returns:
- All registration-related endpoints
- Helps verify frontend is calling correct endpoint

---

## 🧪 How to Test in Production

### Step 1: Check Version
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/version
```
Should show: `v3.4.3-diagnostic-...`

### Step 2: Check LLM Status
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/llm-status
```
Look for:
- `openai_key_exists`: true/false
- `cava_engine_initialized`: true/false
- `engine_error`: Any error messages
- `critical_check`: 🟢 READY or 🔴 NOT READY

### Step 3: List All Endpoints
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/all-endpoints
```
Check which registration endpoints exist

### Step 4: Test Registration with Verbose Logging
```bash
curl -X POST https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "diagnostic_test", "message": "i want to register"}'
```

Then check ECS logs for critical logging output.

---

## 🎯 Common Issues and Solutions

### Issue 1: OpenAI Key Not Set
**Symptom**: `openai_key_exists: false`  
**Solution**: 
1. Go to ECS Task Definition
2. Add environment variable: `OPENAI_API_KEY`
3. Redeploy service

### Issue 2: Engine Fails to Initialize
**Symptom**: `engine_error: "OpenAI API key REQUIRED..."`  
**Solution**: Same as Issue 1 - set the API key

### Issue 3: Frontend Calling Wrong Endpoint
**Symptom**: Registration works via curl but not in app  
**Solution**: 
1. Check `/api/v1/registration/all-endpoints`
2. Verify frontend calls `/api/v1/registration/cava`
3. NOT `/api/v1/chat/register` or other endpoints

### Issue 4: Old Code Still Running
**Symptom**: Hardcoded responses like "👋 Hello! I'm CAVA..."  
**Solution**: 
1. Force new deployment in ECS
2. Check deployment events for errors
3. Ensure health checks pass

---

## 📊 Expected Successful Response

When everything works:
```json
{
  "response": "Hello! I'd be happy to help you register. Could you please tell me your name?",
  "registration_complete": false,
  "llm_used": true,
  "constitutional_compliance": true
}
```

Note: Response varies each time (proof of LLM)

---

## 🚑 Emergency Fixes

### If OpenAI Key Missing in ECS:
1. AWS Console → ECS → Services → ava-olo-agricultural-core
2. Update Service → Task Definition → Environment Variables
3. Add: `OPENAI_API_KEY` = `sk-proj-Op...` (from .env.production)
4. Deploy Changes

### If Deployment Stuck:
1. Stop all tasks
2. Update service to 0 desired tasks
3. Wait 30 seconds
4. Update back to desired count
5. Force new deployment

---

## 📝 Diagnostic Checklist

- [ ] Version shows v3.4.3-diagnostic
- [ ] `/api/v1/registration/llm-status` accessible
- [ ] OpenAI key exists in environment
- [ ] Engine initializes without errors
- [ ] Registration returns varied responses
- [ ] No hardcoded greetings detected
- [ ] ECS logs show critical logging output

---

## 🔗 Related Files

- `/modules/cava/routes.py` - Main registration routes with diagnostic logging
- `/modules/cava/cava_registration_engine.py` - LLM engine requiring OpenAI key
- `/tests/test_cava_registration_llm.py` - Unfakeable LLM tests
- `verify_cava_llm_deployment.py` - Deployment verification script