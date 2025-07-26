"""
OpenAI Key Detective - Find the OpenAI key by any means necessary
"""
import os
import json
from typing import Dict, Optional, List

class OpenAIKeyDetective:
    """Find the OpenAI key by any means necessary"""
    
    @staticmethod
    def investigate() -> Dict:
        """Comprehensive OpenAI key investigation"""
        report = {
            "key_found": False,
            "key_value": None,
            "search_locations": [],
            "environment_variables": {},
            "recommendations": [],
            "manual_fix_instructions": []
        }
        
        # Method 1: Standard environment variables
        env_vars_to_check = [
            "OPENAI_API_KEY",
            "OPENAI_KEY", 
            "openai_api_key",
            "OPENAI_API_TOKEN",
            "OPENAIKEY"
        ]
        
        for var in env_vars_to_check:
            value = os.getenv(var)
            report["search_locations"].append(f"Environment: {var}")
            if value:
                report["key_found"] = True
                report["key_value"] = value[:8] + "..." if len(value) > 8 else value
                report["environment_variables"][var] = "FOUND"
                break
            else:
                report["environment_variables"][var] = "NOT_SET"
        
        # Method 2: Check ALL environment variables
        all_env = os.environ
        for key, value in all_env.items():
            if "openai" in key.lower() or "api" in key.lower() and "key" in key.lower():
                report["search_locations"].append(f"Found related: {key}")
                if value.startswith("sk-"):
                    report["key_found"] = True
                    report["key_value"] = value[:8] + "..."
                    report["environment_variables"][key] = "FOUND (non-standard name)"
        
        # Method 3: Check common config files
        config_files = [
            "/app/.env",
            "/app/.env.production",
            "/app/config.json",
            ".env",
            ".env.production"
        ]
        
        for config_file in config_files:
            report["search_locations"].append(f"File: {config_file}")
            try:
                if config_file.endswith('.json'):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        if 'OPENAI_API_KEY' in config:
                            report["key_found"] = True
                            report["key_value"] = "Found in " + config_file
                else:
                    with open(config_file, 'r') as f:
                        for line in f:
                            if 'OPENAI_API_KEY' in line and '=' in line:
                                report["key_found"] = True
                                report["key_value"] = "Found in " + config_file
            except:
                pass
        
        # Generate recommendations
        if not report["key_found"]:
            report["recommendations"] = [
                "The OpenAI API key is not accessible to the application",
                "ECS task definition environment variables may not be properly configured",
                "The application may need to be restarted after adding the key"
            ]
            
            report["manual_fix_instructions"] = [
                "1. Go to AWS ECS Console",
                "2. Navigate to Task Definitions",
                "3. Find 'ava-agricultural-task'",
                "4. Create new revision",
                "5. In 'Environment variables' section, add:",
                "   - Key: OPENAI_API_KEY",
                "   - Value: Your OpenAI API key (starts with sk-)",
                "6. Update the service to use the new task definition revision",
                "7. Wait for service to restart (2-3 minutes)",
                "8. Test again"
            ]
        
        return report

    @staticmethod
    def attempt_recovery(api_key: Optional[str] = None) -> bool:
        """Try to set OpenAI key if found or provided"""
        import openai
        
        if api_key and api_key.startswith("sk-"):
            try:
                openai.api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key
                return True
            except:
                return False
        
        # Try to find and set
        report = OpenAIKeyDetective.investigate()
        if report["key_found"] and report["key_value"]:
            # Try to extract actual key
            for var in ["OPENAI_API_KEY", "OPENAI_KEY", "openai_api_key"]:
                value = os.getenv(var)
                if value and value.startswith("sk-"):
                    try:
                        openai.api_key = value
                        os.environ["OPENAI_API_KEY"] = value
                        return True
                    except:
                        pass
        
        return False