"""
StockMS Application for Hospital-E
Flask-based REST API for stock monitoring
Port: 8081
"""
import logging
import sys
from threading import Thread
from flask import Flask, jsonify, request

# Add parent directory to path
sys.path.append('../../')

from config.settings import STOCK_MS_CONFIG, HOSPITAL_ID, LOG_CONFIG
from services.stock_ms.stock_monitor import stock_monitor
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
        'service': 'StockMS',
        'hospital': HOSPITAL_ID,
        'port': STOCK_MS_CONFIG['port']
    })


@app.route('/status', methods=['GET'])
def get_status():
    """Get current stock status"""
    try:
        status = stock_monitor.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger stock check (for testing)"""
    try:
        result = stock_monitor.manual_trigger()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in manual trigger: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/simulate-consumption', methods=['POST'])
def simulate_consumption():
    """Simulate consumption and update stock"""
    try:
        result = stock_monitor.simulate_consumption()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error simulating consumption: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent event logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        logs = db.get_recent_logs(limit=limit)
        return jsonify({
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get unacknowledged alerts"""
    try:
        alerts = db.get_unacknowledged_alerts()
        return jsonify({
            'count': len(alerts),
            'alerts': alerts
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        db.acknowledge_alert(alert_id)
        return jsonify({'success': True, 'alert_id': alert_id})
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/performance', methods=['GET'])
def get_performance():
    """Get performance statistics"""
    try:
        stats = db.get_performance_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/consumption-history', methods=['GET'])
def get_consumption_history():
    """Get consumption history"""
    try:
        days = request.args.get('days', 30, type=int)
        history = db.get_consumption_history(days=days)
        return jsonify({
            'days': days,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        logger.error(f"Error getting consumption history: {e}")
        return jsonify({'error': str(e)}), 500


def run_monitor_background():
    """Run stock monitor in background thread"""
    logger.info("Starting background stock monitor...")
    stock_monitor.monitor_loop(interval=STOCK_MS_CONFIG['check_interval'])


if __name__ == '__main__':
    print("=" * 70)
    print(f"  StockMS - Hospital-E Stock Monitoring Service")
    print("=" * 70)
    print(f"  Hospital: {HOSPITAL_ID}")
    print(f"  Port: {STOCK_MS_CONFIG['port']}")
    print(f"  Check Interval: {STOCK_MS_CONFIG['check_interval']}s")
    print("=" * 70)
    print("\nEndpoints:")
    print("  GET  /health                - Health check")
    print("  GET  /status                - Current stock status")
    print("  POST /trigger               - Manual stock check")
    print("  POST /simulate-consumption  - Simulate consumption")
    print("  GET  /logs                  - Recent event logs")
    print("  GET  /alerts                - Unacknowledged alerts")
    print("  GET  /performance           - Performance statistics")
    print("  GET  /consumption-history   - Consumption history")
    print("=" * 70)
    
    # Start background monitor in separate thread
    monitor_thread = Thread(target=run_monitor_background, daemon=True)
    monitor_thread.start()
    
    # Run Flask app
    app.run(
        host=STOCK_MS_CONFIG['host'],
        port=STOCK_MS_CONFIG['port'],
        debug=False
    )