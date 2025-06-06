# notification_structure.py

from enum import Enum
from typing import Dict, Any

class NotificationSeverity(Enum):
    """Enum for notification severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Notification:
    """
    Simple notification structure
    Main fields:
    - title: str
    - severity: NotificationSeverity  
    - body: dict (JSON format)  
    """
    
    def __init__(self, title: str, severity: NotificationSeverity, body: Dict[str, Any]):
        self.title = title
        self.severity = severity
        self.body = body  

