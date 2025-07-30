"""WhatsApp Integration Diagnostic Tool for AVA OLO System"""
import aiohttp
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WhatsAppDiagnostic:
    """Diagnose WhatsApp integration issues"""
    
    def __init__(self):
        self.webhook_url = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
        self.phone_number = "+38591857451"
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_accessibility": None,
            "endpoints_check": None,
            "credentials_check": None,
            "twilio_connectivity": None,
            "message_flow_test": None
        }
    
    async def test_webhook_accessibility(self) -> Dict[str, Any]:
        """Test if webhook URL is accessible from internet"""
        results = {
            "url": self.webhook_url,
            "accessible": False,
            "checks": {}
        }
        
        # Test main health endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.webhook_url}/health", timeout=10) as resp:
                    results["checks"]["health"] = {
                        "status_code": resp.status,
                        "accessible": resp.status == 200,
                        "response": await resp.text() if resp.status == 200 else None
                    }
                    results["accessible"] = resp.status == 200
        except Exception as e:
            results["checks"]["health"] = {
                "error": str(e),
                "accessible": False
            }
        
        # Test API v1 health
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.webhook_url}/api/v1/health", timeout=10) as resp:
                    results["checks"]["api_health"] = {
                        "status_code": resp.status,
                        "accessible": resp.status == 200
                    }
        except Exception as e:
            results["checks"]["api_health"] = {
                "error": str(e),
                "accessible": False
            }
        
        self.test_results["webhook_accessibility"] = results
        return results
    
    async def verify_webhook_endpoints(self) -> Dict[str, Any]:
        """Check if WhatsApp webhook endpoints exist"""
        endpoints = [
            '/api/v1/whatsapp/webhook',  # Primary Twilio webhook
            '/api/v1/whatsapp/fallback',  # Fallback webhook
            '/api/v1/whatsapp/status',    # Status callback
            '/api/v1/whatsapp/config',    # Configuration endpoint
            '/api/v1/whatsapp/health',    # WhatsApp health check
            '/webhook',                   # Alternative webhook path
            '/whatsapp/callback'          # Another common path
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    # Test GET (for verification/config endpoints)
                    async with session.get(f"{self.webhook_url}{endpoint}", timeout=5) as resp:
                        get_status = resp.status
                    
                    # Test POST (for webhook endpoints)
                    async with session.post(
                        f"{self.webhook_url}{endpoint}",
                        json={"test": "diagnostic"},
                        timeout=5
                    ) as resp:
                        post_status = resp.status
                    
                    results[endpoint] = {
                        'GET': get_status,
                        'POST': post_status,
                        'exists': get_status != 404 or post_status != 404,
                        'functional': get_status in [200, 201, 405] or post_status in [200, 201, 405]
                    }
            except Exception as e:
                results[endpoint] = {
                    'GET': 'error',
                    'POST': 'error',
                    'exists': False,
                    'error': str(e)
                }
        
        self.test_results["endpoints_check"] = results
        return results
    
    def check_credentials_configured(self) -> Dict[str, bool]:
        """Check if required WhatsApp/Twilio credentials are configured"""
        credentials = {
            # Twilio credentials
            "TWILIO_ACCOUNT_SID": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "TWILIO_AUTH_TOKEN": bool(os.getenv("TWILIO_AUTH_TOKEN")),
            "TWILIO_PHONE_NUMBER": bool(os.getenv("TWILIO_PHONE_NUMBER")),
            "TWILIO_ENABLED": os.getenv("TWILIO_ENABLED", "false").lower() == "true",
            
            # WhatsApp Business API credentials (if using direct API)
            "WHATSAPP_ACCESS_TOKEN": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
            "WHATSAPP_PHONE_NUMBER_ID": bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID")),
            "WHATSAPP_VERIFY_TOKEN": bool(os.getenv("WHATSAPP_VERIFY_TOKEN")),
            "WHATSAPP_BUSINESS_ID": bool(os.getenv("WHATSAPP_BUSINESS_ID")),
            
            # General configuration
            "BASE_URL": bool(os.getenv("BASE_URL")),
            "WEBHOOK_URL": bool(os.getenv("WEBHOOK_URL", os.getenv("BASE_URL")))
        }
        
        self.test_results["credentials_check"] = credentials
        return credentials
    
    async def test_twilio_connectivity(self) -> Dict[str, Any]:
        """Test Twilio API connectivity"""
        result = {
            "twilio_api_accessible": False,
            "account_verified": False,
            "phone_number_verified": False,
            "error": None
        }
        
        if not (os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")):
            result["error"] = "Twilio credentials not configured"
            self.test_results["twilio_connectivity"] = result
            return result
        
        try:
            # Test Twilio API accessibility
            import base64
            auth = base64.b64encode(
                f"{os.getenv('TWILIO_ACCOUNT_SID')}:{os.getenv('TWILIO_AUTH_TOKEN')}".encode()
            ).decode()
            
            headers = {"Authorization": f"Basic {auth}"}
            
            async with aiohttp.ClientSession() as session:
                # Check account
                async with session.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{os.getenv('TWILIO_ACCOUNT_SID')}.json",
                    headers=headers
                ) as resp:
                    result["twilio_api_accessible"] = resp.status == 200
                    result["account_verified"] = resp.status == 200
                    
                    if resp.status != 200:
                        result["error"] = f"Account verification failed: {resp.status}"
        
        except Exception as e:
            result["error"] = f"Twilio connectivity test failed: {str(e)}"
        
        self.test_results["twilio_connectivity"] = result
        return result
    
    async def test_message_flow(self) -> Dict[str, Any]:
        """Test complete message flow"""
        result = {
            "webhook_reachable": False,
            "can_receive_messages": False,
            "can_send_messages": False,
            "cava_integration": False,
            "database_storage": False
        }
        
        # Check webhook reachability
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "MessageSid": "TEST123",
                    "From": "whatsapp:+359885123456",
                    "Body": "Test message from diagnostic tool",
                    "To": f"whatsapp:{self.phone_number}"
                }
                
                async with session.post(
                    f"{self.webhook_url}/api/v1/whatsapp/webhook",
                    data=test_payload,
                    timeout=10
                ) as resp:
                    result["webhook_reachable"] = resp.status in [200, 201]
                    if resp.status in [200, 201]:
                        result["can_receive_messages"] = True
                        response_data = await resp.text()
                        result["webhook_response"] = response_data
        except Exception as e:
            result["error"] = str(e)
        
        self.test_results["message_flow_test"] = result
        return result
    
    def generate_diagnostic_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        report = [
            "# WhatsApp Integration Diagnostic Report",
            f"Generated: {self.test_results['timestamp']}",
            f"WhatsApp Number: {self.phone_number}",
            f"Webhook URL: {self.webhook_url}",
            "",
            "## 1. Webhook Accessibility"
        ]
        
        if self.test_results["webhook_accessibility"]:
            accessibility = self.test_results["webhook_accessibility"]
            report.append(f"- Main URL Accessible: {'✅' if accessibility['accessible'] else '❌'}")
            for check, details in accessibility.get("checks", {}).items():
                status = '✅' if details.get('accessible', False) else '❌'
                report.append(f"  - {check}: {status}")
                if 'error' in details:
                    report.append(f"    Error: {details['error']}")
        
        report.extend(["", "## 2. WhatsApp Endpoints"])
        if self.test_results["endpoints_check"]:
            for endpoint, details in self.test_results["endpoints_check"].items():
                exists = '✅' if details.get('exists', False) else '❌'
                functional = '✅' if details.get('functional', False) else '⚠️'
                report.append(f"- {endpoint}: {exists} Exists, {functional} Functional")
                if 'error' in details:
                    report.append(f"  Error: {details['error']}")
        
        report.extend(["", "## 3. Credentials Configuration"])
        if self.test_results["credentials_check"]:
            for cred, configured in self.test_results["credentials_check"].items():
                status = '✅' if configured else '❌'
                report.append(f"- {cred}: {status}")
        
        report.extend(["", "## 4. Twilio Connectivity"])
        if self.test_results["twilio_connectivity"]:
            twilio = self.test_results["twilio_connectivity"]
            report.append(f"- API Accessible: {'✅' if twilio['twilio_api_accessible'] else '❌'}")
            report.append(f"- Account Verified: {'✅' if twilio['account_verified'] else '❌'}")
            if twilio.get('error'):
                report.append(f"- Error: {twilio['error']}")
        
        report.extend(["", "## 5. Message Flow Test"])
        if self.test_results["message_flow_test"]:
            flow = self.test_results["message_flow_test"]
            report.append(f"- Webhook Reachable: {'✅' if flow['webhook_reachable'] else '❌'}")
            report.append(f"- Can Receive Messages: {'✅' if flow['can_receive_messages'] else '❌'}")
            if flow.get('error'):
                report.append(f"- Error: {flow['error']}")
        
        report.extend(["", "## Recommendations"])
        
        # Generate recommendations based on findings
        if not self.test_results["webhook_accessibility"]["accessible"]:
            report.append("1. ❗ Webhook URL is not accessible. Check:")
            report.append("   - ECS service is running")
            report.append("   - ALB is healthy and routing correctly")
            report.append("   - Security groups allow inbound traffic")
        
        missing_endpoints = [
            ep for ep, details in self.test_results["endpoints_check"].items()
            if not details.get('exists', False)
        ]
        if missing_endpoints:
            report.append(f"2. ❗ Missing endpoints: {', '.join(missing_endpoints)}")
            report.append("   - Deploy the latest code with WhatsApp webhook handlers")
        
        missing_creds = [
            cred for cred, configured in self.test_results["credentials_check"].items()
            if not configured and cred.startswith(('TWILIO_', 'WHATSAPP_'))
        ]
        if missing_creds:
            report.append(f"3. ❗ Missing credentials: {', '.join(missing_creds)}")
            report.append("   - Configure in ECS task definition environment variables")
        
        return "\n".join(report)
    
    async def run_full_diagnostic(self) -> str:
        """Run complete diagnostic suite"""
        logger.info("Starting WhatsApp integration diagnostics...")
        
        # Run all tests
        await self.test_webhook_accessibility()
        await self.verify_webhook_endpoints()
        self.check_credentials_configured()
        await self.test_twilio_connectivity()
        await self.test_message_flow()
        
        # Generate and return report
        report = self.generate_diagnostic_report()
        logger.info("Diagnostic complete")
        return report


# CLI interface for running diagnostics
async def main():
    """Run WhatsApp diagnostics from command line"""
    diagnostic = WhatsAppDiagnostic()
    report = await diagnostic.run_full_diagnostic()
    print(report)
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"whatsapp_diagnostic_report_{timestamp}.md"
    with open(filename, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())