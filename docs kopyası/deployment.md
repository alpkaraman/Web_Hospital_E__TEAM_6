# Hospital-E Deployment Guide

Complete guide for deploying the Hospital-E Supply Chain Management System.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Azure Container Apps Deployment](#azure-container-apps-deployment)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 15 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Step-by-Step Setup

#### 1. Clone Repository

```bash
git clone https://github.com/your-team/hospital-e-supply-chain.git
cd hospital-e-supply-chain
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup PostgreSQL Database

```bash
# Create database
psql -U postgres -c "CREATE DATABASE hospital_e_db;"

# Run schema script
psql -U postgres -d hospital_e_db -f database/schema.sql

# Load initial data
psql -U postgres -d hospital_e_db -f database/init_data.sql
```

#### 5. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required environment variables:**

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hospital_e_db
DB_USER=postgres
DB_PASSWORD=your_password

# Azure Event Hub (Get from Team 1)
EVENT_HUB_CONNECTION_STRING=Endpoint=sb://...
```

#### 6. Run Services

```bash
# Terminal 1 - Start StockMS
python services/stock_ms/app.py

# Terminal 2 - Start OrderMS
python services/order_ms/app.py
```

#### 7. Verify Installation

```bash
# Check StockMS
curl http://localhost:8081/health

# Check OrderMS
curl http://localhost:8082/health

# Get stock status
curl http://localhost:8081/status
```

---

## Docker Deployment

### Prerequisites

- Docker 20.10 or higher
- Docker Compose 2.0 or higher

### Quick Start with Docker

#### 1. Clone Repository

```bash
git clone https://github.com/your-team/hospital-e-supply-chain.git
cd hospital-e-supply-chain
```

#### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure Event Hub credentials
```

#### 3. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

#### 4. Verify Services

```bash
# Check running containers
docker-compose ps

# Check logs
docker-compose logs stock-ms
docker-compose logs order-ms

# Test endpoints
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart stock-ms

# Rebuild specific service
docker-compose up --build stock-ms

# Access database
docker-compose exec database psql -U postgres -d hospital_e_db

# Execute command in container
docker-compose exec stock-ms python -c "from database.db_manager import db; print(db.get_current_stock())"
```

### Docker Troubleshooting

**Issue**: Containers fail to start
```bash
# Check logs
docker-compose logs

# Remove volumes and rebuild
docker-compose down -v
docker-compose up --build
```

**Issue**: Database connection errors
```bash
# Restart database
docker-compose restart database

# Check database health
docker-compose exec database pg_isready -U postgres
```

---

## Azure Container Apps Deployment

### Prerequisites

- Azure account with active subscription
- Azure CLI installed
- Docker images built

### Step 1: Prepare Azure Resources

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name rg-hospital-e \
  --location westeurope

# Create Container Registry
az acr create \
  --resource-group rg-hospital-e \
  --name hospitaleregistr \
  --sku Basic

# Login to Container Registry
az acr login --name hospitaleregistry
```

### Step 2: Build and Push Docker Images

```bash
# Build images
docker build -f Dockerfile.stockms -t hospitaleregistry.azurecr.io/stock-ms:v1 .
docker build -f Dockerfile.orderms -t hospitaleregistry.azurecr.io/order-ms:v1 .

# Push images
docker push hospitaleregistry.azurecr.io/stock-ms:v1
docker push hospitaleregistry.azurecr.io/order-ms:v1
```

### Step 3: Create Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group rg-hospital-e \
  --name hospital-e-db-server \
  --location westeurope \
  --admin-user adminuser \
  --admin-password <YourStrongPassword> \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 15

# Create database
az postgres flexible-server db create \
  --resource-group rg-hospital-e \
  --server-name hospital-e-db-server \
  --database-name hospital_e_db

# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group rg-hospital-e \
  --name hospital-e-db-server \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Step 4: Initialize Database Schema

```bash
# Connect to database
psql "host=hospital-e-db-server.postgres.database.azure.com port=5432 dbname=hospital_e_db user=adminuser password=<YourPassword> sslmode=require"

# Run schema script
\i database/schema.sql
\i database/init_data.sql
\q
```

### Step 5: Create Container Apps Environment

```bash
# Create Container Apps environment
az containerapp env create \
  --name hospital-e-env \
  --resource-group rg-hospital-e \
  --location westeurope
```

### Step 6: Deploy StockMS Container App

```bash
az containerapp create \
  --name stock-ms \
  --resource-group rg-hospital-e \
  --environment hospital-e-env \
  --image hospitaleregistry.azurecr.io/stock-ms:v1 \
  --target-port 8081 \
  --ingress external \
  --registry-server hospitaleregistry.azurecr.io \
  --env-vars \
    DB_HOST=hospital-e-db-server.postgres.database.azure.com \
    DB_PORT=5432 \
    DB_NAME=hospital_e_db \
    DB_USER=adminuser \
    DB_PASSWORD=<YourPassword> \
    EVENT_HUB_CONNECTION_STRING="<YourEventHubConnectionString>" \
  --cpu 0.5 \
  --memory 1.0Gi
```

### Step 7: Deploy OrderMS Container App

```bash
az containerapp create \
  --name order-ms \
  --resource-group rg-hospital-e \
  --environment hospital-e-env \
  --image hospitaleregistry.azurecr.io/order-ms:v1 \
  --target-port 8082 \
  --ingress external \
  --registry-server hospitaleregistry.azurecr.io \
  --env-vars \
    DB_HOST=hospital-e-db-server.postgres.database.azure.com \
    DB_PORT=5432 \
    DB_NAME=hospital_e_db \
    DB_USER=adminuser \
    DB_PASSWORD=<YourPassword> \
    EVENT_HUB_CONNECTION_STRING="<YourEventHubConnectionString>" \
    EVENT_HUB_CONSUMER_GROUP=hospital-e-consumer \
  --cpu 0.5 \
  --memory 1.0Gi
```

### Step 8: Verify Deployment

```bash
# Get application URLs
az containerapp show \
  --name stock-ms \
  --resource-group rg-hospital-e \
  --query properties.configuration.ingress.fqdn

az containerapp show \
  --name order-ms \
  --resource-group rg-hospital-e \
  --query properties.configuration.ingress.fqdn

# Test endpoints
curl https://<stock-ms-url>/health
curl https://<order-ms-url>/health
```

---

## Database Setup

### Schema Overview

The database consists of 5 main tables:

1. **Stock**: Current inventory levels
2. **Orders**: Received supply orders
3. **EventLog**: Communication event logs
4. **ConsumptionHistory**: Daily consumption tracking
5. **Alerts**: Stock level alerts

### Manual Schema Creation

```sql
-- Connect to database
psql -U postgres -d hospital_e_db

-- Run schema
\i database/schema.sql

-- Load initial data
\i database/init_data.sql

-- Verify tables
\dt

-- Check initial stock
SELECT * FROM Stock;
```

### Database Backup

```bash
# Create backup
pg_dump -U postgres -d hospital_e_db > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U postgres -d hospital_e_db < backup_20260109.sql
```

---

## Configuration

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | Database host | localhost | Yes |
| `DB_PORT` | Database port | 5432 | Yes |
| `DB_NAME` | Database name | hospital_e_db | Yes |
| `DB_USER` | Database user | postgres | Yes |
| `DB_PASSWORD` | Database password | - | Yes |
| `SOAP_WSDL_URL` | Team 1 SOAP WSDL | Team 1 URL | Yes |
| `SOAP_ENDPOINT` | Team 1 SOAP endpoint | Team 1 URL | Yes |
| `EVENT_HUB_CONNECTION_STRING` | Azure Event Hub connection | - | Yes |
| `EVENT_HUB_INVENTORY_TOPIC` | Inventory topic name | inventory-low-events | Yes |
| `EVENT_HUB_ORDER_TOPIC` | Order topic name | order-commands | Yes |
| `EVENT_HUB_CONSUMER_GROUP` | Consumer group | hospital-e-consumer | Yes |
| `STOCK_MS_PORT` | StockMS port | 8081 | No |
| `ORDER_MS_PORT` | OrderMS port | 8082 | No |
| `STOCK_CHECK_INTERVAL` | Check interval (seconds) | 60 | No |
| `LOG_LEVEL` | Logging level | INFO | No |

### Security Best Practices

1. **Never commit `.env` file** to Git
2. **Use strong database passwords**
3. **Rotate Azure Event Hub keys regularly**
4. **Use Azure Key Vault** for production secrets
5. **Enable SSL/TLS** for database connections
6. **Restrict network access** using firewall rules

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env`
- Test connection: `psql -h localhost -U postgres -d hospital_e_db`
- Check firewall rules

#### 2. Azure Event Hub Authentication Error

**Symptoms**: `Unauthorized: The token has an invalid signature`

**Solutions**:
- Verify `EVENT_HUB_CONNECTION_STRING` is correct
- Check connection string format
- Ensure no extra spaces or newlines
- Request new connection string from Team 1

#### 3. SOAP Connection Timeout

**Symptoms**: `zeep.exceptions.TransportError: HTTPConnectionPool timeout`

**Solutions**:
- Verify Team 1's SOAP service is running
- Test endpoint: `curl <SOAP_ENDPOINT>?wsdl`
- Check network connectivity
- Increase timeout in settings

#### 4. Port Already in Use

**Symptoms**: `OSError: [Errno 98] Address already in use`

**Solutions**:
```bash
# Find process using port
lsof -i :8081

# Kill process
kill -9 <PID>

# Or change port in .env
STOCK_MS_PORT=8091
```

#### 5. Docker Container Crashes

**Symptoms**: Container keeps restarting

**Solutions**:
```bash
# Check logs
docker-compose logs stock-ms

# Check container status
docker-compose ps

# Rebuild container
docker-compose up --build stock-ms
```

### Logging

#### View Application Logs

```bash
# Docker
docker-compose logs -f stock-ms
docker-compose logs -f order-ms

# Local
tail -f logs/hospital_e.log
```

#### Increase Log Verbosity

```bash
# Set in .env
LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# StockMS health
curl http://localhost:8081/health

# OrderMS health
curl http://localhost:8082/health

# Database health
docker-compose exec database pg_isready -U postgres
```

---

## Maintenance

### Regular Tasks

1. **Monitor disk space** for database
2. **Review logs** for errors
3. **Check performance metrics**
4. **Update dependencies** regularly
5. **Backup database** daily

### Database Maintenance

```sql
-- Vacuum database
VACUUM ANALYZE;

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables
WHERE schemaname = 'public';

-- Clean old logs (keep last 30 days)
DELETE FROM EventLog 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

---

## Support

For deployment issues:
1. Check this guide thoroughly
2. Review application logs
3. Contact team members
4. Reach out to Team 1 for integration issues

---

**Last Updated**: January 9, 2026