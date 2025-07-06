# AVA OLO SYSTEM CONFIGURATION

## 📜 MANDATORY FIRST READ
1. Read AVA_OLO_CONSTITUTION.md completely
2. Verify understanding of all 12 constitutional principles
3. Confirm commitment to constitutional compliance

## DATABASE CONFIGURATION (Constitutional Rule: PostgreSQL Only)
- **Host:** WSL2 PostgreSQL (migrated from Windows)
- **Connection:** localhost:5432  
- **Database Name:** farmer_crm (NOT ava_olo)
- **Username:** postgres
- **Password:** password [stored in .env]
- **Current Farmers:** 4 real farmers (including KMETIJA VRZEL - Blaž Vrzel)
- **Tables:** 34 tables (farmers, fields, field_crops, tasks, etc.)
- **Messages:** 73 conversation messages preserved
- **Fields:** 53 fields with 46 field crops

## TABLE MAPPING (Constitutional Rule: Configuration Over Hardcoding)
- farmers (NOT ava_farmers)
- fields (NOT ava_fields)
- field_crops (NOT ava_field_crops)  
- incoming_messages (NOT ava_conversations)
- tasks (NOT farm_tasks)

## MODULAR ARCHITECTURE (Constitutional Rule: Module Independence)
```
core/
├── llm_router.py           # Pure routing intelligence
├── database_operations.py  # Farmer data operations
├── knowledge_search.py     # Agricultural knowledge (RAG)
├── external_search.py      # Perplexity integration
└── language_processor.py   # Mango-compliant normalization

interfaces/
├── api_gateway_simple.py   # Standardized API layer (currently running)
├── api_gateway.py          # Full API layer (with external dependencies)
└── web_ui_connector.py     # UI bridge

monitoring/
├── agronomic_dashboard.py  # Expert monitoring
└── business_dashboard.py   # Analytics
```

## SERVER CONFIGURATION
- **API Gateway:** http://localhost:8000 (api_gateway_simple.py)
- **Mock WhatsApp:** http://localhost:8006 (services/whatsapp_mock.py)
- **Agronomic Dashboard:** http://localhost:8007 (services/agronomic_approval.py)
- **Environment:** WSL2 Ubuntu
- **Database:** WSL2 PostgreSQL (localhost:5432)
- **Database Password:** password
- **Constitutional Compliance:** All modules follow 12 principles

## CRITICAL RULES (Constitutional)
1. Database name is farmer_crm, NOT ava_olo
2. Tables use simple names, NOT ava_ prefix
3. PostgreSQL in WSL2, all services localhost
4. Never create new databases - use existing farmer_crm
5. ALL development must follow constitutional principles
6. Mango compliance test required for every feature

## LAST VERIFIED
- Date: 2025-07-06
- Farmers Count: 4 (KMETIJA VRZEL - Blaž Vrzel + 3 others)
- Database Status: Active in WSL2
- Services: All operational
- Constitutional Compliance: Verified