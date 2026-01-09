#!/bin/bash
# ============================================
# scripts/run_stockms.sh
# ============================================

# Run StockMS locally (without Docker)

set -e

echo "=========================================="
echo "  Starting StockMS (Hospital-E)"
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

# Start StockMS
echo ""
echo "Starting StockMS on port ${STOCK_MS_PORT:-8081}..."
echo "Press Ctrl+C to stop"
echo ""

python3 services/stock_ms/app.py
