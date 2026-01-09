# ============================================
# scripts/run_orderms.sh
# ============================================

#!/bin/bash
# Run OrderMS locally (without Docker)

set -e

echo "=========================================="
echo "  Starting OrderMS (Hospital-E)"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and configure it first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check database connection
echo "Checking database connection..."
python3 -c "from database.db_manager import db; db.get_current_stock(); print('✓ Database OK')" 2>/dev/null || {
    echo "ERROR: Cannot connect to database. Is PostgreSQL running?"
    exit 1
}

# Check Event Hub connection
echo "Checking Azure Event Hub connection..."
python3 -c "import os; assert os.getenv('EVENT_HUB_CONNECTION_STRING'), 'EVENT_HUB_CONNECTION_STRING not set'; print('✓ Event Hub configured')"

# Start OrderMS
echo ""
echo "Starting OrderMS on port ${ORDER_MS_PORT:-8082}..."
echo "Listening to Event Hub: ${EVENT_HUB_ORDER_TOPIC:-order-commands}"
echo "Consumer Group: ${EVENT_HUB_CONSUMER_GROUP:-hospital-e-consumer}"
echo "Press Ctrl+C to stop"
echo ""

python3 services/order_ms/app.py