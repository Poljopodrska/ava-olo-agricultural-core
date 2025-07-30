# Manual Verification Steps - v3.4.3 CAVA LLM Deployment

## 🔍 Quick Verification Commands

Since the automated script cannot reach the production server, please run these manual checks:

### Step 1: Check Version (Browser or curl)
```bash
# In browser, go to:
https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/version

# Or via curl:
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/version
```

**Expected Result:**
```json
{
  "version": "v3.4.3-cava-llm-deployment-b4329ae-xxxxxxxx",
  "build_id": "b4329ae-xxxxxxxx"
}
```

✅ **SUCCESS**: Version shows `v3.4.3-cava-llm-deployment`  
❌ **FAIL**: Still shows old version

---

### Step 2: Check Debug Endpoint
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/debug
```

**Expected Result:**
```json
{
  "openai_key_set": true,
  "key_prefix": "sk-proj-Op",
  "cava_mode": "llm"
}
```

✅ **SUCCESS**: `openai_key_set: true` and `cava_mode: llm`  
❌ **FAIL**: `openai_key_set: false` or missing endpoint

---

### Step 3: Test Registration Intelligence
```bash
curl -X POST https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test123", "message": "i want to register"}'
```

**Good Response (LLM):**
- Natural, varied response asking for name
- No hardcoded greeting emojis
- Includes `"llm_used": true` in response

**Bad Response (Hardcoded):**
- "👋 Hello! I'm CAVA..."
- "Welcome to AVA OLO!"
- "Let's get you registered!"

✅ **SUCCESS**: Intelligent, natural response  
❌ **FAIL**: Hardcoded greeting detected

---

### Step 4: Test Bulgarian Registration
```bash
curl -X POST https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test456", "message": "Искам да се регистрирам"}'
```

**Expected:**
- Bulgarian response OR intelligent English response
- Shows understanding of registration intent
- NOT a generic hardcoded message

✅ **SUCCESS**: Understands Bulgarian registration intent  
❌ **FAIL**: Generic/hardcoded response

---

## 🎯 Quick Browser Test

1. Go to: `https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/version`
2. Look for: `v3.4.3-cava-llm-deployment`

If you see the new version, the deployment worked! 🎉

---

## 🚨 If Tests Fail

### Version Not Updated:
- Check ECS deployment status in AWS Console
- Look for failed deployments or errors
- Wait 2-3 more minutes and retry

### OpenAI Key Not Set:
1. Go to AWS ECS Console
2. Find `ava-olo-agricultural-core` service
3. Check task definition environment variables
4. Ensure `OPENAI_API_KEY` is set
5. Redeploy service if needed

### Still Getting Hardcoded Responses:
- This means the LLM engine isn't being used
- Check ECS logs for OpenAI API errors
- Verify the `OPENAI_API_KEY` environment variable
- Check for startup errors in logs

---

## 📊 Summary Checklist

- [ ] Version shows v3.4.3-cava-llm-deployment
- [ ] Debug endpoint shows openai_key_set: true
- [ ] "i want to register" gets intelligent response
- [ ] Bulgarian registration works
- [ ] No hardcoded greetings (👋, Welcome, etc.)

**All checks pass = Deployment successful! 🎉**