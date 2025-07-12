# AVA OLO PROJECT STRUCTURE

## Git Repository Structure

The AVA OLO Constitutional system consists of multiple Git repositories, each following the constitutional principle of Module Independence:

```
ava-olo-constitutional/
├── ava-olo-shared/                 # Shared documentation and constitution
│   ├── AVA_OLO_CONSTITUTION.md    # Core 12 principles (mandatory reading)
│   ├── SYSTEM_CONFIG.md           # System configuration and AWS URLs
│   ├── STARTUP_CHECKLIST.md       # Development startup guide
│   └── README.md                  # Overview
│
├── ava-olo-agricultural-core/      # Core agricultural logic
│   ├── core/                      # Core modules (LLM router, database ops)
│   ├── interfaces/                # API interfaces
│   └── services/                  # Service implementations
│
├── ava-olo-monitoring-dashboards/  # THIS REPOSITORY - All monitoring tools
│   ├── health_check_dashboard.py  # System health monitor
│   ├── business_dashboard.py      # Business KPIs
│   ├── database_explorer.py       # AI-driven database queries
│   ├── agronomic_approval.py      # Expert approval interface
│   ├── templates/                 # HTML templates for all dashboards
│   └── database_operations.py     # Shared database utilities
│
├── ava-olo-api-gateway/           # API gateway service
├── ava-olo-llm-router/            # LLM routing intelligence
├── ava-olo-database-ops/          # Database operations
├── ava-olo-document-search/       # RAG implementation
├── ava-olo-web-search/            # External search integration
├── ava-olo-mock-whatsapp/         # WhatsApp simulator
├── ava-olo-agronomic-dashboard/   # Legacy - merged into monitoring
└── ava-olo-business-dashboard/    # Legacy - merged into monitoring
```

## AWS Deployment Structure

### Production URLs
- **Monitoring Hub:** https://6pmgiripe.us-east-1.awsapprunner.com
  - `/health/` - System health dashboard
  - `/agronomic/` - Agronomic approval
  - `/business/` - Business KPIs
  - `/database/` - Database explorer
  
- **Agricultural Core:** https://3ksdvgdtud.us-east-1.awsapprunner.com
  - Core API and LLM routing

### Repository Focus: ava-olo-monitoring-dashboards

This repository contains all monitoring and dashboard components:

```
ava-olo-monitoring-dashboards/
├── health_check_dashboard.py      # System health monitoring
├── business_dashboard.py          # Business metrics and KPIs
├── database_explorer.py           # AI-driven database interface
├── agronomic_approval.py          # Expert approval workflow
├── database_operations.py         # Shared database utilities
├── config.py                      # Configuration (AWS/local)
├── templates/
│   ├── health_dashboard.html
│   ├── business_dashboard.html
│   ├── database_explorer.html
│   └── agronomic_dashboard.html
├── monitoring/                    # Additional monitoring tools
└── backup_*/                      # Backup directories

```

## Constitutional Compliance

All modules follow the 12 principles from AVA_OLO_CONSTITUTION.md:

1. **Universal Application** - Works for any crop/country
2. **Module Independence** - Each dashboard operates independently
3. **LLM Intelligence First** - AI-driven decisions, minimal hardcoding
4. **PostgreSQL Only** - farmer-crm-production database
5. **Farmer Privacy** - No personal data exposure
6. **API Communication** - RESTful interfaces between services
7. **Configuration Over Hardcoding** - Environment-based config
8. **Error Resilience** - Graceful error handling
9. **Scalability** - Distributed architecture
10. **Monitoring** - Health dashboard tracks all services
11. **Version Control** - Git-based development
12. **Testing** - Mango compliance verification

## Database Structure

Production database: `farmer-crm-production` (AWS RDS)

Key tables (no ava_ prefix per constitution):
- farmers
- fields
- field_crops
- messages
- tasks
- conversations

## Development Workflow

1. All dashboard development happens in `ava-olo-monitoring-dashboards`
2. Push changes to main branch
3. AWS App Runner automatically deploys
4. Access via https://6pmgiripe.us-east-1.awsapprunner.com/[dashboard]/

## Environment Variables (AWS App Runner)

- DATABASE_URL
- OPENAI_API_KEY
- PERPLEXITY_API_KEY
- PINECONE_API_KEY
- AWS_REGION=us-east-1