# BEFORE STARTING ANY DEVELOPMENT

## CONSTITUTIONAL COMPLIANCE (MANDATORY)
1. 📜 Read AVA_OLO_CONSTITUTION.md completely
2. 🥭 Ask: "Would my approach work for mango in Bulgaria?"
3. 🗄️ Verify: Using farmer_crm PostgreSQL database only
4. 🧠 Confirm: Using LLM intelligence, not hardcoded patterns
5. 🏗️ Check: My changes won't break other modules

## SYSTEM VERIFICATION
1. Read SYSTEM_CONFIG.md completely
2. Verify AWS environment variables configured in App Runner
3. Test database connection via AWS RDS
4. Expected result: 4 farmers in farmer_crm database

## TABLE VERIFICATION
```sql
-- Must return 34 tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Must show: farmers, fields, field_crops, tasks, etc.
\dt
```

## CONSTITUTIONAL CHECKPOINT
Before proceeding, confirm:
- ✅ Privacy: No personal data to external APIs
- ✅ API-First: Using standardized interfaces
- ✅ Error Isolation: Failures won't cascade
- ✅ Transparency: All operations logged
- ✅ Farmer-Centric: Appropriate language/tone
- ✅ Production-Ready: Scalable implementation
- ✅ Configuration: No hardcoded values
- ✅ Test-Ready: Validation planned

## SERVICE VERIFICATION
Verify all AWS services running:
- https://6pmgiripe.us-east-1.awsapprunner.com (Monitoring Hub)
- https://3ksdvgdtud.us-east-1.awsapprunner.com (Agricultural Core)
- https://6pmgiripe.us-east-1.awsapprunner.com/database/ (Database Dashboard)

## IF CONSTITUTIONAL VIOLATION DETECTED
1. STOP development immediately
2. Review constitutional principles
3. Redesign approach for compliance
4. Test mango compliance
5. Verify module independence

## NEVER ASSUME
- Database location
- Table names
- Connection parameters
- Environmental setup
- Constitutional compliance

## CONSTITUTIONAL CHECKPOINT
Before proceeding, verify AWS deployment compatibility:
- ✅ Database: AWS RDS connection confirmed
- ✅ Services: AWS App Runner URLs working
- ✅ Environment: AWS environment variables configured