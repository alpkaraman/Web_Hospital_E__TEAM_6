## Architecture Overview §§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§

```
┌─────────────────────────────────────────────────────────────┐
│                      Hospital-E System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  StockMS     │         │  OrderMS     │                  │
│  │  (Port 8081) │         │  (Port 8082) │                  │
│  └──────┬───────┘         └───────┬──────┘                  │
│         │                         │                          │
│         │        ┌────────────────┤                          │
│         │        │                │                          │
│         ▼        ▼                ▼                          │
│  ┌─────────────────────────────────────┐                    │
│  │     PostgreSQL Database             │                    │
│  │  (Stock, Orders, EventLog, Alerts)  │                    │
│  └─────────────────────────────────────┘                    │
│                                                               │
└───────┬───────────────────────────────────┬─────────────────┘
        │                                   │
        │ SOA Path (SOAP)                   │ Serverless Path
        │                                   │ (Event Hubs)
        ▼                                   ▼
┌───────────────────────────────────────────────────────────┐
│              Team 1 - Central Warehouse                    │
├───────────────────────────────────────────────────────────┤
│  SOAP Endpoint         │  Azure Event Hubs                │
│  StockUpdateService    │  inventory-low-events (pub)      │
│  OrderCreationService  │  order-commands (sub)            │
└───────────────────────────────────────────────────────────┘
```

## Components §§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§

### 1. StockMS (Stock Microservice)
- Monitors inventory levels
- Calculates days of supply
- Triggers alerts when threshold breached
- **Dual Path Communication:**
  - Sends SOAP requests to Team 1
  - Publishes events to Azure Event Hub

### 2. OrderMS (Order Microservice)
- Listens to Azure Event Hub `order-commands` topic
- Consumes `OrderCreationCommand` messages
- Filters for Hospital-E orders only
- Saves orders to local database

### 3. Database
- PostgreSQL with 5 main tables
- Tracks stock, orders, events, consumption, alerts

## Technology Stack
- **Language**: Python 3.9+
- **Web Framework**: Flask
- **SOAP Client**: Zeep
- **Event Hub**: azure-eventhub
- **Database**: PostgreSQL (psycopg2)
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest

## Integration Points §§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§

### Team 1 SOAP Endpoint
```
URL: http://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices
WSDL: {URL}?wsdl
```

### Azure Event Hub
```
Namespace: medical-supply-chain-ns.servicebus.windows.net
Input Topic: inventory-low-events (we publish)
Output Topic: order-commands (we consume)
Consumer Group: hospital-e-consumer
```
# §§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§