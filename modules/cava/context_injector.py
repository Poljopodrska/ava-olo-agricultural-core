"""
Context Injector - Injects context reminders into conversation
"""
from typing import Dict

class ContextInjector:
    """Injects context reminders into conversation"""
    
    @staticmethod
    def create_context_reminder(critical_facts: Dict) -> str:
        """Create a context reminder for the LLM"""
        
        reminder_parts = []
        
        if critical_facts.get('farmer_name'):
            reminder_parts.append(f"[Remember: This is {critical_facts['farmer_name']}]")
        
        if critical_facts.get('location'):
            loc = critical_facts['location']
            reminder_parts.append(f"[Location: {loc.get('city', '')}, {loc.get('country', '')}]")
        
        if critical_facts.get('crops'):
            reminder_parts.append(f"[Crops: {', '.join(critical_facts['crops'])}]")
        
        if critical_facts.get('quantities'):
            for value in critical_facts['quantities'].values():
                reminder_parts.append(f"[Farm size: {value}]")
        
        return " ".join(reminder_parts) if reminder_parts else ""