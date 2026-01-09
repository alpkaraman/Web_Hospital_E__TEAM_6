# ============================================
# tests/test_order_ms.py
# ============================================
"""
Unit tests for OrderMS components
"""
import pytest
import sys
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.append('..')

from services.order_ms.event_consumer import EventHubConsumer
from models.order import Order


class TestEventHubConsumer:
    """Test Event Hub Consumer"""
    
    @pytest.fixture
    def consumer(self):
        """Create consumer instance"""
        return EventHubConsumer()
    
    def test_validate_order_command_valid(self, consumer):
        """Test validation with valid command"""
        command = {
            'commandId': 'cmd-123',
            'commandType': 'CreateOrder',
            'orderId': 'ORD-123',
            'hospitalId': 'Hospital-E',
            'productCode': 'PHYSIO-SALINE-500ML',
            'orderQuantity': 340,
            'priority': 'HIGH',
            'estimatedDeliveryDate': '2026-01-10T10:00:00Z',
            'timestamp': '2026-01-09T10:00:00Z'
        }
        
        assert consumer.validate_order_command(command) is True
    
    def test_validate_order_command_missing_field(self, consumer):
        """Test validation with missing field"""
        command = {
            'commandId': 'cmd-123',
            'commandType': 'CreateOrder',
            # Missing orderId
            'hospitalId': 'Hospital-E'
        }
        
        assert consumer.validate_order_command(command) is False
    
    def test_validate_order_command_invalid_type(self, consumer):
        """Test validation with invalid command type"""
        command = {
            'commandId': 'cmd-123',
            'commandType': 'InvalidType',
            'orderId': 'ORD-123',
            'hospitalId': 'Hospital-E',
            'productCode': 'TEST',
            'orderQuantity': 100,
            'priority': 'HIGH',
            'estimatedDeliveryDate': '2026-01-10T10:00:00Z',
            'timestamp': '2026-01-09T10:00:00Z'
        }
        
        assert consumer.validate_order_command(command) is False
    
    def test_should_process_order_correct_hospital(self, consumer):
        """Test order filtering - correct hospital"""
        command = {'hospitalId': 'Hospital-E'}
        assert consumer.should_process_order(command) is True
    
    def test_should_process_order_wrong_hospital(self, consumer):
        """Test order filtering - wrong hospital"""
        command = {'hospitalId': 'Hospital-A'}
        assert consumer.should_process_order(command) is False
    
    def test_process_order_command(self, consumer):
        """Test order command processing"""
        command = {
            'commandId': 'cmd-123',
            'commandType': 'CreateOrder',
            'orderId': 'ORD-123',
            'hospitalId': 'Hospital-E',
            'productCode': 'PHYSIO-SALINE-500ML',
            'orderQuantity': 340,
            'priority': 'HIGH',
            'estimatedDeliveryDate': '2026-01-10T10:00:00Z',
            'warehouseId': 'CENTRAL-WAREHOUSE',
            'timestamp': '2026-01-09T10:00:00Z'
        }
        
        with patch('services.order_ms.event_consumer.db') as mock_db:
            mock_db.insert_order.return_value = True
            consumer.process_order_command(command)
            mock_db.insert_order.assert_called_once()


class TestOrderModel:
    """Test Order model"""
    
    def test_order_creation(self):
        """Test Order model creation"""
        order = Order(
            order_id='ORD-123',
            command_id='cmd-123',
            hospital_id='Hospital-E',
            product_code='PHYSIO-SALINE-500ML',
            order_quantity=340,
            priority='HIGH'
        )
        
        assert order.order_id == 'ORD-123'
        assert order.hospital_id == 'Hospital-E'
        assert order.order_quantity == 340
    
    def test_order_is_pending(self):
        """Test pending status check"""
        order = Order(
            order_id='ORD-123',
            command_id='cmd-123',
            order_status='PENDING'
        )
        
        assert order.is_pending() is True
    
    def test_order_is_urgent(self):
        """Test urgent priority check"""
        order = Order(
            order_id='ORD-123',
            command_id='cmd-123',
            priority='URGENT'
        )
        
        assert order.is_urgent() is True
    
    def test_order_to_dict(self):
        """Test dictionary conversion"""
        order = Order(
            order_id='ORD-123',
            command_id='cmd-123',
            hospital_id='Hospital-E',
            order_quantity=340
        )
        
        data = order.to_dict()
        assert data['order_id'] == 'ORD-123'
        assert data['hospital_id'] == 'Hospital-E'
        assert data['order_quantity'] == 340
    
    def test_order_from_command(self):
        """Test creation from command"""
        command = {
            'orderId': 'ORD-123',
            'commandId': 'cmd-123',
            'hospitalId': 'Hospital-E',
            'productCode': 'PHYSIO-SALINE-500ML',
            'orderQuantity': 340,
            'priority': 'HIGH',
            'estimatedDeliveryDate': '2026-01-10T10:00:00Z',
            'warehouseId': 'CENTRAL-WAREHOUSE'
        }
        
        order = Order.from_command(command)
        assert order.order_id == 'ORD-123'
        assert order.hospital_id == 'Hospital-E'
        assert order.priority == 'HIGH'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])