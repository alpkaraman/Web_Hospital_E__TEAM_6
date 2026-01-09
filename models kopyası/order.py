# ============================================
# models/order.py
# ============================================
"""
Order data model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """
    Represents a supply order
    """
    order_id: str
    command_id: str
    hospital_id: str = "Hospital-E"
    product_code: str = "PHYSIO-SALINE-500ML"
    order_quantity: int = 0
    priority: str = "NORMAL"  # URGENT, HIGH, NORMAL
    order_status: str = "PENDING"  # PENDING, RECEIVED, DELIVERED, CANCELLED
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    warehouse_id: str = "CENTRAL-WAREHOUSE"
    received_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def is_pending(self) -> bool:
        """Check if order is pending"""
        return self.order_status == "PENDING"
    
    def is_urgent(self) -> bool:
        """Check if order is urgent priority"""
        return self.priority == "URGENT"
    
    def is_delivered(self) -> bool:
        """Check if order is delivered"""
        return self.order_status == "DELIVERED"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'order_id': self.order_id,
            'command_id': self.command_id,
            'hospital_id': self.hospital_id,
            'product_code': self.product_code,
            'order_quantity': self.order_quantity,
            'priority': self.priority,
            'order_status': self.order_status,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'warehouse_id': self.warehouse_id,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Order':
        """Create Order from database row"""
        return cls(
            order_id=row.get('order_id'),
            command_id=row.get('command_id'),
            hospital_id=row.get('hospital_id'),
            product_code=row.get('product_code'),
            order_quantity=row.get('order_quantity'),
            priority=row.get('priority'),
            order_status=row.get('order_status'),
            estimated_delivery_date=row.get('estimated_delivery_date'),
            actual_delivery_date=row.get('actual_delivery_date'),
            warehouse_id=row.get('warehouse_id'),
            received_at=row.get('received_at'),
            created_at=row.get('created_at')
        )
    
    @classmethod
    def from_command(cls, command: dict) -> 'Order':
        """Create Order from OrderCreationCommand"""
        return cls(
            order_id=command.get('orderId'),
            command_id=command.get('commandId'),
            hospital_id=command.get('hospitalId'),
            product_code=command.get('productCode'),
            order_quantity=command.get('orderQuantity'),
            priority=command.get('priority'),
            order_status='PENDING',
            estimated_delivery_date=datetime.fromisoformat(
                command.get('estimatedDeliveryDate').replace('Z', '+00:00')
            ) if command.get('estimatedDeliveryDate') else None,
            warehouse_id=command.get('warehouseId', 'CENTRAL-WAREHOUSE')
        )