"""
SOAP Client for Hospital-E
Communicates with Team 1's SOAP services
"""
import logging
import time
from typing import Dict, Optional
from zeep import Client
from zeep.transports import Transport
from zeep.exceptions import Fault, TransportError
from requests import Session

from config.settings import SOAP_CONFIG, HOSPITAL_ID
from database.db_manager import db

logger = logging.getLogger(__name__)


class SOAPClient:
    """SOAP client for StockUpdateService"""
    
    def __init__(self):
        self.wsdl_url = SOAP_CONFIG['wsdl_url']
        self.endpoint = SOAP_CONFIG['endpoint']
        self.timeout = SOAP_CONFIG['timeout']
        self.retry_count = SOAP_CONFIG['retry_count']
        self.retry_delay = SOAP_CONFIG['retry_delay']
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SOAP client with timeout settings"""
        try:
            session = Session()
            session.timeout = self.timeout
        
            # Content-Type header ekle
            session.headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': ''
            }
        
            transport = Transport(session=session)
        
            self.client = Client(
                wsdl=self.wsdl_url,
                transport=transport
            )
            logger.info(f"SOAP client initialized: {self.wsdl_url}")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}")
            raise
    
    def send_stock_update(
        self,
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float,
        timestamp: str
    ) -> Optional[Dict]:
        """
        Send stock update to Team 1's StockUpdateService
        
        Args:
            current_stock: Current stock units
            daily_consumption: Daily consumption units
            days_of_supply: Calculated days of supply
            timestamp: ISO 8601 timestamp
        
        Returns:
            Response dict or None if failed
        """
        request_data = {
            'hospitalId': HOSPITAL_ID,
            'productCode': 'PHYSIO-SALINE-500ML',
            'currentStockUnits': current_stock,
            'dailyConsumptionUnits': daily_consumption,
            'daysOfSupply': days_of_supply,
            'timestamp': timestamp
        }
        
        logger.info(f"[SOAP] Sending stock update: {current_stock} units, {days_of_supply:.2f} days")
        
        # Retry logic
        for attempt in range(1, self.retry_count + 1):
            try:
                start_time = time.time()
                
                # Call SOAP service
                response = self.client.service.StockUpdate(request=request_data)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Log success
                db.log_event(
                    event_type='STOCK_UPDATE_SENT',
                    direction='OUTGOING',
                    architecture='SOA',
                    payload=str(request_data),
                    status='SUCCESS',
                    latency_ms=latency_ms
                )
                
                logger.info(
                    f"[SOAP] Success: orderTriggered={response.get('orderTriggered')}, "
                    f"latency={latency_ms}ms"
                )
                
                return {
                    'success': response.get('success'),
                    'message': response.get('message'),
                    'orderTriggered': response.get('orderTriggered'),
                    'orderId': response.get('orderId'),
                    'latency_ms': latency_ms
                }
            
            except Fault as fault:
                logger.error(f"[SOAP] SOAP Fault (attempt {attempt}): {fault}")
                
                db.log_event(
                    event_type='STOCK_UPDATE_SENT',
                    direction='OUTGOING',
                    architecture='SOA',
                    payload=str(request_data),
                    status='FAILURE',
                    error_message=str(fault)
                )
                
                if attempt < self.retry_count:
                    logger.info(f"[SOAP] Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("[SOAP] Max retries reached")
                    return None
            
            except TransportError as e:
                logger.error(f"[SOAP] Transport error (attempt {attempt}): {e}")
                
                db.log_event(
                    event_type='STOCK_UPDATE_SENT',
                    direction='OUTGOING',
                    architecture='SOA',
                    payload=str(request_data),
                    status='TIMEOUT' if 'timeout' in str(e).lower() else 'FAILURE',
                    error_message=str(e)
                )
                
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                else:
                    return None
            
            except Exception as e:
                logger.error(f"[SOAP] Unexpected error: {e}")
                
                db.log_event(
                    event_type='STOCK_UPDATE_SENT',
                    direction='OUTGOING',
                    architecture='SOA',
                    payload=str(request_data),
                    status='FAILURE',
                    error_message=str(e)
                )
                return None
        
        return None
    
    def test_connection(self) -> bool:
        """Test SOAP service connection"""
        try:
            # Try to get service definition
            _ = self.client.service
            logger.info("[SOAP] Connection test successful")
            return True
        except Exception as e:
            logger.error(f"[SOAP] Connection test failed: {e}")
            return False


# Singleton instance
soap_client = SOAPClient()