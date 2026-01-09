# ============================================
# config/__init__.py
# ============================================
"""
Configuration module for Hospital-E
"""
from .settings import *

__all__ = [
    'HOSPITAL_ID',
    'PRODUCT_CODE',
    'REORDER_THRESHOLD',
    'DB_CONFIG',
    'SOAP_CONFIG',
    'EVENT_HUB_CONFIG',
    'STOCK_MS_CONFIG',
    'ORDER_MS_CONFIG'
]