# ============================================
# tests/test_stock_ms.py
# ============================================
"""
Unit tests for StockMS components
"""
import pytest
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

sys.path.append('..')

from services.stock_ms.stock_monitor import StockMonitor
from services.stock_ms.soap_client import SOAPClient
from models.stock import Stock


class TestStockMonitor:
    """Test StockMonitor class"""
    
    @pytest.fixture
    def stock_monitor(self):
        """Create StockMonitor instance"""
        return StockMonitor()
    
    def test_calculate_consumption_weekday(self, stock_monitor):
        """Test consumption calculation for weekday"""
        consumption = stock_monitor.calculate_consumption(is_weekend=False)
        assert consumption > 0
        assert isinstance(consumption, int)
        # Should be around 68 units (±15% + spike)
        assert 40 < consumption < 150
    
    def test_calculate_consumption_weekend(self, stock_monitor):
        """Test consumption calculation for weekend"""
        consumption = stock_monitor.calculate_consumption(is_weekend=True)
        assert consumption > 0
        # Weekend should be lower (80% of weekday)
        assert 30 < consumption < 120
    
    def test_calculate_days_of_supply(self, stock_monitor):
        """Test days of supply calculation"""
        # Normal case
        days = stock_monitor.calculate_days_of_supply(136, 68)
        assert days == 2.0
        
        # Zero consumption
        days = stock_monitor.calculate_days_of_supply(100, 0)
        assert days == float('inf')
        
        # Zero stock
        days = stock_monitor.calculate_days_of_supply(0, 68)
        assert days == 0.0
    
    def test_check_threshold_breach_critical(self, stock_monitor):
        """Test threshold breach detection - critical"""
        breached, alert_type, severity = stock_monitor.check_threshold_breach(0.5)
        assert breached is True
        assert alert_type == 'CRITICAL_STOCK'
        assert severity == 'URGENT'
    
    def test_check_threshold_breach_low(self, stock_monitor):
        """Test threshold breach detection - low"""
        breached, alert_type, severity = stock_monitor.check_threshold_breach(1.5)
        assert breached is True
        assert alert_type == 'LOW_STOCK'
        assert severity == 'HIGH'
    
    def test_check_threshold_breach_adequate(self, stock_monitor):
        """Test threshold breach detection - adequate"""
        breached, alert_type, severity = stock_monitor.check_threshold_breach(3.0)
        assert breached is False
        assert alert_type is None
        assert severity is None
    
    def test_get_status(self, stock_monitor):
        """Test status retrieval"""
        with patch('services.stock_ms.stock_monitor.db') as mock_db:
            mock_db.get_current_stock.return_value = {
                'hospital_id': 'Hospital-E',
                'product_code': 'PHYSIO-SALINE-500ML',
                'current_stock_units': 136,
                'daily_consumption_units': 68,
                'days_of_supply': 2.0,
                'reorder_threshold': 2.0,
                'last_updated': datetime.now()
            }
            
            status = stock_monitor.get_status()
            assert status['hospital_id'] == 'Hospital-E'
            assert status['current_stock'] == 136
            assert status['days_of_supply'] == 2.0


class TestSOAPClient:
    """Test SOAP Client"""
    
    @pytest.fixture
    def soap_client(self):
        """Create SOAP client (may fail if no connection)"""
        try:
            return SOAPClient()
        except Exception:
            pytest.skip("SOAP service not available")
    
    def test_soap_client_initialization(self, soap_client):
        """Test SOAP client initialization"""
        assert soap_client.wsdl_url is not None
        assert soap_client.endpoint is not None
        assert soap_client.client is not None


class TestStockModel:
    """Test Stock model"""
    
    def test_stock_creation(self):
        """Test Stock model creation"""
        stock = Stock(
            hospital_id='Hospital-E',
            product_code='PHYSIO-SALINE-500ML',
            current_stock_units=136,
            daily_consumption_units=68,
            days_of_supply=2.0
        )
        
        assert stock.hospital_id == 'Hospital-E'
        assert stock.current_stock_units == 136
        assert stock.days_of_supply == 2.0
    
    def test_stock_calculate_days_of_supply(self):
        """Test days of supply calculation"""
        stock = Stock(
            current_stock_units=136,
            daily_consumption_units=68
        )
        
        days = stock.calculate_days_of_supply()
        assert days == 2.0
    
    def test_stock_is_below_threshold(self):
        """Test threshold check"""
        stock = Stock(
            current_stock_units=136,
            daily_consumption_units=68,
            days_of_supply=2.0,
            reorder_threshold=2.0
        )
        
        assert stock.is_below_threshold() is False
        
        stock.days_of_supply = 1.5
        assert stock.is_below_threshold() is True
    
    def test_stock_is_critical(self):
        """Test critical level check"""
        stock = Stock(
            days_of_supply=0.5
        )
        
        assert stock.is_critical() is True
    
    def test_stock_get_status(self):
        """Test status string generation"""
        stock = Stock(days_of_supply=3.0)
        assert stock.get_status() == 'ADEQUATE'
        
        stock.days_of_supply = 1.5
        assert stock.get_status() == 'LOW'
        
        stock.days_of_supply = 0.5
        assert stock.get_status() == 'CRITICAL'
        
        stock.current_stock_units = 0
        assert stock.get_status() == 'OUT_OF_STOCK'
    
    def test_stock_to_dict(self):
        """Test dictionary conversion"""
        stock = Stock(
            hospital_id='Hospital-E',
            current_stock_units=136,
            daily_consumption_units=68,
            days_of_supply=2.0
        )
        
        data = stock.to_dict()
        assert data['hospital_id'] == 'Hospital-E'
        assert data['current_stock_units'] == 136
        assert 'status' in data