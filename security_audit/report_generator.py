"""
Security Report Generator
Generates comprehensive markdown security audit reports
"""

from datetime import datetime
from typing import Dict, List, Any


class SecurityReportGenerator:
    """Generate formatted security audit reports"""
    
    def __init__(self):
        self.emoji_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🔵"
        }
    
    def generate(self, audit_results: Dict[str, Any]) -> str:
        """Generate markdown report from audit results"""
        report = []
        
        # Header
        report.append(self._generate_header(audit_results))
        
        # Executive Summary
        report.append(self._generate_executive_summary(audit_results))
        
        # Summary Statistics
        report.append(self._generate_statistics(audit_results))
        
        # Critical Findings
        if audit_results["findings"]["critical"]:
            report.append(self._generate_critical_section(audit_results["findings"]["critical"]))
        
        # High Priority Findings
        if audit_results["findings"]["high"]:
            report.append(self._generate_findings_section("HIGH", audit_results["findings"]["high"]))
        
        # Medium Priority Findings
        if audit_results["findings"]["medium"]:
            report.append(self._generate_findings_section("MEDIUM", audit_results["findings"]["medium"]))
        
        # Low Priority Findings
        if audit_results["findings"]["low"]:
            report.append(self._generate_findings_section("LOW", audit_results["findings"]["low"]))
        
        # Recommendations
        report.append(self._generate_recommendations(audit_results))
        
        # Next Steps
        report.append(self._generate_next_steps(audit_results))
        
        # Appendix
        report.append(self._generate_appendix())
        
        return "\n\n".join(report)
    
    def _generate_header(self, results: Dict) -> str:
        """Generate report header"""
        return f"""# 🔒 AVA OLO Security Audit Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Services Audited:** {', '.join(results['services'])}  
**Audit Type:** Comprehensive Security Assessment

---"""
    
    def _generate_executive_summary(self, results: Dict) -> str:
        """Generate executive summary"""
        summary = results["summary"]
        critical_count = summary["critical_count"]
        
        if critical_count > 0:
            status = "⚠️ **CRITICAL ISSUES FOUND**"
            message = f"This audit has identified {critical_count} critical security vulnerabilities that require immediate attention."
        elif summary["high_count"] > 0:
            status = "🟠 **HIGH PRIORITY ISSUES FOUND**"
            message = f"This audit has identified {summary['high_count']} high-priority security issues that should be addressed urgently."
        elif summary["medium_count"] > 0:
            status = "🟡 **MEDIUM PRIORITY ISSUES FOUND**"
            message = "The audit found several medium-priority issues that should be addressed in the near term."
        else:
            status = "✅ **GOOD SECURITY POSTURE**"
            message = "The audit found only minor issues. The application has a generally good security posture."
        
        return f"""## Executive Summary

{status}

{message}

The AVA OLO agricultural platform security audit has identified a total of **{summary['total_issues']} security issues** across the Agricultural Core and Monitoring Dashboard services. This comprehensive assessment covered authentication, data protection, code security, and infrastructure configuration."""
    
    def _generate_statistics(self, results: Dict) -> str:
        """Generate statistics section"""
        summary = results["summary"]
        
        # Calculate percentages
        total = summary["total_issues"] or 1  # Avoid division by zero
        critical_pct = (summary["critical_count"] / total) * 100
        high_pct = (summary["high_count"] / total) * 100
        medium_pct = (summary["medium_count"] / total) * 100
        low_pct = (summary["low_count"] / total) * 100
        
        return f"""## Summary Statistics

### Issue Distribution

| Severity | Count | Percentage | Status |
|----------|-------|------------|--------|
| 🔴 CRITICAL | {summary['critical_count']} | {critical_pct:.1f}% | {"⚠️ Immediate Action Required" if summary['critical_count'] > 0 else "✅ None Found"} |
| 🟠 HIGH | {summary['high_count']} | {high_pct:.1f}% | {"Action Required" if summary['high_count'] > 0 else "✅ None Found"} |
| 🟡 MEDIUM | {summary['medium_count']} | {medium_pct:.1f}% | {"Review Recommended" if summary['medium_count'] > 0 else "✅ None Found"} |
| 🔵 LOW | {summary['low_count']} | {low_pct:.1f}% | {"Monitor" if summary['low_count'] > 0 else "✅ None Found"} |
| **TOTAL** | **{summary['total_issues']}** | **100%** | - |

### Categories Affected

- 🔐 **Authentication & Access Control**
- 🔒 **Data Protection & Encryption**
- 💻 **Code Security**
- ☁️ **Infrastructure & Deployment**"""
    
    def _generate_critical_section(self, findings: List[Dict]) -> str:
        """Generate critical findings section"""
        content = ["## 🔴 CRITICAL Security Issues"]
        content.append("")
        content.append("**⚠️ These issues pose immediate risk and must be fixed before production deployment:**")
        content.append("")
        
        for i, finding in enumerate(findings, 1):
            content.append(f"### {i}. {finding['issue']}")
            content.append("")
            content.append(f"**Category:** {finding['category']}")
            content.append(f"**Description:** {finding['description']}")
            
            if 'file' in finding:
                content.append(f"**Location:** `{finding['file']}`")
            
            if 'line' in finding:
                content.append(f"**Line:** {finding['line']}")
            
            if 'code_snippet' in finding:
                content.append(f"**Code:** `{finding['code_snippet']}`")
            
            content.append(f"**Recommendation:** {finding['recommendation']}")
            content.append("")
            
            # Add specific fix instructions for critical issues
            if "hardcoded" in finding['issue'].lower():
                content.append("**Fix Instructions:**")
                content.append("1. Remove hardcoded credentials immediately")
                content.append("2. Rotate any exposed credentials")
                content.append("3. Use environment variables or AWS Secrets Manager")
                content.append("4. Update deployment configurations")
            elif "dashboard" in finding['issue'].lower() and "auth" in finding['issue'].lower():
                content.append("**Fix Instructions:**")
                content.append("1. Implement authentication middleware")
                content.append("2. Add login page and session management")
                content.append("3. Protect all dashboard routes")
                content.append("4. Test authentication thoroughly")
            
            content.append("")
            content.append("---")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_findings_section(self, severity: str, findings: List[Dict]) -> str:
        """Generate findings section for given severity"""
        emoji = self.emoji_map[severity]
        content = [f"## {emoji} {severity} Priority Issues"]
        content.append("")
        
        # Group findings by category
        by_category = {}
        for finding in findings:
            category = finding.get('category', 'General')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)
        
        for category, category_findings in by_category.items():
            content.append(f"### {category}")
            content.append("")
            
            for finding in category_findings:
                content.append(f"#### • {finding['issue']}")
                content.append(f"   - **Description:** {finding['description']}")
                
                if 'file' in finding:
                    content.append(f"   - **File:** `{finding['file']}`")
                
                content.append(f"   - **Recommendation:** {finding['recommendation']}")
                content.append("")
        
        return "\n".join(content)
    
    def _generate_recommendations(self, results: Dict) -> str:
        """Generate recommendations section"""
        content = ["## 📋 Security Recommendations"]
        content.append("")
        content.append("Based on this audit, we recommend the following security improvements:")
        content.append("")
        
        # Priority-based recommendations
        if results["summary"]["critical_count"] > 0:
            content.append("### 🔴 Immediate Actions (Within 24-48 hours)")
            content.append("")
            content.append("1. **Fix all CRITICAL vulnerabilities** - These pose immediate risk")
            content.append("2. **Implement dashboard authentication** - Protect sensitive agricultural data")
            content.append("3. **Remove hardcoded credentials** - Move to secure credential management")
            content.append("4. **Enable HTTPS/TLS** - Encrypt all data in transit")
            content.append("")
        
        content.append("### 🟠 Short-term Actions (Within 1 week)")
        content.append("")
        content.append("1. **Implement security headers** - Add X-Frame-Options, CSP, etc.")
        content.append("2. **Enable database encryption** - Use SSL/TLS for RDS connections")
        content.append("3. **Fix SQL injection vulnerabilities** - Use parameterized queries")
        content.append("4. **Implement CSRF protection** - Add tokens to all forms")
        content.append("")
        
        content.append("### 🟡 Medium-term Actions (Within 1 month)")
        content.append("")
        content.append("1. **Set up security monitoring** - CloudTrail, GuardDuty, CloudWatch")
        content.append("2. **Implement automated security scanning** - Add to CI/CD pipeline")
        content.append("3. **Create security documentation** - Policies and procedures")
        content.append("4. **Conduct security training** - For development team")
        content.append("")
        
        content.append("### 🔵 Long-term Actions (Ongoing)")
        content.append("")
        content.append("1. **Regular security audits** - Monthly automated, quarterly manual")
        content.append("2. **Dependency updates** - Keep all libraries current")
        content.append("3. **Penetration testing** - Annual third-party assessment")
        content.append("4. **Security awareness** - Continuous team education")
        
        return "\n".join(content)
    
    def _generate_next_steps(self, results: Dict) -> str:
        """Generate next steps section"""
        return """## 🚀 Next Steps

1. **Review this report** with the development team and stakeholders
2. **Prioritize fixes** based on severity and business impact
3. **Create tickets** for each security issue in your tracking system
4. **Implement fixes** starting with CRITICAL issues
5. **Verify fixes** through testing and re-scanning
6. **Document changes** and update security policies
7. **Schedule follow-up** audit in 30 days

### Support Resources

- AWS Security Best Practices: https://aws.amazon.com/security/best-practices/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- AVA OLO Security Guidelines: [To be created]"""
    
    def _generate_appendix(self) -> str:
        """Generate appendix"""
        return """## 📚 Appendix

### Severity Definitions

- **🔴 CRITICAL**: Vulnerabilities that can be exploited immediately to compromise the system
- **🟠 HIGH**: Serious issues that could lead to data breach or system compromise
- **🟡 MEDIUM**: Issues that pose moderate risk or violate security best practices
- **🔵 LOW**: Minor issues or recommendations for security hardening

### Audit Scope

This security audit covered:
- Authentication and authorization mechanisms
- Data protection and encryption practices
- Code security (SQL injection, XSS, etc.)
- Infrastructure and deployment security
- Third-party dependencies
- Configuration management

### Compliance Considerations

For Croatian agricultural operations, consider:
- GDPR compliance for farmer data
- Croatian National Security Standards
- Agricultural data protection regulations
- EU cybersecurity directives

---

*This report was generated by the AVA OLO Security Scanner v1.0*"""