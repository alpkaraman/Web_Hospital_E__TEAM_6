# ============================================
# models/event_log.py
# ============================================
"""
Event log data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class EventLog:
    """
    Represents a communication event log entry
    """
    log_id: Optional[int] = None
    event_type: str = ""  # STOCK_UPDATE_SENT, INVENTORY_EVENT_PUBLISHED, ORDER_RECEIVED
    direction: str = ""  # OUTGOING, INCOMING
    architecture: str = ""  # SOA, SERVERLESS
    payload: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS, FAILURE, TIMEOUT, RETRY
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    def is_successful(self) -> bool:
        """Check if event was successful"""
        return self.status == "SUCCESS"
    
    def is_soa(self) -> bool:
        """Check if SOA architecture"""
        return self.architecture == "SOA"
    
    def is_serverless(self) -> bool:
        """Check if Serverless architecture"""
        return self.architecture == "SERVERLESS"
    
    def is_outgoing(self) -> bool:
        """Check if outgoing event"""
        return self.direction == "OUTGOING"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'log_id': self.log_id,
            'event_type': self.event_type,
            'direction': self.direction,
            'architecture': self.architecture,
            'payload': self.payload,
            'status': self.status,
            'error_message': self.error_message,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'EventLog':
        """Create EventLog from database row"""
        return cls(
            log_id=row.get('log_id'),
            event_type=row.get('event_type'),
            direction=row.get('direction'),
            architecture=row.get('architecture'),
            payload=row.get('payload'),
            status=row.get('status'),
            error_message=row.get('error_message'),
            latency_ms=row.get('latency_ms'),
            timestamp=row.get('timestamp')
        )