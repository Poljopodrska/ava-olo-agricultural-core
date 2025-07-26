#!/usr/bin/env python3
"""
OpenAI Key Manager - Secure AWS SSM Integration
Retrieves OpenAI API key from AWS Systems Manager Parameter Store
"""
import boto3
import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIKeyManager:
    """Manages OpenAI API key retrieval from AWS SSM"""
    
    def __init__(self):
        self.ssm_parameter_name = "/ava-olo/openai-api-key"
        self.region = "us-east-1"
        self._cached_key = None
        
    def get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or AWS SSM"""
        
        # Try environment variable first (for local development)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info("Using OpenAI key from environment variable")
            return api_key
        
        # Try cached key
        if self._cached_key:
            logger.info("Using cached OpenAI key from SSM")
            return self._cached_key
        
        # Get from AWS SSM Parameter Store
        try:
            logger.info("Retrieving OpenAI key from AWS SSM Parameter Store...")
            ssm = boto3.client('ssm', region_name=self.region)
            
            response = ssm.get_parameter(
                Name=self.ssm_parameter_name,
                WithDecryption=True
            )
            
            api_key = response['Parameter']['Value']
            self._cached_key = api_key  # Cache for subsequent requests
            
            logger.info(f"Successfully retrieved OpenAI key from SSM: {api_key[:10]}...")
            return api_key
            
        except Exception as e:
            logger.error(f"Failed to get OpenAI key from SSM: {e}")
            return None
    
    def get_openai_client(self) -> Optional[OpenAI]:
        """Get configured OpenAI client"""
        api_key = self.get_api_key()
        
        if not api_key:
            logger.error("No OpenAI API key available")
            return None
        
        try:
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return None
    
    def test_connection(self) -> dict:
        """Test OpenAI connection"""
        client = self.get_openai_client()
        
        if not client:
            return {
                "success": False,
                "error": "Could not create OpenAI client",
                "source": "None"
            }
        
        try:
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Say 'Connection test successful'"}],
                max_tokens=10
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model": "gpt-4",
                "source": "env" if os.getenv("OPENAI_API_KEY") else "ssm"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": "env" if os.getenv("OPENAI_API_KEY") else "ssm"
            }

# Global instance
key_manager = OpenAIKeyManager()

def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client using secure key management"""
    return key_manager.get_openai_client()

def get_openai_key() -> Optional[str]:
    """Get OpenAI API key using secure key management"""
    return key_manager.get_api_key()