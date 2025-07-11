"""
CONSTITUTIONAL COMPLIANCE: CONFIGURATION over hardcoding
All dashboard configuration in one place
"""

DASHBOARD_CONFIG = {
    "database": {
        "name": "farmer_crm",  # Constitutional: PostgreSQL only
        "connection": "aws_rds",
        "max_connections": 20,
        "connection_timeout": 30
    },
    "llm": {
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.1,
        "timeout": 30,
        "retry_attempts": 3
    },
    "features": {
        "natural_language_query": True,
        "data_modification": True,
        "export_functionality": True,
        "multi_language_support": True,  # LLM handles ALL languages
        "agricultural_context": True
    },
    "compliance": {
        "privacy_first": True,      # No personal data to external APIs
        "mango_rule": True,         # Works for any crop/country
        "error_isolation": True,    # Never crash system
        "module_independence": True, # UI/backend separation
        "api_first": True,          # Clean interfaces
        "llm_first": True,          # AI handles complexity
        "farmer_centric": True,     # Agricultural focus
        "professional_tone": True   # Not overly sweet
    },
    "ui": {
        "items_per_page": 50,
        "max_export_rows": 10000,
        "session_timeout": 3600,  # 1 hour
        "theme": "professional"
    },
    "security": {
        "sanitize_inputs": True,
        "sql_injection_protection": True,
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 60
        }
    },
    "supported_operations": [
        "natural_query",      # Natural language SELECT
        "modify_data",        # Natural language INSERT/UPDATE/DELETE
        "export_data",        # Export to CSV/JSON
        "table_browse",       # Direct table viewing
        "schema_inspect"      # View database structure
    ],
    "error_handling": {
        "show_technical_details": False,  # Only in debug mode
        "fallback_messages": True,
        "graceful_degradation": True,
        "log_errors": True
    },
    "performance": {
        "query_timeout": 30,
        "max_result_rows": 10000,
        "enable_caching": True,
        "cache_ttl": 300  # 5 minutes
    }
}

# API Endpoints configuration
API_ENDPOINTS = {
    "base_url": "/api",
    "version": "v2",
    "routes": {
        "natural_query": "/natural-query",
        "modify_data": "/modify-data",
        "list_tables": "/tables",
        "table_data": "/table/{table_name}",
        "health": "/health",
        "export": "/export/{format}"
    }
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["console", "file"],
    "file_path": "logs/dashboard.log",
    "max_file_size": "10MB",
    "backup_count": 5
}

# Export formats configuration
EXPORT_FORMATS = {
    "csv": {
        "mime_type": "text/csv",
        "extension": ".csv",
        "delimiter": ","
    },
    "json": {
        "mime_type": "application/json",
        "extension": ".json",
        "indent": 2
    },
    "excel": {
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "extension": ".xlsx"
    }
}

# Constitutional validation
def validate_configuration():
    """Ensure configuration meets constitutional requirements"""
    assert DASHBOARD_CONFIG["compliance"]["mango_rule"], "Must support any crop/country"
    assert DASHBOARD_CONFIG["compliance"]["privacy_first"], "Must protect farmer privacy"
    assert DASHBOARD_CONFIG["compliance"]["error_isolation"], "Must handle errors gracefully"
    assert DASHBOARD_CONFIG["database"]["name"] == "farmer_crm", "Must use PostgreSQL farmer_crm"
    assert DASHBOARD_CONFIG["compliance"]["llm_first"], "Must use LLM for complexity"
    return True

# Run validation on import
validate_configuration()