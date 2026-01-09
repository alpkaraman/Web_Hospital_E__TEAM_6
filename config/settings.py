"""
Configuration Settings for Hospital-E
Loads from environment variables with fallback defaults
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Hospital Identity
# ============================================
HOSPITAL_ID = "Hospital-E"
HOSPITAL_NAME = "Central Medical Complex"
BED_CAPACITY = 400
DAILY_CONSUMPTION_AVG = 68  # units/day
PRODUCT_CODE = "PHYSIO-SALINE-500ML"
REORDER_THRESHOLD = 2.0  # days

# ============================================
# Database Configuration
# ============================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'hospital_e_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# ============================================
# Team 1 - SOAP Service Configuration
# ============================================
SOAP_CONFIG = {
    'wsdl_url': os.getenv(
        'SOAP_WSDL_URL',
        'http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices?wsdl'
    ),
    'endpoint': os.getenv(
        'SOAP_ENDPOINT',
        'http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices'
    ),
    'timeout': int(os.getenv('SOAP_TIMEOUT', 30)),
    'retry_count': int(os.getenv('SOAP_RETRY_COUNT', 3)),
    'retry_delay': int(os.getenv('SOAP_RETRY_DELAY', 5))
}

# ============================================
# Azure Event Hub Configuration
# ============================================
EVENT_HUB_CONFIG = {
    'connection_string': os.getenv(
        'EVENT_HUB_CONNECTION_STRING',
        'Endpoint=sb://medical-supply-chain-ns.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=HFDW05QKieWgy3uDKmNHc2OisPdrfNvoy+AEhKCJZlw='
    ),
    'inventory_topic': os.getenv('EVENT_HUB_INVENTORY_TOPIC', 'inventory-low-events'),
    'order_topic': os.getenv('EVENT_HUB_ORDER_TOPIC', 'order-commands'),
    'consumer_group': os.getenv('EVENT_HUB_CONSUMER_GROUP', 'hospital-e-consumer')
}

# ============================================
# Microservices Configuration
# ============================================
STOCK_MS_CONFIG = {
    'host': os.getenv('STOCK_MS_HOST', '0.0.0.0'),
    'port': int(os.getenv('STOCK_MS_PORT', 8081)),
    'check_interval': int(os.getenv('STOCK_CHECK_INTERVAL', 60))  # seconds
}

ORDER_MS_CONFIG = {
    'host': os.getenv('ORDER_MS_HOST', '0.0.0.0'),
    'port': int(os.getenv('ORDER_MS_PORT', 8082))
}

# ============================================
# Stock Monitoring Configuration
# ============================================
STOCK_CONFIG = {
    'initial_stock': int(os.getenv('INITIAL_STOCK', 200)),
    'max_stock': int(os.getenv('MAX_STOCK', 680)),  # 10 days supply
    'reorder_threshold': REORDER_THRESHOLD,
    'consumption_variation': float(os.getenv('CONSUMPTION_VARIATION', 0.15)),  # ±15%
    'spike_probability': float(os.getenv('SPIKE_PROBABILITY', 0.05)),  # 5%
    'spike_multiplier': float(os.getenv('SPIKE_MULTIPLIER', 1.5))  # 50% increase
}

# ============================================
# Logging Configuration
# ============================================
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'logs/hospital_e.log')
}

# ============================================
# Testing & Development
# ============================================
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
TESTING = os.getenv('TESTING', 'False').lower() == 'true'
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'False').lower() == 'true'