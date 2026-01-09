"""
Stock Monitor for Hospital-E
Monitors inventory levels and triggers dual-path communication
"""
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, Tuple

from config.settings import (
    HOSPITAL_ID, PRODUCT_CODE, STOCK_CONFIG, 
    DAILY_CONSUMPTION_AVG, REORDER_THRESHOLD
)
from database.db_manager import db
from services.stock_ms.soap_client import soap_client
from services.stock_ms.event_producer import event_producer

logger = logging.getLogger(__name__)


class StockMonitor:
    """Monitors and manages hospital inventory"""
    
    def __init__(self):
        self.hospital_id = HOSPITAL_ID
        self.product_code = PRODUCT_CODE
        self.reorder_threshold = REORDER_THRESHOLD
        self.daily_consumption_avg = DAILY_CONSUMPTION_AVG
        self.initial_stock = STOCK_CONFIG['initial_stock']
        self.max_stock = STOCK_CONFIG['max_stock']
        self.consumption_variation = STOCK_CONFIG['consumption_variation']
        self.spike_probability = STOCK_CONFIG['spike_probability']
        self.spike_multiplier = STOCK_CONFIG['spike_multiplier']
    
    def calculate_consumption(self, is_weekend: bool = False) -> int:
        """
        Calculate daily consumption with variation and spikes
        
        Args:
            is_weekend: Whether today is weekend (lower consumption)
        
        Returns:
            Calculated consumption units
        """
        base_consumption = self.daily_consumption_avg
        
        # Weekend effect: 20% lower consumption
        if is_weekend:
            base_consumption = int(base_consumption * 0.8)
        
        # Random variation: ±15%
        variation = random.uniform(
            -self.consumption_variation, 
            self.consumption_variation
        )
        consumption = base_consumption * (1 + variation)
        
        # Spike probability: 5% chance of 50% increase
        if random.random() < self.spike_probability:
            consumption *= self.spike_multiplier
            logger.info(f"📈 Consumption spike detected: {int(consumption)} units")
        
        return max(int(consumption), 1)  # At least 1 unit
    
    def calculate_days_of_supply(self, current_stock: int, daily_consumption: int) -> float:
        """Calculate days of supply remaining"""
        if daily_consumption <= 0:
            return float('inf') if current_stock > 0 else 0.0
        return round(current_stock / daily_consumption, 2)
    
    def check_threshold_breach(self, days_of_supply: float) -> Tuple[bool, str, str]:
        """
        Check if stock threshold is breached
        
        Returns:
            (breached, alert_type, severity)
        """
        if days_of_supply <= 0:
            return True, 'OUT_OF_STOCK', 'URGENT'
        elif days_of_supply < 1.0:
            return True, 'CRITICAL_STOCK', 'URGENT'
        elif days_of_supply < self.reorder_threshold:
            return True, 'LOW_STOCK', 'HIGH'
        return False, None, None
    
    def trigger_dual_path_alert(
        self,
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float
    ):
        """
        Trigger BOTH SOA and Serverless paths in parallel
        
        This is the core requirement: when threshold is breached,
        BOTH communication paths must be activated simultaneously.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.warning(
            f"🚨 THRESHOLD BREACH! Stock: {current_stock} units, "
            f"Days of supply: {days_of_supply:.2f}"
        )
        logger.info("📡 Triggering DUAL PATH communication (SOA + Serverless)...")
        
        # Path 1: SOAP (Synchronous)
        logger.info("  → Path 1: Sending SOAP request...")
        soap_response = soap_client.send_stock_update(
            current_stock=current_stock,
            daily_consumption=daily_consumption,
            days_of_supply=days_of_supply,
            timestamp=timestamp
        )
        
        if soap_response:
            logger.info(
                f"  ✅ SOAP: orderTriggered={soap_response.get('orderTriggered')}, "
                f"latency={soap_response.get('latency_ms')}ms"
            )
        else:
            logger.error("  ❌ SOAP: Failed")
        
        # Path 2: Event Hub (Asynchronous)
        logger.info("  → Path 2: Publishing Event Hub event...")
        event_success = event_producer.publish_event_sync(
            current_stock=current_stock,
            daily_consumption=daily_consumption,
            days_of_supply=days_of_supply,
            threshold=self.reorder_threshold
        )
        
        if event_success:
            logger.info("  ✅ Event Hub: Published successfully")
        else:
            logger.error("  ❌ Event Hub: Failed")
        
        logger.info("📡 Dual path communication completed")
        
        return {
            'soap_success': soap_response is not None,
            'event_hub_success': event_success,
            'soap_response': soap_response
        }
    
    def simulate_consumption(self) -> Dict:
        """
        Simulate one day of consumption and update stock
        
        Returns:
            Updated stock information
        """
        # Get current stock
        stock = db.get_current_stock()
        
        # Initialize if not exists
        if not stock:
            db.initialize_stock(self.initial_stock, self.daily_consumption_avg)
            stock = db.get_current_stock()
        
        current_stock = stock['current_stock_units']
        
        # Calculate consumption
        today = datetime.now()
        is_weekend = today.weekday() >= 5  # Saturday=5, Sunday=6
        consumption = self.calculate_consumption(is_weekend)
        
        # Update stock (don't go negative)
        new_stock = max(current_stock - consumption, 0)
        
        # Calculate days of supply
        days_of_supply = self.calculate_days_of_supply(new_stock, self.daily_consumption_avg)
        
        # Update database
        db.update_stock(new_stock, self.daily_consumption_avg, days_of_supply)
        
        # Record consumption history
        db.record_consumption(
            consumption_date=today.date(),
            units_consumed=consumption,
            opening_stock=current_stock,
            closing_stock=new_stock,
            day_of_week=today.strftime('%A'),
            is_weekend=is_weekend,
            notes=f"Simulated consumption"
        )
        
        logger.info(
            f"📊 Stock Update: {current_stock} → {new_stock} units "
            f"(consumed: {consumption}, {days_of_supply:.2f} days remaining)"
        )
        
        # Check threshold
        breached, alert_type, severity = self.check_threshold_breach(days_of_supply)
        
        result = {
            'previous_stock': current_stock,
            'consumption': consumption,
            'current_stock': new_stock,
            'days_of_supply': days_of_supply,
            'threshold_breached': breached,
            'alert_type': alert_type,
            'severity': severity
        }
        
        if breached:
            # Create alert in database
            db.create_alert(
                alert_type=alert_type,
                severity=severity,
                current_stock=new_stock,
                daily_consumption=self.daily_consumption_avg,
                days_of_supply=days_of_supply,
                threshold=self.reorder_threshold
            )
            
            # Trigger dual path communication
            comm_result = self.trigger_dual_path_alert(
                current_stock=new_stock,
                daily_consumption=self.daily_consumption_avg,
                days_of_supply=days_of_supply
            )
            result['communication_result'] = comm_result
        
        return result
    
    def monitor_loop(self, interval: int = 60):
        """
        Continuous monitoring loop
        
        Args:
            interval: Check interval in seconds
        """
        logger.info(f"🏥 Starting stock monitor for {self.hospital_id}")
        logger.info(f"   Product: {self.product_code}")
        logger.info(f"   Threshold: {self.reorder_threshold} days")
        logger.info(f"   Check interval: {interval}s")
        
        while True:
            try:
                result = self.simulate_consumption()
                
                if result['threshold_breached']:
                    logger.warning(
                        f"⚠️  ALERT: {result['alert_type']} - "
                        f"Severity: {result['severity']}"
                    )
                
                logger.info(f"⏰ Next check in {interval}s...")
                time.sleep(interval)
            
            except KeyboardInterrupt:
                logger.info("🛑 Stock monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitor loop: {e}")
                time.sleep(interval)
    
    def manual_trigger(self):
        """Manually trigger a stock check (for testing)"""
        logger.info("🔧 Manual stock check triggered")
        result = self.simulate_consumption()
        return result
    
    def get_status(self) -> Dict:
        """Get current stock status"""
        stock = db.get_current_stock()
        if not stock:
            return {'status': 'not_initialized'}
        
        return {
            'hospital_id': self.hospital_id,
            'product_code': self.product_code,
            'current_stock': stock['current_stock_units'],
            'daily_consumption': stock['daily_consumption_units'],
            'days_of_supply': float(stock['days_of_supply']),
            'threshold': self.reorder_threshold,
            'status': 'critical' if stock['days_of_supply'] < 1.0 
                     else 'low' if stock['days_of_supply'] < self.reorder_threshold 
                     else 'adequate',
            'last_updated': stock['last_updated'].isoformat() if stock['last_updated'] else None
        }


# Singleton instance
stock_monitor = StockMonitor()