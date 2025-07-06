# 📜 AVA OLO CONSTITUTIONAL PRINCIPLES

## CORE PHILOSOPHY
These 12 rules are MANDATORY for all development. Every decision must comply with ALL principles.

### 🥭 MANGO RULE: Universal Scalability
- Everything must work for any crop in any country
- "Would this work for mango in Bulgaria?" is the ultimate test
- No hardcoded Croatian/regional patterns allowed
- LLM intelligence handles all language/crop variations

### 🗄️ POSTGRESQL ONLY: Single Database
- Database: farmer_crm on WSL2 PostgreSQL (migrated from Windows)
- Connection: localhost:5432
- NO SQLite, NO multiple databases, NO exceptions
- All modules use same PostgreSQL connection

### 🧠 LLM-FIRST: Maximum AI Intelligence
- Minimal coding + Maximum LLM intelligence
- Let GPT-4 handle complexity, not hardcoded rules
- Trust AI over pattern matching
- Simple prompts > Complex bypass systems

### 🏗️ MODULE INDEPENDENCE: Isolated Components
- Each module must work independently
- Working on RAG cannot break database operations
- Working on UI cannot break LLM routing
- Bulletproof separation prevents cascading failures

### 🔒 PRIVACY-FIRST: Personal Data Protection
- Personal farm data NEVER goes to external APIs
- Farmer information stays internal (database/RAG only)
- External search (Perplexity) only for general knowledge
- Clean separation of personal vs public data

### ⚡ API-FIRST: Standardized Communication
- All modules communicate through standardized APIs
- No direct function imports between modules
- Clean interfaces prevent coupling disasters
- Each module has defined contracts

### 🛡️ ERROR ISOLATION: Graceful Degradation
- One module failure cannot crash the system
- Always provide fallback responses
- System stays operational even with partial failures
- User never sees "system down" messages

### 📊 TRANSPARENCY: Complete Monitoring
- All LLM decisions must be logged and explainable
- Complete audit trail for agricultural operations
- Real-time monitoring of system health
- Every operation tracked in llm_debug_log

### 🌾 FARMER-CENTRIC: Appropriate Communication
- Every response in farmer's preferred language
- Professional agricultural tone (not "overly sweet")
- Contextually appropriate communication
- Respect agricultural expertise

### 🔄 PRODUCTION-READY: Scalable Architecture
- Every component must be scalable from day one
- WhatsApp-ready design
- Multi-farmer, multi-country capable
- No "toy" implementations

### 📝 CONFIGURATION: Settings Over Hardcoding
- Country/language settings via configuration
- No hardcoded regional logic in code
- Easy expansion to new markets
- All parameters in config files

### 🧪 TEST-DRIVEN: Validation Required
- "Prosaro PHI" test must always pass
- Every change validated against core agricultural scenarios
- Performance benchmarks maintained
- Constitutional compliance verified

## CONSTITUTIONAL COMPLIANCE CHECK
Before ANY development work:
1. Read this constitution completely
2. Ensure your approach follows ALL 12 principles
3. Test mango compliance: "Would this work in Bulgaria?"
4. Verify module independence
5. Confirm privacy protection

## VIOLATION CONSEQUENCES
- Constitutional violations delay deployment
- Breaks scalability to international markets
- Creates maintenance burden
- Undermines architectural integrity

REMEMBER: These principles prevent the problems you've experienced and ensure global scalability!