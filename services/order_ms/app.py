"""
OrderMS Application for Hospital-E
Flask-based REST API for order management
Consumes events from Azure Event Hub
Port: 8082
"""
import logging
import sys
from threading import Thread
from flask import Flask, jsonify, request

# Add parent directory to path
sys.path.append('../../')

from config.settings import ORDER_MS_CONFIG, HOSPITAL_ID, LOG_CONFIG
from services.order_ms.event_consumer import event_consumer
from database.db_manager import db

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format']
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OrderMS',
        'hospital': HOSPITAL_ID,
        'port': ORDER_MS_CONFIG['port'],
        'consumer_running': event_consumer.running
    })


@app.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    try:
        status_filter = request.args.get('status', None)
        
        if status_filter:
            # Get orders by status
            query = """
                SELECT * FROM Orders 
                WHERE hospital_id = %s AND order_status = %s
                ORDER BY received_at DESC
            """
            orders = db.execute_query(query, (HOSPITAL_ID, status_filter.upper()), fetch=True)
        else:
            # Get all orders
            query = """
                SELECT * FROM Orders 
                WHERE hospital_id = %s
                ORDER BY received_at DESC
            """
            orders = db.execute_query(query, (HOSPITAL_ID,), fetch=True)
        
        return jsonify({
            'count': len(orders),
            'orders': orders
        })
    
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific order by ID"""
    try:
        query = """
            SELECT * FROM Orders 
            WHERE order_id = %s AND hospital_id = %s
        """
        order = db.execute_one(query, (order_id, HOSPITAL_ID))
        
        if order:
            return jsonify(order)
        else:
            return jsonify({'error': 'Order not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        new_status = data.get('status', '').upper()
        
        valid_statuses = ['PENDING', 'RECEIVED', 'DELIVERED', 'CANCELLED']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        db.update_order_status(order_id, new_status)
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'new_status': new_status
        })
    
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orders/pending', methods=['GET'])
def get_pending_orders():
    """Get pending orders"""
    try:
        orders = db.get_pending_orders()
        return jsonify({
            'count': len(orders),
            'orders': orders
        })
    except Exception as e:
        logger.error(f"Error getting pending orders: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Get order statistics"""
    try:
        query = """
            SELECT 
                order_status,
                priority,
                COUNT(*) as count,
                SUM(order_quantity) as total_quantity
            FROM Orders
            WHERE hospital_id = %s
            GROUP BY order_status, priority
            ORDER BY order_status, priority
        """
        stats = db.execute_query(query, (HOSPITAL_ID,), fetch=True)
        
        # Total stats
        total_query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(order_quantity) as total_units
            FROM Orders
            WHERE hospital_id = %s
        """
        total = db.execute_one(total_query, (HOSPITAL_ID,))
        
        return jsonify({
            'total': total,
            'by_status_priority': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting order stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent event logs (filtered for ORDER_RECEIVED)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        query = """
            SELECT * FROM EventLog
            WHERE event_type = 'ORDER_RECEIVED'
            ORDER BY timestamp DESC
            LIMIT %s
        """
        logs = db.execute_query(query, (limit,), fetch=True)
        
        return jsonify({
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500


def run_consumer_background():
    """Run Event Hub consumer in background thread"""
    logger.info("Starting background Event Hub consumer...")
    event_consumer.start()


if __name__ == '__main__':
    print("=" * 70)
    print(f"  OrderMS - Hospital-E Order Management Service")
    print("=" * 70)
    print(f"  Hospital: {HOSPITAL_ID}")
    print(f"  Port: {ORDER_MS_CONFIG['port']}")
    print(f"  Event Hub: {event_consumer.event_hub_name}")
    print(f"  Consumer Group: {event_consumer.consumer_group}")
    print("=" * 70)
    print("\nEndpoints:")
    print("  GET  /health                - Health check")
    print("  GET  /orders                - Get all orders")
    print("  GET  /orders/<id>           - Get specific order")
    print("  PUT  /orders/<id>/status    - Update order status")
    print("  GET  /orders/pending        - Get pending orders")
    print("  GET  /orders/stats          - Get order statistics")
    print("  GET  /logs                  - Recent order logs")
    print("=" * 70)
    
    # Start background consumer in separate thread
    consumer_thread = Thread(target=run_consumer_background, daemon=True)
    consumer_thread.start()
    
    # Run Flask app
    app.run(
        host=ORDER_MS_CONFIG['host'],
        port=ORDER_MS_CONFIG['port'],
        debug=False
    )