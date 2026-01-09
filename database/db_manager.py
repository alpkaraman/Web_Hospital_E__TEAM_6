"""
Database Manager for Hospital-E
Handles all database operations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from config.settings import DB_CONFIG, HOSPITAL_ID, PRODUCT_CODE

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DB_CONFIG
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query and optionally fetch results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                return cur.rowcount
    
    def execute_one(self, query: str, params: tuple = None):
        """Execute query and fetch one result"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()
    
    # ============================================
    # Stock Operations
    # ============================================
    
    def get_current_stock(self) -> Optional[Dict]:
        """Get current stock for Hospital-E"""
        query = """
            SELECT * FROM Stock 
            WHERE hospital_id = %s AND product_code = %s
        """
        return self.execute_one(query, (HOSPITAL_ID, PRODUCT_CODE))
    
    def update_stock(self, current_stock: int, daily_consumption: int, days_of_supply: float):
        """Update stock levels"""
        query = """
            INSERT INTO Stock (
                hospital_id, product_code, current_stock_units,
                daily_consumption_units, days_of_supply
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (hospital_id, product_code)
            DO UPDATE SET
                current_stock_units = EXCLUDED.current_stock_units,
                daily_consumption_units = EXCLUDED.daily_consumption_units,
                days_of_supply = EXCLUDED.days_of_supply,
                last_updated = CURRENT_TIMESTAMP
        """
        self.execute_query(
            query,
            (HOSPITAL_ID, PRODUCT_CODE, current_stock, daily_consumption, days_of_supply)
        )
        logger.info(f"Stock updated: {current_stock} units, {days_of_supply:.2f} days")
    
    def initialize_stock(self, initial_stock: int, daily_consumption: int):
        """Initialize stock if not exists"""
        stock = self.get_current_stock()
        if not stock:
            days_of_supply = initial_stock / daily_consumption if daily_consumption > 0 else 0
            self.update_stock(initial_stock, daily_consumption, days_of_supply)
            logger.info(f"Stock initialized: {initial_stock} units")
    
    # ============================================
    # Order Operations
    # ============================================
    
    def insert_order(self, order_data: Dict):
        """Insert a new order"""
        query = """
            INSERT INTO Orders (
                order_id, command_id, hospital_id, product_code,
                order_quantity, priority, order_status,
                estimated_delivery_date, warehouse_id
            ) VALUES (
                %(orderId)s, %(commandId)s, %(hospitalId)s, %(productCode)s,
                %(orderQuantity)s, %(priority)s, 'PENDING',
                %(estimatedDeliveryDate)s, %(warehouseId)s
            )
            ON CONFLICT (order_id) DO NOTHING
        """
        try:
            self.execute_query(query, order_data)
            logger.info(f"Order inserted: {order_data['orderId']}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert order: {e}")
            return False
    
    def get_pending_orders(self) -> List[Dict]:
        """Get all pending orders"""
        query = """
            SELECT * FROM Orders 
            WHERE hospital_id = %s AND order_status = 'PENDING'
            ORDER BY received_at DESC
        """
        return self.execute_query(query, (HOSPITAL_ID,), fetch=True)
    
    def update_order_status(self, order_id: str, status: str):
        """Update order status"""
        query = """
            UPDATE Orders 
            SET order_status = %s, 
                actual_delivery_date = CASE WHEN %s = 'DELIVERED' 
                    THEN CURRENT_TIMESTAMP ELSE actual_delivery_date END
            WHERE order_id = %s
        """
        self.execute_query(query, (status, status, order_id))
    
    # ============================================
    # Event Log Operations
    # ============================================
    
    def log_event(self, event_type: str, direction: str, architecture: str,
                  payload: str, status: str, error_message: str = None,
                  latency_ms: int = None):
        """Log a communication event"""
        query = """
            INSERT INTO EventLog (
                event_type, direction, architecture, payload,
                status, error_message, latency_ms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(
            query,
            (event_type, direction, architecture, payload, status, error_message, latency_ms)
        )
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent event logs"""
        query = """
            SELECT * FROM EventLog 
            ORDER BY timestamp DESC 
            LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)
    
    # ============================================
    # Consumption History Operations
    # ============================================
    
    def record_consumption(self, consumption_date: datetime, units_consumed: int,
                          opening_stock: int, closing_stock: int,
                          day_of_week: str, is_weekend: bool, notes: str = None):
        """Record daily consumption"""
        query = """
            INSERT INTO ConsumptionHistory (
                hospital_id, product_code, consumption_date, units_consumed,
                opening_stock, closing_stock, day_of_week, is_weekend, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (hospital_id, product_code, consumption_date) DO NOTHING
        """
        self.execute_query(
            query,
            (HOSPITAL_ID, PRODUCT_CODE, consumption_date, units_consumed,
             opening_stock, closing_stock, day_of_week, is_weekend, notes)
        )
    
    def get_consumption_history(self, days: int = 30) -> List[Dict]:
        """Get consumption history for last N days"""
        query = """
            SELECT * FROM ConsumptionHistory
            WHERE hospital_id = %s AND product_code = %s
            ORDER BY consumption_date DESC
            LIMIT %s
        """
        return self.execute_query(query, (HOSPITAL_ID, PRODUCT_CODE, days), fetch=True)
    
    # ============================================
    # Alert Operations
    # ============================================
    
    def create_alert(self, alert_type: str, severity: str, current_stock: int,
                    daily_consumption: int, days_of_supply: float, threshold: float):
        """Create a new alert"""
        query = """
            INSERT INTO Alerts (
                hospital_id, alert_type, severity, current_stock,
                daily_consumption, days_of_supply, threshold
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(
            query,
            (HOSPITAL_ID, alert_type, severity, current_stock,
             daily_consumption, days_of_supply, threshold)
        )
        logger.warning(f"Alert created: {alert_type} - {severity}")
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get all unacknowledged alerts"""
        query = """
            SELECT * FROM Alerts 
            WHERE hospital_id = %s AND acknowledged = FALSE
            ORDER BY created_at DESC
        """
        return self.execute_query(query, (HOSPITAL_ID,), fetch=True)
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        query = """
            UPDATE Alerts 
            SET acknowledged = TRUE, acknowledged_at = CURRENT_TIMESTAMP
            WHERE alert_id = %s
        """
        self.execute_query(query, (alert_id,))
    
    # ============================================
    # Performance Metrics
    # ============================================
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        query = """
            SELECT 
                architecture,
                COUNT(*) as total_events,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
            FROM EventLog
            WHERE latency_ms IS NOT NULL
            GROUP BY architecture
        """
        results = self.execute_query(query, fetch=True)
        return {row['architecture']: dict(row) for row in results}


# Singleton instance
db = DatabaseManager()