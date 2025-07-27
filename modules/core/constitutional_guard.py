#!/usr/bin/env python3
"""
Constitutional Guard - Enforces AVA OLO Constitutional principles
Part of the Complete Protection System v3.5.2
"""
import re
import sys
from pathlib import Path
from typing import List, Dict

class ConstitutionalGuard:
    """Enforces the 15 constitutional principles"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        
        # Constitutional violations to detect
        self.violation_patterns = {
            "hardcoded_country": {
                "patterns": [r'"(Croatia|Serbia|Bulgaria)"', r"'(Croatia|Serbia|Bulgaria)'"],
                "message": "Hardcoded country violates Principle 8 (No hardcoding)",
                "severity": "high"
            },
            "hardcoded_crop": {
                "patterns": [r'"(wheat|corn|barley|mangoes)"', r"'(wheat|corn|barley|mangoes)'"],
                "message": "Hardcoded crop violates Principle 8 (No hardcoding)",
                "severity": "medium"
            },
            "missing_version": {
                "patterns": [r"<(?!.*version).*>"],  # HTML without version
                "message": "Missing version display violates Principle 3",
                "severity": "high",
                "file_types": [".html"]
            },
            "hardcoded_colors": {
                "patterns": [r"color:\s*#[0-9A-Fa-f]{6}(?!.*8B4513|.*FFD700)"],
                "message": "Non-constitutional colors violate Design Constitution",
                "severity": "medium",
                "file_types": [".css", ".scss"]
            },
            "non_universal_text": {
                "patterns": [r"(only in Croatia|specific to Serbia|Bulgaria exclusive)"],
                "message": "Non-universal text violates Principle 1 (Mango rule)",
                "severity": "high"
            }
        }
    
    def check_file_for_violations(self, file_path: Path) -> List[Dict]:
        """Check a single file for constitutional violations"""
        violations = []
        
        if not file_path.exists() or not file_path.is_file():
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return violations
        
        # Check each violation pattern
        for violation_name, violation_config in self.violation_patterns.items():
            # Check if this violation applies to this file type
            file_types = violation_config.get("file_types", [])
            if file_types and not any(str(file_path).endswith(ft) for ft in file_types):
                continue
            
            patterns = violation_config["patterns"]
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    violations.append({
                        "type": violation_name,
                        "file": str(file_path.relative_to(self.base_path)),
                        "line": line_num,
                        "match": match.group(),
                        "message": violation_config["message"],
                        "severity": violation_config["severity"]
                    })
        
        return violations
    
    def check_directory_for_violations(self, directory: Path = None) -> List[Dict]:
        """Check entire directory for violations"""
        if directory is None:
            directory = self.base_path
        
        all_violations = []
        
        # File types to check
        check_extensions = ['.py', '.html', '.css', '.scss', '.js', '.md']
        
        for file_path in directory.rglob('*'):
            if (file_path.is_file() and 
                any(str(file_path).endswith(ext) for ext in check_extensions) and
                '.git' not in str(file_path) and
                '__pycache__' not in str(file_path)):
                
                file_violations = self.check_file_for_violations(file_path)
                all_violations.extend(file_violations)
        
        return all_violations
    
    def check_specific_constitutional_rules(self) -> List[Dict]:
        """Check specific constitutional compliance"""
        violations = []
        
        # Rule 1: Check for version badge in templates
        templates_dir = self.base_path / "templates"
        if templates_dir.exists():
            for template in templates_dir.glob("*.html"):
                try:
                    with open(template, 'r') as f:
                        content = f.read()
                    
                    if "version" not in content.lower() and "{{version}}" not in content:
                        violations.append({
                            "type": "missing_version_badge",
                            "file": str(template.relative_to(self.base_path)),
                            "line": 1,
                            "match": "template",
                            "message": "Template missing version badge (Principle 3)",
                            "severity": "high"
                        })
                except:
                    pass
        
        # Rule 2: Check main.py for version definition
        main_py = self.base_path / "main.py"
        if main_py.exists():
            try:
                with open(main_py, 'r') as f:
                    content = f.read()
                
                if "version" not in content.lower() and "VERSION" not in content:
                    violations.append({
                        "type": "missing_version_definition",
                        "file": "main.py",
                        "line": 1,
                        "match": "main.py",
                        "message": "Main application missing version definition (Principle 3)",
                        "severity": "medium"
                    })
            except:
                pass
        
        return violations
    
    def generate_compliance_report(self) -> Dict:
        """Generate comprehensive compliance report"""
        print("🏛️ Running Constitutional Compliance Check...")
        
        # Check for violations
        violations = self.check_directory_for_violations()
        constitutional_violations = self.check_specific_constitutional_rules()
        all_violations = violations + constitutional_violations
        
        # Categorize by severity
        high_severity = [v for v in all_violations if v["severity"] == "high"]
        medium_severity = [v for v in all_violations if v["severity"] == "medium"]
        low_severity = [v for v in all_violations if v["severity"] == "low"]
        
        # Determine compliance status
        if len(high_severity) > 0:
            compliance_status = "non_compliant"
        elif len(medium_severity) > 3:  # Too many medium violations
            compliance_status = "partial_compliance"
        else:
            compliance_status = "compliant"
        
        report = {
            "compliance_status": compliance_status,
            "total_violations": len(all_violations),
            "high_severity_violations": len(high_severity),
            "medium_severity_violations": len(medium_severity),
            "low_severity_violations": len(low_severity),
            "violations": all_violations,
            "constitutional_principles_checked": 15,
            "files_scanned": len(list(self.base_path.rglob('*.py'))) + len(list(self.base_path.rglob('*.html')))
        }
        
        return report
    
    def print_compliance_report(self, report: Dict):
        """Print human-readable compliance report"""
        status = report["compliance_status"]
        
        if status == "compliant":
            print("✅ CONSTITUTIONAL COMPLIANCE: PASSED")
        elif status == "partial_compliance":
            print("⚠️ CONSTITUTIONAL COMPLIANCE: PARTIAL")
        else:
            print("❌ CONSTITUTIONAL COMPLIANCE: FAILED")
        
        print(f"Total violations: {report['total_violations']}")
        print(f"High severity: {report['high_severity_violations']}")
        print(f"Medium severity: {report['medium_severity_violations']}")
        print(f"Files scanned: {report['files_scanned']}")
        
        if report['violations']:
            print("\nViolations found:")
            for violation in report['violations'][:10]:  # Show first 10
                severity_icon = "🚨" if violation['severity'] == 'high' else "⚠️" if violation['severity'] == 'medium' else "ℹ️"
                print(f"  {severity_icon} {violation['file']}:{violation['line']} - {violation['message']}")
            
            if len(report['violations']) > 10:
                print(f"  ... and {len(report['violations']) - 10} more violations")

def main():
    """Command line interface"""
    guard = ConstitutionalGuard()
    
    if len(sys.argv) < 2:
        print("Usage: python constitutional_guard.py [check|file] [file_path]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        report = guard.generate_compliance_report()
        guard.print_compliance_report(report)
        
        # Exit with error if not compliant
        if report["compliance_status"] != "compliant":
            sys.exit(1)
    
    elif command == "file":
        if len(sys.argv) < 3:
            print("Usage: python constitutional_guard.py file <file_path>")
            sys.exit(1)
        
        file_path = Path(sys.argv[2])
        violations = guard.check_file_for_violations(file_path)
        
        if violations:
            print(f"Constitutional violations in {file_path}:")
            for violation in violations:
                print(f"  Line {violation['line']}: {violation['message']}")
            sys.exit(1)
        else:
            print(f"✅ No constitutional violations in {file_path}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()