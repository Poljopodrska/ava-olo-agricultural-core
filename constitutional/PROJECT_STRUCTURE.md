# AVA OLO PROJECT STRUCTURE (CONSTITUTIONAL)

## 📜 MANDATORY READING
Before ANY development:
1. Read AVA_OLO_CONSTITUTION.md
2. Read this PROJECT_STRUCTURE.md  
3. NEVER create new folders without updating this document

## 📁 OFFICIAL FOLDER STRUCTURE
```
ava-olo-monitoring-dashboards/ (THIS REPOSITORY)
├── constitutional/         # ALL CONSTITUTIONAL DOCUMENTS (SINGLE SOURCE OF TRUTH)
│   ├── AVA_OLO_CONSTITUTION.md     # Core 12 principles
│   ├── SYSTEM_CONFIG.md            # System configuration
│   ├── PROJECT_STRUCTURE.md        # THIS FILE
│   ├── DEVELOPMENT_CHECKLIST.md    # Pre-development checks
│   ├── STARTUP_CHECKLIST.md        # Startup verification
│   ├── CONSTITUTIONAL_COMPLIANCE.md # Compliance guidelines
│   ├── GIT_COMMANDS_CONSTITUTIONAL.md # Git workflow
│   └── README.md                   # Constitutional guide
│
├── templates/              # HTML templates for all dashboards
├── monitoring/             # Monitoring modules
│   ├── config/            # Configuration files
│   ├── core/              # Core monitoring logic
│   ├── interfaces/        # API interfaces
│   └── templates/         # Additional templates
├── static/                # Static assets (CSS, JS, images)
├── backup_*/              # Backup directories (DO NOT USE)
│
├── health_check_dashboard.py    # System health monitor
├── business_dashboard.py        # Business KPIs
├── database_explorer.py         # AI-driven database queries
├── agronomic_approval.py        # Expert approval interface
├── admin_dashboard.py           # Admin interface
├── database_operations.py       # Shared database utilities
├── config.py                    # Configuration settings
├── llm_query_handler.py        # LLM-first query processing
└── README.md                   # Repository overview
```

## 🚨 FOLDER RULES (CONSTITUTIONAL)

### ✅ ALLOWED ACTIONS
- Modify files WITHIN existing folders
- Add new files to appropriate existing folders
- Update this PROJECT_STRUCTURE.md when changes needed

### ❌ FORBIDDEN ACTIONS  
- Creating new top-level folders without constitutional review
- Duplicating functionality in different folders
- Moving files between folders without updating this document

## 📋 BEFORE CREATING ANY NEW FOLDER
**MANDATORY CHECKLIST:**
1. Does this functionality belong in existing folder?
2. Does this violate MODULE INDEPENDENCE?
3. Would this work for "mango in Bulgaria"?
4. Is this LLM-first or hardcoded patterns?
5. Update PROJECT_STRUCTURE.md if truly needed

## 🎯 CURRENT FOCUS: Database Dashboard
We are currently working on LLM-first database dashboard.
ALL dashboard work goes in existing monitoring structure - NO new folders!

## 📞 EMERGENCY RECOVERY
If someone creates wrong structure:
1. Show this PROJECT_STRUCTURE.md
2. Point to constitutional violations  
3. Move code to correct existing folders
4. Delete unauthorized folders

## 🌐 AWS DEPLOYMENT
- **Platform:** AWS App Runner
- **URLs:** https://6pmgiripe.us-east-1.awsapprunner.com/[dashboard]/
- **Database:** AWS RDS PostgreSQL (farmer-crm-production)
- **Repository:** ava-olo-monitoring-dashboards

## 📁 SISTER REPOSITORIES (DO NOT MODIFY)
Other repositories in the AVA OLO ecosystem:
- ava-olo-agricultural-core
- ava-olo-api-gateway
- ava-olo-llm-router
- ava-olo-database-ops
- ava-olo-document-search
- ava-olo-web-search
- ava-olo-mock-whatsapp
- ava-olo-shared