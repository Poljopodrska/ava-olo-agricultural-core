"""
Zero-Regression Safety Monitoring System
COMPLETELY ISOLATED - No imports from existing modules
Read-only database access only
"""
from .safety_monitor import SafetyMonitor

__all__ = ['SafetyMonitor']