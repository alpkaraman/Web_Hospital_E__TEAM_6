#!/bin/bash

# Quick Start Script for Hospital-E Supply Chain System
# This script helps you get started quickly with the system

set -e  # Exit on error

echo "=========================================="
echo "  Hospital-E Supply Chain System"
echo "  Quick Start Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found"
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "IMPORTANT: Edit .env file with your Azure Event Hub credentials!"
        echo ""
        echo "Press Enter to continue after editing .env, or Ctrl+C to exit"
        read
    else
        print_success ".env file exists"
    fi
}

# Build and start services
start_services() {
    print_info "Building and starting services..."
    docker-compose up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for database
    echo -n "  Database... "
    for i in {1..30}; do
        if docker-compose exec -T database pg_isready -U postgres &> /dev/null; then
            print_success "ready"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            print_error "timeout"
            exit 1
        fi
    done
    
    # Wait for StockMS
    echo -n "  StockMS... "
    for i in {1..30}; do
        if curl -s http://localhost:8081/health &> /dev/null; then
            print_success "ready"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            print_error "timeout"
            exit 1
        fi
    done
    
    # Wait for OrderMS
    echo -n "  OrderMS... "
    for i in {1..30}; do
        if curl -s http://localhost:8082/health &> /dev/null; then
            print_success "ready"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            print_error "timeout"
            exit 1
        fi
    done
}

# Show service status
show_status() {
    echo ""
    echo "=========================================="
    echo "  Service Status"
    echo "=========================================="
    
    # StockMS
    STOCK_STATUS=$(curl -s http://localhost:8081/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
    if [ "$STOCK_STATUS" = "healthy" ]; then
        print_success "StockMS: http://localhost:8081 - $STOCK_STATUS"
    else
        print_error "StockMS: http://localhost:8081 - $STOCK_STATUS"
    fi
    
    # OrderMS
    ORDER_STATUS=$(curl -s http://localhost:8082/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
    if [ "$ORDER_STATUS" = "healthy" ]; then
        print_success "OrderMS: http://localhost:8082 - $ORDER_STATUS"
    else
        print_error "OrderMS: http://localhost:8082 - $ORDER_STATUS"
    fi
    
    # Database
    DB_STATUS=$(docker-compose exec -T database pg_isready -U postgres 2>/dev/null | grep "accepting connections" &> /dev/null && echo "healthy" || echo "error")
    if [ "$DB_STATUS" = "healthy" ]; then
        print_success "Database: localhost:5432 - $DB_STATUS"
    else
        print_error "Database: localhost:5432 - $DB_STATUS"
    fi
}

# Show useful commands
show_commands() {
    echo ""
    echo "=========================================="
    echo "  Useful Commands"
    echo "=========================================="
    echo ""
    echo "View logs:"
    echo "  docker-compose logs -f stock-ms"
    echo "  docker-compose logs -f order-ms"
    echo ""
    echo "Test endpoints:"
    echo "  curl http://localhost:8081/status"
    echo "  curl http://localhost:8082/orders"
    echo "  curl -X POST http://localhost:8081/trigger"
    echo ""
    echo "Run test scenarios:"
    echo "  python scripts/test_scenarios.py"
    echo ""
    echo "Stop services:"
    echo "  docker-compose down"
    echo ""
    echo "View database:"
    echo "  docker-compose exec database psql -U postgres -d hospital_e_db"
    echo ""
}

# Main execution
main() {
    echo "Step 1: Checking prerequisites..."
    check_docker
    check_docker_compose
    echo ""
    
    echo "Step 2: Checking configuration..."
    check_env_file
    echo ""
    
    echo "Step 3: Starting services..."
    start_services
    echo ""
    
    echo "Step 4: Waiting for services..."
    wait_for_services
    echo ""
    
    echo "Step 5: Checking status..."
    show_status
    echo ""
    
    print_success "Hospital-E system is ready!"
    
    show_commands
    
    echo "=========================================="
    echo "  Quick Start Complete!"
    echo "=========================================="
}

# Run main function
main