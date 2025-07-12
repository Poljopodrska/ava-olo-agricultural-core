# AVA OLO SYSTEM CONFIGURATION

## 📜 MANDATORY FIRST READ
1. Read AVA_OLO_CONSTITUTION.md completely
2. Verify understanding of all 12 constitutional principles
3. Confirm commitment to constitutional compliance

## DATABASE CONFIGURATION (Constitutional Rule: PostgreSQL Only)
- **Host:** farmer-crm-production.xxxxx.us-east-1.rds.amazonaws.com (AWS RDS)
- **Database Name:** farmer_crm 
- **Environment:** AWS RDS PostgreSQL
- **Connection:** Via AWS environment variables (DB_HOST, DB_NAME, etc.)
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

## SERVICE CONFIGURATION
- **Monitoring Hub:** https://6pmgiripe.us-east-1.awsapprunner.com
- **Agricultural Core:** https://3ksdvgdtud.us-east-1.awsapprunner.com
- **Dashboard Endpoints:**
  - Health: https://6pmgiripe.us-east-1.awsapprunner.com/health/
  - Agronomic: https://6pmgiripe.us-east-1.awsapprunner.com/agronomic/
  - Business: https://6pmgiripe.us-east-1.awsapprunner.com/business/
  - Database: https://6pmgiripe.us-east-1.awsapprunner.com/database/

## ENVIRONMENT
- **Platform:** AWS App Runner
- **Database:** AWS RDS PostgreSQL
- **Repository:** ava-olo-monitoring-dashboards
- **Environment Variables:** All configured in AWS (DATABASE_URL, OPENAI_API_KEY, etc.)

## CRITICAL RULES (Constitutional)
1. Database name is farmer_crm, NOT ava_olo
2. AWS RDS, NOT localhost
3. HTTPS URLs, NOT port numbers
4. AWS App Runner, NOT local services
5. ALL development must follow constitutional principles
6. Mango compliance test required for every feature

## LAST VERIFIED
- Date: 2025-07-12
- Farmers Count: 4 (KMETIJA VRZEL - Blaž Vrzel + 3 others)
- Database Status: Active in AWS RDS and WSL2
- AWS Services: 2 App Runner services operational
- Local Services: All dashboards functional
- Constitutional Compliance: Verified