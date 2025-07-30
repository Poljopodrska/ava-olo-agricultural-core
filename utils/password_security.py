#!/usr/bin/env python3
"""
Password Security Utilities
Secure password hashing and verification for AVA OLO platform
"""

import os
import secrets
import hashlib
import bcrypt
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class PasswordSecurity:
    """Secure password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str, use_bcrypt: bool = True) -> str:
        """
        Hash password using bcrypt (recommended) or SHA256 with salt
        
        Args:
            password: Plain text password
            use_bcrypt: Use bcrypt (True) or SHA256 with salt (False)
            
        Returns:
            Hashed password string
        """
        if use_bcrypt:
            # Use bcrypt (recommended for new passwords)
            salt = bcrypt.gensalt(rounds=12)  # 12 rounds for good security/performance balance
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return f"bcrypt:{hashed.decode('utf-8')}"
        else:
            # Fallback: SHA256 with salt (for compatibility)
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return f"sha256:{salt}:{pwd_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            if stored_hash.startswith('bcrypt:'):
                # bcrypt verification
                hash_part = stored_hash[7:]  # Remove 'bcrypt:' prefix
                return bcrypt.checkpw(password.encode('utf-8'), hash_part.encode('utf-8'))
            
            elif stored_hash.startswith('sha256:'):
                # SHA256 with salt verification
                parts = stored_hash.split(':')
                if len(parts) != 3:
                    return False
                _, salt, pwd_hash = parts
                computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return computed_hash == pwd_hash
            
            elif ':' in stored_hash:
                # Legacy format: salt:hash
                salt, pwd_hash = stored_hash.split(':', 1)
                computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return computed_hash == pwd_hash
            
            else:
                # Plain text comparison (development only)
                logger.warning("⚠️ Using plain text password comparison - NOT SECURE!")
                return password == stored_hash
                
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password
        
        Args:
            length: Password length (minimum 12)
            
        Returns:
            Secure random password
        """
        if length < 12:
            length = 12
            
        # Use a mix of uppercase, lowercase, digits, and special characters
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, list]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'admin', 'password123', 'admin123',
            'qwerty', 'letmein', 'welcome', 'monkey', 'dragon'
        ]
        
        if password.lower() in weak_passwords:
            issues.append("Password is too common and easily guessable")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def upgrade_password_hash(password: str, old_hash: str) -> Optional[str]:
        """
        Upgrade old password hash to bcrypt if needed
        
        Args:
            password: Plain text password
            old_hash: Current hash
            
        Returns:
            New bcrypt hash if upgrade needed, None if already secure
        """
        if old_hash.startswith('bcrypt:'):
            return None  # Already using bcrypt
        
        # Verify with old method first
        if PasswordSecurity.verify_password(password, old_hash):
            # Create new bcrypt hash
            return PasswordSecurity.hash_password(password, use_bcrypt=True)
        
        return None

def test_password_security():
    """Test password security functions"""
    print("🔐 Testing Password Security...")
    
    # Test password generation
    secure_password = PasswordSecurity.generate_secure_password(16)
    print(f"✅ Generated secure password: {secure_password[:4]}***")
    
    # Test password validation
    is_valid, issues = PasswordSecurity.validate_password_strength("weakpass")
    print(f"❌ Weak password validation: {'Valid' if is_valid else 'Invalid'}")
    if issues:
        for issue in issues:
            print(f"   - {issue}")
    
    is_valid, issues = PasswordSecurity.validate_password_strength("StrongPass123!")
    print(f"✅ Strong password validation: {'Valid' if is_valid else 'Invalid'}")
    
    # Test hashing and verification
    test_password = "TestPassword123!"
    
    # Test bcrypt
    bcrypt_hash = PasswordSecurity.hash_password(test_password, use_bcrypt=True)
    bcrypt_verify = PasswordSecurity.verify_password(test_password, bcrypt_hash)
    print(f"✅ bcrypt hash/verify: {bcrypt_verify}")
    
    # Test SHA256
    sha256_hash = PasswordSecurity.hash_password(test_password, use_bcrypt=False)
    sha256_verify = PasswordSecurity.verify_password(test_password, sha256_hash)
    print(f"✅ SHA256 hash/verify: {sha256_verify}")
    
    # Test wrong password
    wrong_verify = PasswordSecurity.verify_password("WrongPassword", bcrypt_hash)
    print(f"✅ Wrong password rejection: {not wrong_verify}")
    
    print("🔐 Password security tests completed!")

def create_admin_hash():
    """Create a secure admin password hash"""
    print("🔐 Creating Admin Password Hash...")
    
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not admin_password or admin_password in ['admin123', 'password', 'CHANGE_THIS_PASSWORD']:
        print("⚠️ No secure admin password found in environment variables")
        admin_password = input("Enter secure admin password: ")
    
    # Validate password strength
    is_valid, issues = PasswordSecurity.validate_password_strength(admin_password)
    if not is_valid:
        print("❌ Password is not strong enough:")
        for issue in issues:
            print(f"   - {issue}")
        return None
    
    # Create hash
    password_hash = PasswordSecurity.hash_password(admin_password, use_bcrypt=True)
    print(f"✅ Admin password hash created: {password_hash[:20]}...")
    print(f"💡 Set this in your environment: ADMIN_PASSWORD_HASH={password_hash}")
    
    return password_hash

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_password_security()
    elif len(sys.argv) > 1 and sys.argv[1] == "hash":
        create_admin_hash()
    else:
        print("Usage:")
        print("  python password_security.py test   - Run tests")
        print("  python password_security.py hash   - Create admin hash")