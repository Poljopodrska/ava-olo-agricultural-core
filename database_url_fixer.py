#!/usr/bin/env python3
"""
Database URL Fixer - Bulletproof PostgreSQL URL parsing
Fixes common database URL format issues that cause connection errors
"""

import os
import re
import logging
from urllib.parse import urlparse, urlunparse
from typing import Optional

logger = logging.getLogger(__name__)

def fix_database_url() -> str:
    """
    Fix PostgreSQL URL for any format issues
    
    Returns:
        Fixed database URL
    """
    original_url = os.environ.get("DATABASE_URL", "")
    
    if not original_url:
        logger.warning("⚠️ DATABASE_URL not set in environment")
        return ""
    
    logger.info(f"🔍 Original DATABASE_URL: {original_url[:50]}...")
    
    try:
        # Handle brackets in password (common AWS RDS issue)
        if "[" in original_url and "]" in original_url:
            # Check if brackets are in password, not hostname
            if "://" in original_url and "@" in original_url:
                # Extract parts: scheme://user:pass@host:port/db
                scheme_part = original_url.split("://")[0]
                rest = original_url.split("://")[1]
                
                if "@" in rest:
                    credentials_part = rest.split("@")[0]
                    host_part = rest.split("@")[1]
                    
                    # If brackets are in credentials (password), URL-encode them
                    if "[" in credentials_part and "]" in credentials_part:
                        # URL-encode brackets in password
                        fixed_credentials = credentials_part.replace("[", "%5B").replace("]", "%5D")
                        fixed_url = f"{scheme_part}://{fixed_credentials}@{host_part}"
                        
                        os.environ["DATABASE_URL"] = fixed_url
                        logger.info(f"✅ Fixed brackets in password: {fixed_url[:50]}...")
                        return fixed_url
        
        # Parse the URL to identify components
        parsed = urlparse(original_url)
        
        # Handle IPv6 bracket issues in hostname
        if parsed.hostname and "[" in parsed.hostname and "]" in parsed.hostname:
            # Extract IPv6 address from brackets
            ipv6_match = re.search(r'\[([^\]]+)\]', parsed.hostname)
            if ipv6_match:
                ipv6_addr = ipv6_match.group(1)
                # Replace bracketed IPv6 with plain IPv6
                fixed_hostname = ipv6_addr
                logger.info(f"🔧 Fixed IPv6 hostname: {parsed.hostname} -> {fixed_hostname}")
                
                # Reconstruct URL with fixed hostname
                fixed_url = urlunparse((
                    parsed.scheme,
                    f"{parsed.username}:{parsed.password}@{fixed_hostname}:{parsed.port}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                
                os.environ["DATABASE_URL"] = fixed_url
                logger.info(f"✅ Fixed IPv6 URL: {fixed_url[:50]}...")
                return fixed_url
        
        # Handle postgres:// vs postgresql:// scheme
        if parsed.scheme == "postgres":
            fixed_url = original_url.replace("postgres://", "postgresql://")
            os.environ["DATABASE_URL"] = fixed_url
            logger.info(f"✅ Fixed scheme: postgres:// -> postgresql://")
            logger.info(f"✅ Fixed URL: {fixed_url[:50]}...")
            return fixed_url
        
        # Handle AWS RDS endpoint format issues
        if "amazonaws.com" in parsed.hostname and "]:5432" in original_url:
            # Common AWS RDS IPv6 format issue
            fixed_url = re.sub(r'\[([^\]]+)\]:(\d+)', r'\1:\2', original_url)
            os.environ["DATABASE_URL"] = fixed_url
            logger.info(f"✅ Fixed AWS RDS IPv6 format: {fixed_url[:50]}...")
            return fixed_url
        
        # Handle port specification issues
        if parsed.port is None and ":5432" not in original_url:
            # Add default PostgreSQL port
            if "@" in original_url and "/" in original_url:
                # Insert port before database name
                fixed_url = original_url.replace(f"@{parsed.hostname}/", f"@{parsed.hostname}:5432/")
                os.environ["DATABASE_URL"] = fixed_url
                logger.info(f"✅ Added default port: {fixed_url[:50]}...")
                return fixed_url
        
        # URL seems fine, return original
        logger.info(f"✅ Database URL appears valid: {original_url[:50]}...")
        return original_url
        
    except Exception as e:
        logger.error(f"❌ Failed to parse DATABASE_URL: {e}")
        logger.error(f"❌ Original URL: {original_url}")
        return original_url

def get_database_components() -> dict:
    """
    Extract database connection components from URL
    
    Returns:
        Dictionary with database connection components
    """
    database_url = os.environ.get("DATABASE_URL", "")
    
    if not database_url:
        return {}
    
    try:
        parsed = urlparse(database_url)
        
        # Handle IPv6 brackets in hostname
        hostname = parsed.hostname
        if hostname and "[" in hostname and "]" in hostname:
            ipv6_match = re.search(r'\[([^\]]+)\]', hostname)
            if ipv6_match:
                hostname = ipv6_match.group(1)
        
        # Handle URL-encoded brackets in password
        password = parsed.password
        if password:
            password = password.replace("%5B", "[").replace("%5D", "]")
        
        components = {
            "scheme": parsed.scheme,
            "username": parsed.username,
            "password": password,
            "hostname": hostname,
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip('/') if parsed.path else 'postgres'
        }
        
        logger.info(f"🔍 Database components extracted successfully")
        # Don't log password for security
        safe_components = {k: v for k, v in components.items() if k != "password"}
        safe_components["password"] = "[REDACTED]" if password else None
        logger.info(f"🔍 Safe components: {safe_components}")
        return components
        
    except Exception as e:
        logger.error(f"❌ Failed to parse database components: {e}")
        return {}

def test_database_url_parsing():
    """Test database URL parsing with various formats"""
    
    test_urls = [
        # Standard format
        "postgresql://user:pass@host:5432/db",
        # IPv6 with brackets
        "postgresql://user:pass@[::1]:5432/db",
        # AWS RDS format
        "postgresql://user:pass@[host.amazonaws.com]:5432/db",
        # Missing port
        "postgresql://user:pass@host/db",
        # Wrong scheme
        "postgres://user:pass@host:5432/db"
    ]
    
    for test_url in test_urls:
        print(f"\n🧪 Testing: {test_url}")
        os.environ["DATABASE_URL"] = test_url
        
        fixed_url = fix_database_url()
        components = get_database_components()
        
        print(f"✅ Fixed: {fixed_url}")
        print(f"📋 Components: {components}")

if __name__ == "__main__":
    # Run tests
    test_database_url_parsing()