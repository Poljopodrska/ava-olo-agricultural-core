# 🚨 CLAUDE CODE: READ THIS BEFORE ANY DEVELOPMENT

## 📁 FOLDER CHECK (MANDATORY)
1. Read PROJECT_STRUCTURE.md completely
2. Identify which existing folder your work belongs in
3. NEVER create new folders - use existing structure
4. If unsure, ask: "Does this belong in existing monitoring structure?"

## 🎯 CURRENT PROJECT: DATABASE DASHBOARD
- Location: Use existing monitoring dashboard structure
- All database dashboard code goes in existing folders
- NO new dashboard folders allowed

## 📜 CONSTITUTIONAL CHECK
1. Would this work for Bulgarian mango farmer? (🥭 MANGO RULE)
2. Am I using LLM-first approach? (🧠 LLM-FIRST)
3. Does this maintain module independence? (🏗️ MODULE INDEPENDENCE)
4. Am I following privacy-first principles? (🔒 PRIVACY-FIRST)

## 🚫 FORBIDDEN ACTIONS
- Creating folders like `new_dashboard/` (use existing monitoring/)
- Creating folders like `database_admin/` (use existing structure)  
- Duplicating functionality across folders
- Hardcoded language/crop patterns (CONSTITUTIONAL VIOLATION!)

## ✅ CORRECT APPROACH
- Use existing monitoring folder structure
- Implement LLM-first query processing (NO hardcoded patterns!)
- Follow constitutional principles
- Test mango compliance: "Would this work in Bulgaria?"

## 🌐 AWS DEPLOYMENT
- Platform: AWS App Runner  
- URLs: https://6pmgiripe.us-east-1.awsapprunner.com/database/
- Database: AWS RDS (farmer-crm-production)
- NO port numbers - use HTTPS URLs only

## 🔍 BEFORE WRITING CODE

### Step 1: Constitutional Verification
```python
# BAD - Hardcoded patterns
if "tomato" in query or "potato" in query:
    # VIOLATION: Won't work for mango in Bulgaria!

# GOOD - LLM-first approach  
llm_result = await llm_handler.process_agricultural_query(query)
# Works for ANY crop in ANY country!
```

### Step 2: Folder Verification
```bash
# Check existing structure
cat PROJECT_STRUCTURE.md

# Place files in correct location:
# ✅ database_explorer.py (existing file)
# ✅ templates/database_explorer.html
# ❌ new_folder/database_admin.py (FORBIDDEN!)
```

### Step 3: AWS Compatibility
```python
# BAD - Local development mindset
url = "http://localhost:8005/health"

# GOOD - AWS production ready
url = "https://6pmgiripe.us-east-1.awsapprunner.com/database/health"
```

## 📊 DATABASE DASHBOARD SPECIFICS

### LLM-First Query Processing
1. Use `llm_query_handler.py` for natural language processing
2. NO hardcoded SQL patterns
3. Support ANY language (English, Slovenian, Bulgarian, etc.)
4. Test with: "Show me mango fields in Bulgaria"

### Constitutional Compliance
```python
# The database dashboard MUST:
- Use OpenAI GPT-4 for query generation (LLM-first)
- Work for any crop type (mango test)
- Support any language (universal application)
- Maintain farmer privacy (no personal data exposure)
```

## 🚀 DEPLOYMENT CHECKLIST
- [ ] No localhost references
- [ ] No port numbers in URLs  
- [ ] AWS RDS connection via environment variables
- [ ] HTTPS URLs only
- [ ] Constitutional mango test passed

## 🆘 IF YOU GET STUCK
1. Re-read AVA_OLO_CONSTITUTION.md
2. Check PROJECT_STRUCTURE.md for folder rules
3. Run mango test: "Would this work for Bulgarian mango farmer?"
4. Verify LLM-first approach (no hardcoded patterns)

## 🎯 REMEMBER
**The goal is a universal agricultural system that works for ANY crop in ANY country using LLM intelligence, NOT hardcoded patterns!**