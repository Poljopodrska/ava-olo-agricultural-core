# Critical Deployment: Commit 8a3408b - Constitutional Fix

## 🚨 CONSTITUTIONAL VIOLATION FIXED

**Violation**: Registration endpoint was using hardcoded responses instead of LLM
**Amendment**: Constitutional Amendment #15 requires 95%+ LLM intelligence
**Impact**: All registration flows were non-compliant
**Commit**: 8a3408b

## Deployment Status

**Target Version**: v3.4.2-constitutional-fix-8a3408b
**Build ID Format**: 8a3408b-xxxxxxxx
**Deployment Time**: 2025-07-26 14:30:00

## Verification Steps

### 1. Version Check
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/version
```
**Expected Response**:
```json
{
  "version": "v3.4.2-constitutional-fix-8a3408b-xxxxxxxx",
  "build_id": "8a3408b-xxxxxxxx"
}
```

### 2. Debug Endpoint Check
```bash
curl https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/debug
```
**Expected Response**:
```json
{
  "openai_key_set": true,
  "key_prefix": "sk-proj-Op",
  "cava_mode": "llm"
}
```

### 3. Registration Test
```bash
curl -X POST https://ava-olo-agricultural-core.us-east-1.elb.amazonaws.com/api/v1/registration/cava \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": "test123", "message": "I want to register", "language": "en"}'
```

**Should NOT contain**:
- ❌ "👋 Hello! I'm CAVA"
- ❌ "Welcome to AVA OLO!"
- ❌ "Let's get you registered!"

**Should contain**: Natural LLM-generated response

## Files Changed

1. **modules/cava/routes.py**:
   - Line 33-48: Changed to use `enhanced_cava` instead of `registration_flow`
   - Line 319-328: Added debug endpoint

2. **modules/chat/openai_chat.py**:
   - Line 112: Added constitutional logging
   - Line 133: Added warning for fallback mode
   - Line 161: Added success logging

3. **modules/cava/enhanced_cava_registration.py**:
   - Line 193-199: Added registration intent detection

4. **main.py**:
   - Line 115-136: Added critical startup checks

5. **modules/core/config.py**:
   - Line 14-17: Updated version with commit hash

## Deployment Actions

### Created Scripts:
- `verify_deployment_8a3408b.py` - Automated verification
- `force_deploy_8a3408b.py` - Force deployment trigger
- `ensure_openai_key.py` - Environment verification

### Configuration Updates:
- Updated ecs.yaml with commit reference
- Added OpenAI API key to environment
- Set FORCE_REBUILD to trigger deployment

## Success Criteria Checklist

- [ ] Version endpoint shows 8a3408b in build ID
- [ ] Debug endpoint returns openai_key_set: true
- [ ] Registration test uses LLM (no hardcoded responses)
- [ ] Server logs show "🏛️ CONSTITUTIONAL LLM CALL"
- [ ] Bulgarian test "Искам да се регистрирам" works
- [ ] No timeout errors on registration endpoint

## Manual Deployment Steps (if automatic fails)

1. **AWS ECS Console**:
   - Navigate to ava-olo-agricultural-core service
   - Click "Deploy" button
   - Wait for deployment to complete

2. **Verify Environment Variables**:
   - Ensure OPENAI_API_KEY is set
   - Value should start with: sk-proj-Op

3. **Monitor Deployment**:
   - Check deployment logs
   - Look for "Build completed - v3.4.2-constitutional-fix-8a3408b"

## Post-Deployment Testing

Run verification script:
```bash
python verify_deployment_8a3408b.py
```

Test Bulgarian registration:
```bash
python test_bulgarian_registration.py
```

## Rollback Plan

If deployment fails or causes issues:
1. Revert to previous commit in ECS
2. Check environment variables
3. Review deployment logs for errors
4. Ensure database connectivity

## Contact

For deployment issues:
- Check AWS ECS logs
- Verify environment variables
- Ensure GitHub webhook is configured