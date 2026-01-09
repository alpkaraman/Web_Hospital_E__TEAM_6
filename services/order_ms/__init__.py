# ============================================
# services/order_ms/__init__.py
# ============================================
"""
Order Management Service (OrderMS)
Consumes order commands from Event Hub
"""
from .event_consumer import EventHubConsumer, event_consumer

__all__ = ['EventHubConsumer', 'event_consumer']