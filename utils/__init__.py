"""
AVA OLO Utilities Package
Security and infrastructure utilities for the AVA OLO platform
"""

# Try to import secrets manager, but don't fail if boto3 not available
try:
    from .secrets_manager import SecretsManager, migrate_env_to_secrets, get_database_config, get_admin_config
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False
    SecretsManager = None
    migrate_env_to_secrets = None
    get_database_config = None
    get_admin_config = None

# Always try to import password security
try:
    from .password_security import PasswordSecurity
except ImportError:
    PasswordSecurity = None

__all__ = [
    'PasswordSecurity',
    'SecretsManager',
    'migrate_env_to_secrets', 
    'get_database_config',
    'get_admin_config',
    'SECRETS_MANAGER_AVAILABLE'
]