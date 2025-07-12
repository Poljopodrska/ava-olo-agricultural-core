# 📜 AVA OLO CONSTITUTIONAL DOCUMENTS

## 🚨 SINGLE SOURCE OF TRUTH

This directory contains ALL constitutional documents for the AVA OLO system. 
**NO constitutional documents should exist outside this directory!**

## 📋 Document Hierarchy

1. **AVA_OLO_CONSTITUTION.md** - The supreme law (12 principles)
2. **SYSTEM_CONFIG.md** - System configuration and AWS deployment details
3. **PROJECT_STRUCTURE.md** - Official folder organization
4. **DEVELOPMENT_CHECKLIST.md** - Pre-development mandatory checks
5. **STARTUP_CHECKLIST.md** - System startup verification
6. **CONSTITUTIONAL_COMPLIANCE.md** - Compliance guidelines
7. **GIT_COMMANDS_CONSTITUTIONAL.md** - Git workflow commands

## 🎯 Reading Order

For new developers:
1. Start with AVA_OLO_CONSTITUTION.md
2. Read DEVELOPMENT_CHECKLIST.md
3. Review PROJECT_STRUCTURE.md
4. Check SYSTEM_CONFIG.md for infrastructure

## 🔍 Quick Reference

- **Mango Test**: Would this work for a mango farmer in Bulgaria?
- **Database**: AWS RDS PostgreSQL (farmer_crm)
- **URLs**: https://6pmgiripe.us-east-1.awsapprunner.com/[dashboard]/
- **No Hardcoding**: LLM-first approach for all logic

## ⚠️ Constitutional Violations

If you find constitutional documents elsewhere:
1. Move them to this directory immediately
2. Update cross-references
3. Delete the duplicates
4. Commit with "CONSTITUTIONAL:" prefix

## 🏗️ Maintenance

All updates to constitutional documents must:
- Maintain AWS deployment compatibility
- Pass the mango test
- Follow LLM-first principles
- Be committed with clear messages