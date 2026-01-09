# ============================================
# models/stock.py
# ============================================
"""
Stock data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Stock:
    """
    Represents hospital inventory stock
    """
    stock_id: Optional[int] = None
    hospital_id: str = "Hospital-E"
    product_code: str = "PHYSIO-SALINE-500ML"
    current_stock_units: int = 0
    daily_consumption_units: int = 68
    days_of_supply: float = 0.0
    reorder_threshold: float = 2.0
    max_stock_level: int = 680
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def calculate_days_of_supply(self) -> float:
        """Calculate days of supply from current values"""
        if self.daily_consumption_units <= 0:
            return float('inf') if self.current_stock_units > 0 else 0.0
        return round(self.current_stock_units / self.daily_consumption_units, 2)
    
    def is_below_threshold(self) -> bool:
        """Check if stock is below reorder threshold"""
        return self.days_of_supply < self.reorder_threshold
    
    def is_critical(self) -> bool:
        """Check if stock is at critical level (< 1 day)"""
        return self.days_of_supply < 1.0
    
    def is_out_of_stock(self) -> bool:
        """Check if out of stock"""
        return self.current_stock_units <= 0
    
    def get_status(self) -> str:
        """Get stock status as string"""
        if self.is_out_of_stock():
            return "OUT_OF_STOCK"
        elif self.is_critical():
            return "CRITICAL"
        elif self.is_below_threshold():
            return "LOW"
        else:
            return "ADEQUATE"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'stock_id': self.stock_id,
            'hospital_id': self.hospital_id,
            'product_code': self.product_code,
            'current_stock_units': self.current_stock_units,
            'daily_consumption_units': self.daily_consumption_units,
            'days_of_supply': self.days_of_supply,
            'reorder_threshold': self.reorder_threshold,
            'max_stock_level': self.max_stock_level,
            'status': self.get_status(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Stock':
        """Create Stock from database row"""
        return cls(
            stock_id=row.get('stock_id'),
            hospital_id=row.get('hospital_id'),
            product_code=row.get('product_code'),
            current_stock_units=row.get('current_stock_units'),
            daily_consumption_units=row.get('daily_consumption_units'),
            days_of_supply=float(row.get('days_of_supply')),
            reorder_threshold=float(row.get('reorder_threshold')),
            max_stock_level=row.get('max_stock_level'),
            last_updated=row.get('last_updated'),
            created_at=row.get('created_at')
        )