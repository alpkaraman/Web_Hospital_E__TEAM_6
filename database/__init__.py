# ============================================
# database/__init__.py
# ============================================
"""
Database module for Hospital-E
"""
from .db_manager import DatabaseManager, db

__all__ = ['DatabaseManager', 'db']