# Git Commands for Constitutional Setup

## 1. Add the new constitutional files:

```bash
# Add all new constitutional files
git add monitoring/
git add admin_dashboard.py
git add test_constitutional_compliance.py
git add CONSTITUTIONAL_COMPLIANCE.md
git add migrate_to_constitutional.py

# Add the backup directory (optional - if you want to preserve backups)
git add backup_*/
```

## 2. Commit the constitutional changes:

```bash
git commit -m "Implement constitutional compliance for database dashboard

- Restructured from 880-line monolith to modular architecture
- Implemented LLM-first approach (no hardcoded translations)
- Added support for any language (passes Bulgarian mango test)
- Created clean API interfaces with error isolation
- Separated UI from business logic (module independence)
- Privacy first: no personal data sent to external APIs
- Professional agricultural tone, not overly sweet
- All 10 constitutional tests passing

Key files:
- monitoring/core/llm_query_processor.py - AI handles all languages
- monitoring/interfaces/admin_dashboard_api.py - Clean API
- monitoring/config/dashboard_config.py - Central configuration
- admin_dashboard.py - New entry point

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## 3. Push to GitHub:

```bash
# Push to origin
git push origin main

# Or use your git-push-simple.bat
cd C:\Users\HP\ava-olo-constitutional
git-push-simple.bat
# Then select option 1 for monitoring dashboards
```

## 4. Alternative: Single command approach

If you prefer, here's everything in one go:

```bash
# Add, commit and push
git add monitoring/ admin_dashboard.py test_constitutional_compliance.py CONSTITUTIONAL_COMPLIANCE.md migrate_to_constitutional.py && \
git commit -m "Implement constitutional compliance for database dashboard" && \
git push origin main
```

## 5. After deployment:

1. The new dashboard will be at: `/database/` (same URL)
2. Test with Bulgarian mango query: "Колко манго дървета имам?"
3. Verify all languages work without hardcoding
4. Check error isolation by testing invalid queries

## Notes:

- Old files are backed up in `backup_[timestamp]/` directory
- The system now uses `admin_dashboard.py` as entry point
- All constitutional principles are implemented
- No hardcoded translations - LLM handles everything