#!/usr/bin/env python3
"""
Main Security Scanner Orchestrator
Coordinates all security checks and generates comprehensive report
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_checker import AuthenticationChecker
from data_checker import DataProtectionChecker
from code_scanner import CodeSecurityScanner
from infra_checker import InfrastructureChecker
from report_generator import SecurityReportGenerator


class SecurityScanner:
    """Main security audit orchestrator"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/mnt/c/Users/HP/ava_olo_project"
        self.auth_checker = AuthenticationChecker(self.project_root)
        self.data_checker = DataProtectionChecker(self.project_root)
        self.code_scanner = CodeSecurityScanner(self.project_root)
        self.infra_checker = InfrastructureChecker()
        self.report_generator = SecurityReportGenerator()
        
        # Severity levels
        self.CRITICAL = "CRITICAL"
        self.HIGH = "HIGH"
        self.MEDIUM = "MEDIUM"
        self.LOW = "LOW"
        
    def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        print("🔍 Starting AVA OLO Security Audit...")
        
        results = {
            "audit_date": datetime.now().isoformat(),
            "services": ["agricultural-core", "monitoring-dashboards"],
            "findings": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            },
            "summary": {},
            "recommendations": []
        }
        
        # 1. Authentication Audit
        print("\n📋 Checking Authentication...")
        auth_results = self.auth_checker.check_all()
        self._categorize_findings(auth_results, results["findings"])
        
        # 2. Data Protection Audit
        print("\n🔐 Checking Data Protection...")
        data_results = self.data_checker.check_all()
        self._categorize_findings(data_results, results["findings"])
        
        # 3. Code Security Scan
        print("\n💻 Scanning Code Security...")
        code_results = self.code_scanner.scan_all()
        self._categorize_findings(code_results, results["findings"])
        
        # 4. Infrastructure Security
        print("\n☁️ Checking Infrastructure...")
        infra_results = self.infra_checker.check_all()
        self._categorize_findings(infra_results, results["findings"])
        
        # 5. Generate Summary
        results["summary"] = self._generate_summary(results["findings"])
        
        # 6. Generate Recommendations
        results["recommendations"] = self._generate_recommendations(results["findings"])
        
        return results
    
    def _categorize_findings(self, findings: List[Dict], results_dict: Dict):
        """Categorize findings by severity"""
        for finding in findings:
            severity = finding.get("severity", self.MEDIUM).lower()
            if severity in results_dict:
                results_dict[severity].append(finding)
    
    def _generate_summary(self, findings: Dict) -> Dict:
        """Generate audit summary"""
        return {
            "total_issues": sum(len(findings[sev]) for sev in findings),
            "critical_count": len(findings["critical"]),
            "high_count": len(findings["high"]),
            "medium_count": len(findings["medium"]),
            "low_count": len(findings["low"]),
            "requires_immediate_action": len(findings["critical"]) > 0
        }
    
    def _generate_recommendations(self, findings: Dict) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if findings["critical"]:
            recommendations.append("⚠️ URGENT: Fix all CRITICAL issues before any production deployment")
        
        if any("hardcoded" in str(f).lower() for f in findings["critical"] + findings["high"]):
            recommendations.append("🔑 Move all credentials to environment variables or AWS Secrets Manager")
        
        if any("auth" in str(f).lower() for f in findings["critical"] + findings["high"]):
            recommendations.append("🔐 Implement proper authentication on all administrative interfaces")
        
        if any("https" in str(f).lower() or "ssl" in str(f).lower() for f in findings["high"]):
            recommendations.append("🔒 Enable HTTPS/TLS on all endpoints")
        
        recommendations.extend([
            "📊 Set up continuous security monitoring",
            "🔄 Schedule regular security audits (monthly)",
            "📚 Implement security training for development team",
            "🛡️ Enable AWS CloudTrail and GuardDuty"
        ])
        
        return recommendations
    
    def generate_report(self, results: Dict, output_file: str = None):
        """Generate markdown security report"""
        if output_file is None:
            output_file = f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report = self.report_generator.generate(results)
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Security audit report generated: {output_file}")
        return output_file


def main():
    """Run security audit"""
    scanner = SecurityScanner()
    results = scanner.run_full_audit()
    report_file = scanner.generate_report(results)
    
    # Print summary
    summary = results["summary"]
    print("\n" + "="*50)
    print("🔒 SECURITY AUDIT SUMMARY")
    print("="*50)
    print(f"Total Issues Found: {summary['total_issues']}")
    print(f"  - CRITICAL: {summary['critical_count']} ⚠️")
    print(f"  - HIGH: {summary['high_count']} 🟠")
    print(f"  - MEDIUM: {summary['medium_count']} 🟡")
    print(f"  - LOW: {summary['low_count']} 🔵")
    
    if summary['requires_immediate_action']:
        print("\n⚠️ IMMEDIATE ACTION REQUIRED!")
        print("Critical security vulnerabilities detected.")
    
    print(f"\nFull report: {report_file}")


if __name__ == "__main__":
    main()