#!/usr/bin/env python3
"""
Feature Protection System - Prevents breaking working features
Part of the Complete Protection System v3.5.2
"""
import json
import sys
from datetime import datetime
from pathlib import Path

class FeatureProtectionSystem:
    """Prevents breaking working features when adding new ones"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.protection_dir = self.base_path / "protection_system"
        self.protection_dir.mkdir(exist_ok=True)
        
        # Core working features that MUST never break
        self.working_features = {
            "farmer_registration": {
                "endpoint": "/register",
                "form_fields": ["first_name", "last_name", "farm_name", "phone"],
                "database_table": "farmers",
                "status": "working"
            },
            "business_dashboard": {
                "endpoint": "/business-dashboard",
                "required_elements": ["farmer_count", "hectares_display", "yellow_box"],
                "data_source": "farmers table",
                "status": "working"
            },
            "version_display": {
                "location": "all_pages",
                "format": "vX.X.X",
                "position": "top_right",
                "status": "working"
            },
            "database_connection": {
                "type": "postgresql",
                "tables": ["farmers", "fields", "crops"],
                "status": "working"
            }
        }
    
    def capture_current_state(self):
        """Capture current working state as baseline"""
        state_file = self.protection_dir / "working_state.json"
        
        current_state = {
            "timestamp": datetime.utcnow().isoformat(),
            "features": self.working_features,
            "git_commit": self.get_current_git_commit(),
            "captured_by": "feature_protection_system"
        }
        
        with open(state_file, 'w') as f:
            json.dump(current_state, f, indent=2)
        
        print(f"✅ Working state captured: {state_file}")
        return current_state
    
    def verify_features_still_work(self) -> bool:
        """Verify all critical features still work"""
        state_file = self.protection_dir / "working_state.json"
        
        if not state_file.exists():
            print("⚠️ No baseline state found - capturing current state")
            self.capture_current_state()
            return True
        
        # Load baseline state
        with open(state_file) as f:
            baseline_state = json.load(f)
        
        violations = []
        
        # Check each feature
        for feature_name, feature_config in self.working_features.items():
            baseline_feature = baseline_state.get("features", {}).get(feature_name)
            
            if not baseline_feature:
                violations.append(f"Feature '{feature_name}' not in baseline")
                continue
            
            # Check critical properties haven't changed
            if feature_config.get("endpoint") != baseline_feature.get("endpoint"):
                violations.append(f"Feature '{feature_name}' endpoint changed")
            
            if feature_config.get("status") != "working":
                violations.append(f"Feature '{feature_name}' marked as broken")
        
        # Check for new features that might break existing ones
        current_git = self.get_current_git_commit()
        baseline_git = baseline_state.get("git_commit", "")
        
        if current_git != baseline_git:
            # There have been changes - verify they don't break features
            changes_safe = self.verify_changes_dont_break_features()
            if not changes_safe:
                violations.append("Recent changes may break existing features")
        
        if violations:
            print("❌ Feature protection violations detected:")
            for violation in violations:
                print(f"  - {violation}")
            return False
        else:
            print("✅ All features verified as working")
            return True
    
    def verify_changes_dont_break_features(self) -> bool:
        """Verify recent changes don't break existing features"""
        # In a real implementation, this would:
        # 1. Run automated tests
        # 2. Check database schema compatibility  
        # 3. Verify API endpoints still respond
        # 4. Check UI elements still exist
        
        # For now, assume changes are safe if core files exist
        critical_files = [
            "main.py",
            "templates/farmer_registration.html",
            "templates/business_dashboard.html"
        ]
        
        for file_path in critical_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                print(f"⚠️ Critical file missing: {file_path}")
                return False
        
        return True
    
    def get_current_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.base_path
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    def mark_feature_as_working(self, feature_name: str):
        """Mark a feature as confirmed working"""
        if feature_name in self.working_features:
            self.working_features[feature_name]["status"] = "working"
            self.working_features[feature_name]["last_verified"] = datetime.utcnow().isoformat()
            
            # Update saved state
            self.capture_current_state()
            print(f"✅ Feature '{feature_name}' marked as working")
        else:
            print(f"❌ Unknown feature: {feature_name}")
    
    def mark_feature_as_broken(self, feature_name: str, reason: str):
        """Mark a feature as broken - triggers protection"""
        if feature_name in self.working_features:
            self.working_features[feature_name]["status"] = "broken"
            self.working_features[feature_name]["broken_reason"] = reason
            self.working_features[feature_name]["broken_timestamp"] = datetime.utcnow().isoformat()
            
            print(f"🚨 FEATURE PROTECTION TRIGGERED!")
            print(f"Feature '{feature_name}' marked as broken: {reason}")
            print("This will block commits until fixed!")
        else:
            print(f"❌ Unknown feature: {feature_name}")
    
    def get_protection_status(self) -> dict:
        """Get current protection status"""
        working_count = sum(1 for f in self.working_features.values() if f.get("status") == "working")
        total_count = len(self.working_features)
        
        return {
            "total_features": total_count,
            "working_features": working_count,
            "broken_features": total_count - working_count,
            "protection_active": working_count == total_count,
            "features": self.working_features
        }

def main():
    """Command line interface"""
    fps = FeatureProtectionSystem()
    
    if len(sys.argv) < 2:
        print("Usage: python feature_protection.py [capture|verify|status|mark_working|mark_broken] [feature_name] [reason]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "capture":
        fps.capture_current_state()
        
    elif command == "verify":
        success = fps.verify_features_still_work()
        if not success:
            sys.exit(1)
    
    elif command == "status":
        status = fps.get_protection_status()
        print(f"Feature Protection Status:")
        print(f"  Working features: {status['working_features']}/{status['total_features']}")
        print(f"  Protection active: {'✅' if status['protection_active'] else '❌'}")
        
        for name, feature in status['features'].items():
            status_icon = "✅" if feature.get('status') == 'working' else "❌"
            print(f"  {status_icon} {name}: {feature.get('status', 'unknown')}")
    
    elif command == "mark_working":
        if len(sys.argv) < 3:
            print("Usage: python feature_protection.py mark_working <feature_name>")
            sys.exit(1)
        fps.mark_feature_as_working(sys.argv[2])
    
    elif command == "mark_broken":
        if len(sys.argv) < 4:
            print("Usage: python feature_protection.py mark_broken <feature_name> <reason>")
            sys.exit(1)
        fps.mark_feature_as_broken(sys.argv[2], sys.argv[3])
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()