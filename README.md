§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Project Overview

This project implements a dual-architecture supply chain management system for Hospital-E (Central Medical Complex), integrating with Team 1's central warehouse using both:

SOA Architecture (Legacy): SOAP/WSDL synchronous communication
Serverless Architecture (Modern): Azure Event Hubs asynchronous messaging

Hospital Details

Hospital ID: Hospital-E
Hospital Name: Central Medical Complex
Bed Capacity: 400 beds
Daily Consumption: ~68 units/day
Product: Physiological Saline Solution 0.9% 500ml (PHYSIO-SALINE-500ML)
Reorder Threshold: 2.0 days


§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Architecture
┌─────────────────────────────────────────────────────────────────┐
│                      Hospital-E System                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐              ┌────────────────┐             │
│  │   StockMS      │              │   OrderMS      │             │
│  │   Port 8081    │              │   Port 8082    │             │
│  │                │              │                │             │
│  │ • Monitor      │              │ • Consume      │             │
│  │ • Alert        │              │   Events       │             │
│  │ • Dual Trigger │              │ • Save Orders  │             │
│  └────────┬───────┘              └───────┬────────┘             │
│           │                              │                       │
│           └──────────┬───────────────────┘                       │
│                      │                                           │
│           ┌──────────▼──────────┐                                │
│           │  PostgreSQL DB      │                                │
│           │  • Stock            │                                │
│           │  • Orders           │                                │
│           │  • EventLog         │                                │
│           │  • Consumption      │                                │
│           │  • Alerts           │                                │
│           └─────────────────────┘                                │
│                                                                   │
└────────┬────────────────────────────────────┬───────────────────┘
         │                                     │
         │ SOA Path (SOAP)                    │ Serverless Path
         │ Synchronous                        │ Asynchronous
         ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Team 1 - Central Warehouse Platform                 │
├─────────────────────────────────────────────────────────────────┤
│  SOAP Services                │  Azure Event Hubs                │
│  • StockUpdateService         │  • inventory-low-events (pub)   │
│  • OrderCreationService       │  • order-commands (sub)          │
└─────────────────────────────────────────────────────────────────┘

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Quick Start

Prerequisites

Docker & Docker Compose (recommended)
OR Python 3.9+ with PostgreSQL
Azure Event Hub credentials (from Team 1)

Option 1: Docker (Recommended)
bash# 1. Clone repository
git clone https://github.com/your-team/hospital-e-supply-chain.git
cd hospital-e-supply-chain

# 2. Create environment file
cp .env.example .env
# Edit .env with your credentials (especially EVENT_HUB_CONNECTION_STRING)

# 3. Start all services
docker-compose up --build

# 4. Verify services are running
curl http://localhost:8081/health  # StockMS
curl http://localhost:8082/health  # OrderMS
Option 2: Local Development
bash# 1. Clone repository
git clone https://github.com/your-team/hospital-e-supply-chain.git
cd hospital-e-supply-chain

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup PostgreSQL database
# Create database: hospital_e_db
psql -U postgres -c "CREATE DATABASE hospital_e_db;"

# 5. Initialize database schema
psql -U postgres -d hospital_e_db -f database/schema.sql
psql -U postgres -d hospital_e_db -f database/init_data.sql

# 6. Create .env file
cp .env.example .env
# Edit .env with your database and Azure credentials

# 7. Run services
# Terminal 1
python services/stock_ms/app.py

# Terminal 2
python services/order_ms/app.py


§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Project Components

1. StockMS (Stock Monitoring Service)
Port: 8081
Responsibilities:

Monitor inventory levels continuously
Calculate days of supply
Detect threshold breaches
Trigger DUAL PATH communication:

Send SOAP request to Team 1
Publish event to Azure Event Hub


Record all events in database

Endpoints:
bashGET  /health                  # Health check
GET  /status                  # Current stock status
POST /trigger                 # Manual stock check
POST /simulate-consumption    # Simulate consumption
GET  /logs                    # Recent event logs
GET  /alerts                  # Unacknowledged alerts
GET  /performance             # Performance statistics
GET  /consumption-history     # Consumption history
Example Usage:
bash# Get current stock status
curl http://localhost:8081/status

# Manually trigger stock check
curl -X POST http://localhost:8081/trigger

# Get performance comparison
curl http://localhost:8081/performance
2. OrderMS (Order Management Service)
Port: 8082
Responsibilities:

Listen to Azure Event Hub order-commands topic
Consume OrderCreationCommand messages
Filter for Hospital-E orders only
Save orders to local database
Provide order management API

Endpoints:
bashGET  /health                 # Health check
GET  /orders                 # Get all orders
GET  /orders/<id>            # Get specific order
PUT  /orders/<id>/status     # Update order status
GET  /orders/pending         # Get pending orders
GET  /orders/stats           # Order statistics
GET  /logs                   # Recent order logs
Example Usage:
bash# Get all pending orders
curl http://localhost:8082/orders/pending

# Get order statistics
curl http://localhost:8082/orders/stats

# Update order status
curl -X PUT http://localhost:8082/orders/ORD-20260109-ABCD1234/status \
  -H "Content-Type: application/json" \
  -d '{"status": "DELIVERED"}'
3. Database Schema
Tables:

Stock: Current inventory levels
Orders: Received supply orders
EventLog: Communication event logs (SOA + Serverless)
ConsumptionHistory: Daily consumption tracking
Alerts: Stock level alerts


§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Workflow

Normal Operation Flow

Stock Monitoring (Every 60 seconds by default):

   StockMS checks current stock
   → Simulates daily consumption
   → Updates database
   → Calculates days of supply

Threshold Breach Detection:

   If days_of_supply < 2.0:
     → Create alert in database
     → Trigger DUAL PATH communication

Dual Path Communication (Both paths run in parallel):

   Path 1 (SOAP):
     → Create StockUpdateRequest
     → Send to Team 1's SOAP endpoint
     → Wait for StockUpdateResponse
     → Log to EventLog (architecture='SOA')
   
   Path 2 (Event Hub):
     → Create InventoryLowEvent (JSON)
     → Publish to Azure Event Hub
     → Log to EventLog (architecture='SERVERLESS')

Order Reception:

   Team 1 processes event
   → Creates OrderCreationCommand
   → Publishes to order-commands Event Hub
   → OrderMS consumes event
   → Filters for Hospital-E orders
   → Saves to Orders table
   → Logs to EventLog
Test Scenarios
The project includes predefined test scenarios from Team 1:
SCEN-001: Normal Replenishment (Hospital-E)
json{
  "current_stock": 136,
  "daily_consumption": 68,
  "days_of_supply": 2.0,
  "expected_priority": "HIGH"
}
SCEN-002: Critical Shortage (Hospital-E)
json{
  "current_stock": 34,
  "daily_consumption": 68,
  "days_of_supply": 0.5,
  "expected_priority": "URGENT"
}

🔌 Integration with Team 1
SOAP Integration
Team 1 SOAP Endpoint:
URL: http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices
WSDL: {URL}?wsdl
StockUpdateRequest (sent by Hospital-E):
xml<tns:StockUpdateRequest>
    <tns:hospitalId>Hospital-E</tns:hospitalId>
    <tns:productCode>PHYSIO-SALINE-500ML</tns:productCode>
    <tns:currentStockUnits>136</tns:currentStockUnits>
    <tns:dailyConsumptionUnits>68</tns:dailyConsumptionUnits>
    <tns:daysOfSupply>2.0</tns:daysOfSupply>
    <tns:timestamp>2026-01-09T10:30:00Z</tns:timestamp>
</tns:StockUpdateRequest>
StockUpdateResponse (received from Team 1):
xml<tns:StockUpdateResponse>
    <tns:success>true</tns:success>
    <tns:message>Order created</tns:message>
    <tns:orderTriggered>true</tns:orderTriggered>
    <tns:orderId>ORD-20260109-ABCD1234</tns:orderId>
</tns:StockUpdateResponse>
Azure Event Hub Integration
Connection String (from Team 1):
Endpoint=sb://medical-supply-chain-ns.servicebus.windows.net/;
SharedAccessKeyName=RootManageSharedAccessKey;
SharedAccessKey=HFDW05QKieWgy3uDKmNHc2OisPdrfNvoy+AEhKCJZlw=
Topics:

Publish to: inventory-low-events (when threshold breached)
Subscribe to: order-commands (receive orders)
Consumer Group: hospital-e-consumer

InventoryLowEvent (published by Hospital-E):
json{
  "eventId": "evt-550e8400-e29b-41d4-a716-446655440000",
  "eventType": "InventoryLow",
  "hospitalId": "Hospital-E",
  "productCode": "PHYSIO-SALINE-500ML",
  "currentStockUnits": 136,
  "dailyConsumptionUnits": 68,
  "daysOfSupply": 2.0,
  "threshold": 2.0,
  "timestamp": "2026-01-09T10:30:00.000Z"
}
OrderCreationCommand (consumed by Hospital-E):
json{
  "commandId": "cmd-550e8400-e29b-41d4-a716-446655440001",
  "commandType": "CreateOrder",
  "orderId": "ORD-20260109-ABCD1234",
  "hospitalId": "Hospital-E",
  "productCode": "PHYSIO-SALINE-500ML",
  "orderQuantity": 340,
  "priority": "HIGH",
  "estimatedDeliveryDate": "2026-01-11T10:00:00.000Z",
  "warehouseId": "CENTRAL-WAREHOUSE",
  "timestamp": "2026-01-09T10:30:00.000Z"
}

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Testing

Run Unit Tests
bashpytest tests/ -v
Test Individual Components
bash# Test SOAP Client
python -c "from services.stock_ms.soap_client import soap_client; soap_client.test_connection()"

# Test Event Producer
python -c "from services.stock_ms.event_producer import event_producer; import asyncio; asyncio.run(event_producer.test_connection())"

# Test Event Consumer
python -c "from services.order_ms.event_consumer import event_consumer; import asyncio; asyncio.run(event_consumer.test_connection())"
Manual End-to-End Test
bash# 1. Start services
docker-compose up

# 2. Check initial stock
curl http://localhost:8081/status

# 3. Simulate consumption to trigger threshold
curl -X POST http://localhost:8081/simulate-consumption

# 4. Check if alert was created
curl http://localhost:8081/alerts

# 5. Check event logs (should see both SOA and SERVERLESS events)
curl http://localhost:8081/logs

# 6. Wait for order (should arrive in OrderMS)
curl http://localhost:8082/orders

# 7. Check performance comparison
curl http://localhost:8081/performance

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Performance Metrics

The system tracks and compares performance between SOA and Serverless architectures:
bashcurl http://localhost:8081/performance
Expected Output:
json{
  "SOA": {
    "total_events": 10,
    "avg_latency": 450.5,
    "min_latency": 200,
    "max_latency": 800,
    "p95_latency": 750
  },
  "SERVERLESS": {
    "total_events": 10,
    "avg_latency": 120.3,
    "min_latency": 50,
    "max_latency": 200,
    "p95_latency": 180
  }
}

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Troubleshooting

Common Issues
1. Database Connection Error
Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
Solution: Ensure PostgreSQL is running and credentials in .env are correct.
2. SOAP Connection Timeout
Error: Connection to SOAP service timed out
Solution: Check if Team 1's SOAP service is accessible. Try:
bashcurl http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices?wsdl
3. Event Hub Authentication Error
Error: Unauthorized. The token has invalid signature
Solution: Verify EVENT_HUB_CONNECTION_STRING in .env is correct and up-to-date.
4. Orders Not Received in OrderMS
OrderMS running but no orders appearing
Solutions:

Verify consumer group exists: hospital-e-consumer
Check if Team 1's Azure Function is processing events
Check OrderMS logs: docker logs hospital_e_order_ms
Ensure correct hospitalId filter (Hospital-E)

5. Docker Container Fails to Start
Error: database system is ready to accept connections
Solution: Wait for database health check to pass (~10 seconds)

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§

Project Structure
hospital-e-supply-chain/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── database/
│   ├── __init__.py
│   ├── schema.sql               # Database schema
│   ├── init_data.sql            # Initial data
│   └── db_manager.py            # Database operations
├── services/
│   ├── stock_ms/
│   │   ├── __init__.py
│   │   ├── app.py               # StockMS Flask app
│   │   ├── stock_monitor.py     # Stock monitoring logic
│   │   ├── soap_client.py       # SOAP client
│   │   └── event_producer.py    # Event Hub producer
│   └── order_ms/
│       ├── __init__.py
│       ├── app.py               # OrderMS Flask app
│       └── event_consumer.py    # Event Hub consumer
├── tests/
│   ├── test_stock_ms.py
│   ├── test_order_ms.py
│   └── test_integration.py
├── docs/
│   ├── architecture.md
│   └── deployment.md
├── docker-compose.yml           # Docker orchestration
├── Dockerfile.stockms           # StockMS container
├── Dockerfile.orderms           # OrderMS container
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore
└── README.md                    # This file

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§
Team Members
Team 6 - Hospital-E

Alp Karaman
Ruken Yıldız
Ece Oğuzbal
Ilgın Dursun
Tuğçe Akay

§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§

ACK

Team 1 (Central Warehouse) for providing integration contracts and infrastructure
Course instructor and TAs for project guidance


§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§