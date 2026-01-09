# ============================================
# services/stock_ms/__init__.py
# ============================================
"""
Stock Monitoring Service (StockMS)
Monitors inventory and triggers dual-path communication
"""
from .stock_monitor import StockMonitor, stock_monitor
from .soap_client import SOAPClient, soap_client
from .event_producer import EventHubProducer, event_producer

__all__ = [
    'StockMonitor',
    'stock_monitor',
    'SOAPClient',
    'soap_client',
    'EventHubProducer',
    'event_producer'
]