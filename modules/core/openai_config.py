#!/usr/bin/env python3
"""
OpenAI Configuration Helper - Robust OpenAI API key management
Handles multiple environment variable sources and proper initialization
"""
import os
from typing import Optional
from openai import OpenAI


class OpenAIConfig:
    """Centralized OpenAI configuration and client management"""
    
    _initialized = False
    _api_key = None
    _client = None
    
    @classmethod
    def initialize(cls, force: bool = False) -> bool:
        """Initialize OpenAI with proper error handling"""
        if cls._initialized and not force:
            return True
        
        print("🔄 Initializing OpenAI configuration...")
        
        # Try multiple sources for API key
        api_key = (
            os.getenv("OPENAI_API_KEY") or
            os.getenv("OPENAI_KEY") or
            os.getenv("openai_api_key")
        )
        
        if not api_key:
            print("❌ OpenAI API key not found in environment variables")
            print("📋 Checked: OPENAI_API_KEY, OPENAI_KEY, openai_api_key")
            return False
        
        if not api_key.startswith("sk-"):
            print("⚠️ OpenAI API key format may be invalid (should start with 'sk-')")
            print(f"📋 Current format: {api_key[:10]}...")
            
        try:
            # Create OpenAI client with the key
            cls._client = OpenAI(api_key=api_key)
            cls._api_key = api_key
            cls._initialized = True
            
            print("✅ OpenAI initialized successfully")
            print(f"🔑 API key prefix: {api_key[:10]}...")
            
            # Test the connection with a minimal request
            try:
                models = cls._client.models.list()
                print(f"✅ OpenAI connection verified - {len(models.data)} models available")
            except Exception as test_error:
                print(f"⚠️ OpenAI key valid but connection test failed: {str(test_error)}")
                # Still consider it initialized if the client was created
            
            return True
            
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {str(e)}")
            cls._client = None
            cls._api_key = None
            cls._initialized = False
            return False
    
    @classmethod
    def get_client(cls) -> Optional[OpenAI]:
        """Get initialized OpenAI client"""
        if not cls._initialized:
            if not cls.initialize():
                return None
        
        return cls._client
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if OpenAI is properly configured"""
        return cls._initialized and cls._client is not None
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Get the configured API key"""
        if not cls._initialized:
            cls.initialize()
        return cls._api_key
    
    @classmethod
    def get_status(cls) -> dict:
        """Get detailed status for debugging"""
        status = {
            "initialized": cls._initialized,
            "client_available": cls._client is not None,
            "api_key_present": cls._api_key is not None,
            "api_key_format_valid": False,
            "env_vars_checked": ["OPENAI_API_KEY", "OPENAI_KEY", "openai_api_key"]
        }
        
        if cls._api_key:
            status["api_key_format_valid"] = cls._api_key.startswith("sk-")
            status["api_key_length"] = len(cls._api_key)
            status["api_key_preview"] = cls._api_key[:10] + "..." if len(cls._api_key) > 10 else "SHORT"
        
        # Check what's actually in environment
        env_status = {}
        for var in status["env_vars_checked"]:
            value = os.getenv(var)
            env_status[var] = {
                "present": bool(value),
                "length": len(value) if value else 0,
                "preview": value[:7] + "..." if value and len(value) > 7 else value or "NOT_SET"
            }
        
        status["environment_variables"] = env_status
        
        return status
    
    @classmethod
    def reset(cls):
        """Reset configuration - useful for testing"""
        cls._initialized = False
        cls._api_key = None
        cls._client = None
        print("🔄 OpenAI configuration reset")


# Convenience function for backward compatibility
def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client - backward compatible function"""
    return OpenAIConfig.get_client()


# Auto-initialize on import if API key is available
if os.getenv("OPENAI_API_KEY"):
    OpenAIConfig.initialize()