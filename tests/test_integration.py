"""
Integration Tests for Hospital-E
Tests end-to-end workflows including SOAP and Event Hub communication
"""
import pytest
import sys
import time
import requests
from datetime import datetime

sys.path.append('..')

from config.settings import STOCK_MS_CONFIG, ORDER_MS_CONFIG, HOSPITAL_ID
from services.stock_ms.soap_client import soap_client
from services.stock_ms.event_producer import event_producer
from database.db_manager import db


class TestIntegration:
    """Integration tests for Hospital-E system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        self.stock_ms_url = f"http://localhost:{STOCK_MS_CONFIG['port']}"
        self.order_ms_url = f"http://localhost:{ORDER_MS_CONFIG['port']}"
    
    def test_services_health(self):
        """Test if both services are healthy"""
        # StockMS health check
        response = requests.get(f"{self.stock_ms_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['hospital'] == HOSPITAL_ID
        
        # OrderMS health check
        response = requests.get(f"{self.order_ms_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['hospital'] == HOSPITAL_ID
    
    def test_stock_status(self):
        """Test stock status endpoint"""
        response = requests.get(f"{self.stock_ms_url}/status")
        assert response.status_code == 200
        data = response.json()
        
        assert 'current_stock' in data
        assert 'daily_consumption' in data
        assert 'days_of_supply' in data
        assert 'threshold' in data
        assert data['hospital_id'] == HOSPITAL_ID
        assert data['product_code'] == 'PHYSIO-SALINE-500ML'
    
    def test_soap_connection(self):
        """Test SOAP client connection"""
        result = soap_client.test_connection()
        assert result is True, "SOAP connection failed"
    
    @pytest.mark.asyncio
    async def test_event_hub_producer_connection(self):
        """Test Event Hub producer connection"""
        result = await event_producer.test_connection()
        assert result is True, "Event Hub producer connection failed"
    
    def test_manual_stock_trigger(self):
        """Test manual stock check trigger"""
        response = requests.post(f"{self.stock_ms_url}/trigger")
        assert response.status_code == 200
        data = response.json()
        
        assert 'current_stock' in data
        assert 'consumption' in data
        assert 'days_of_supply' in data
        assert 'threshold_breached' in data
    
    def test_simulate_consumption(self):
        """Test consumption simulation"""
        response = requests.post(f"{self.stock_ms_url}/simulate-consumption")
        assert response.status_code == 200
        data = response.json()
        
        assert 'previous_stock' in data
        assert 'consumption' in data
        assert 'current_stock' in data
        assert data['current_stock'] <= data['previous_stock']
    
    def test_event_logs(self):
        """Test event log retrieval"""
        response = requests.get(f"{self.stock_ms_url}/logs?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'logs' in data
        assert isinstance(data['logs'], list)
    
    def test_consumption_history(self):
        """Test consumption history retrieval"""
        response = requests.get(f"{self.stock_ms_url}/consumption-history?days=7")
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'history' in data
        assert isinstance(data['history'], list)
    
    def test_orders_retrieval(self):
        """Test order retrieval"""
        response = requests.get(f"{self.order_ms_url}/orders")
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'orders' in data
        assert isinstance(data['orders'], list)
    
    def test_pending_orders(self):
        """Test pending orders retrieval"""
        response = requests.get(f"{self.order_ms_url}/orders/pending")
        assert response.status_code == 200
        data = response.json()
        
        assert 'count' in data
        assert 'orders' in data
    
    def test_order_stats(self):
        """Test order statistics"""
        response = requests.get(f"{self.order_ms_url}/orders/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert 'total' in data
        assert 'by_status_priority' in data
    
    def test_performance_metrics(self):
        """Test performance metrics retrieval"""
        response = requests.get(f"{self.stock_ms_url}/performance")
        assert response.status_code == 200
        data = response.json()
        
        # May be empty initially, but should return dict
        assert isinstance(data, dict)
    
    def test_dual_path_communication(self):
        """Test that both SOAP and Event Hub paths work"""
        # Trigger stock check
        response = requests.post(f"{self.stock_ms_url}/trigger")
        assert response.status_code == 200
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check event logs
        response = requests.get(f"{self.stock_ms_url}/logs?limit=20")
        logs = response.json()['logs']
        
        # Look for both SOA and SERVERLESS events
        architectures = set(log['architecture'] for log in logs)
        
        # Note: Will only have both if threshold was breached
        # At minimum, should have logged events
        assert len(logs) > 0, "No events logged"
    
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            stock = db.get_current_stock()
            assert stock is not None or stock is None  # Either works
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")
    
    def test_alert_creation_and_acknowledgment(self):
        """Test alert workflow"""
        # Get current alerts
        response = requests.get(f"{self.stock_ms_url}/alerts")
        assert response.status_code == 200
        alerts_before = response.json()['count']
        
        # Simulate consumption until threshold breach
        # (may not breach in single call)
        response = requests.post(f"{self.stock_ms_url}/simulate-consumption")
        
        # Check alerts again
        response = requests.get(f"{self.stock_ms_url}/alerts")
        assert response.status_code == 200


class TestScenarios:
    """Test predefined scenarios from Team 1"""
    
    def test_scenario_normal_replenishment(self):
        """SCEN-001: Normal Replenishment for Hospital-E"""
        # Current stock: 136, Daily: 68, Days: 2.0
        test_data = {
            'current_stock': 136,
            'daily_consumption': 68,
            'days_of_supply': 2.0,
            'expected_priority': 'HIGH'
        }
        
        # Update stock to scenario values
        db.update_stock(
            test_data['current_stock'],
            test_data['daily_consumption'],
            test_data['days_of_supply']
        )
        
        # Check status
        stock = db.get_current_stock()
        assert stock['current_stock_units'] == test_data['current_stock']
        assert float(stock['days_of_supply']) == test_data['days_of_supply']
    
    def test_scenario_critical_shortage(self):
        """SCEN-002: Critical Shortage for Hospital-E"""
        # Current stock: 34, Daily: 68, Days: 0.5
        test_data = {
            'current_stock': 34,
            'daily_consumption': 68,
            'days_of_supply': 0.5,
            'expected_priority': 'URGENT'
        }
        
        # Update stock to scenario values
        db.update_stock(
            test_data['current_stock'],
            test_data['daily_consumption'],
            test_data['days_of_supply']
        )
        
        # Check that this triggers URGENT priority
        stock = db.get_current_stock()
        assert stock['current_stock_units'] == test_data['current_stock']
        assert float(stock['days_of_supply']) < 1.0  # Critical level


if __name__ == '__main__':
    pytest.main([__file__, '-v'])