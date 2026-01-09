-- ============================================
-- Hospital-E Database Schema
-- PostgreSQL Schema for Team 6
-- ============================================

-- Drop existing types if they exist
DROP TYPE IF EXISTS event_type_enum CASCADE;
DROP TYPE IF EXISTS architecture_enum CASCADE;
DROP TYPE IF EXISTS log_status_enum CASCADE;
DROP TYPE IF EXISTS order_status_enum CASCADE;
DROP TYPE IF EXISTS priority_enum CASCADE;
DROP TYPE IF EXISTS alert_type_enum CASCADE;
DROP TYPE IF EXISTS severity_enum CASCADE;

-- Create ENUM types
CREATE TYPE event_type_enum AS ENUM (
    'STOCK_UPDATE_SENT',
    'INVENTORY_EVENT_PUBLISHED',
    'ORDER_RECEIVED'
);

CREATE TYPE architecture_enum AS ENUM ('SOA', 'SERVERLESS');
CREATE TYPE log_status_enum AS ENUM ('SUCCESS', 'FAILURE', 'TIMEOUT', 'RETRY');
CREATE TYPE order_status_enum AS ENUM ('PENDING', 'RECEIVED', 'DELIVERED', 'CANCELLED');
CREATE TYPE priority_enum AS ENUM ('URGENT', 'HIGH', 'NORMAL');
CREATE TYPE alert_type_enum AS ENUM ('LOW_STOCK', 'CRITICAL_STOCK', 'OUT_OF_STOCK');
CREATE TYPE severity_enum AS ENUM ('NORMAL', 'HIGH', 'URGENT');

-- ============================================
-- Table: Stock
-- Tracks current inventory levels
-- ============================================
CREATE TABLE Stock (
    stock_id SERIAL PRIMARY KEY,
    hospital_id VARCHAR(50) NOT NULL DEFAULT 'Hospital-E',
    product_code VARCHAR(100) NOT NULL,
    current_stock_units INTEGER NOT NULL CHECK (current_stock_units >= 0),
    daily_consumption_units INTEGER NOT NULL CHECK (daily_consumption_units >= 0),
    days_of_supply DECIMAL(10, 2) NOT NULL CHECK (days_of_supply >= 0),
    reorder_threshold DECIMAL(10, 2) NOT NULL DEFAULT 2.0,
    max_stock_level INTEGER NOT NULL DEFAULT 680,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(hospital_id, product_code)
);

CREATE INDEX idx_stock_hospital_product ON Stock(hospital_id, product_code);
CREATE INDEX idx_stock_days_of_supply ON Stock(days_of_supply);

-- ============================================
-- Table: Orders
-- Stores received supply orders
-- ============================================
CREATE TABLE Orders (
    order_id VARCHAR(100) PRIMARY KEY,
    command_id VARCHAR(100) UNIQUE NOT NULL,
    hospital_id VARCHAR(50) NOT NULL DEFAULT 'Hospital-E',
    product_code VARCHAR(100) NOT NULL,
    order_quantity INTEGER NOT NULL CHECK (order_quantity > 0),
    priority priority_enum NOT NULL DEFAULT 'NORMAL',
    order_status order_status_enum NOT NULL DEFAULT 'PENDING',
    estimated_delivery_date TIMESTAMP WITH TIME ZONE,
    actual_delivery_date TIMESTAMP WITH TIME ZONE,
    warehouse_id VARCHAR(50) DEFAULT 'CENTRAL-WAREHOUSE',
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_hospital ON Orders(hospital_id);
CREATE INDEX idx_orders_status ON Orders(order_status);
CREATE INDEX idx_orders_priority ON Orders(priority);
CREATE INDEX idx_orders_received_at ON Orders(received_at DESC);

-- ============================================
-- Table: EventLog
-- Logs all communication events
-- ============================================
CREATE TABLE EventLog (
    log_id SERIAL PRIMARY KEY,
    event_type event_type_enum NOT NULL,
    direction VARCHAR(20) NOT NULL, -- 'OUTGOING' or 'INCOMING'
    architecture architecture_enum NOT NULL,
    payload TEXT,
    status log_status_enum NOT NULL,
    error_message TEXT,
    latency_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eventlog_timestamp ON EventLog(timestamp DESC);
CREATE INDEX idx_eventlog_type ON EventLog(event_type);
CREATE INDEX idx_eventlog_status ON EventLog(status);
CREATE INDEX idx_eventlog_architecture ON EventLog(architecture);

-- ============================================
-- Table: ConsumptionHistory
-- Tracks daily consumption patterns
-- ============================================
CREATE TABLE ConsumptionHistory (
    consumption_id SERIAL PRIMARY KEY,
    hospital_id VARCHAR(50) NOT NULL DEFAULT 'Hospital-E',
    product_code VARCHAR(100) NOT NULL,
    consumption_date DATE NOT NULL,
    units_consumed INTEGER NOT NULL CHECK (units_consumed >= 0),
    opening_stock INTEGER NOT NULL,
    closing_stock INTEGER NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(hospital_id, product_code, consumption_date)
);

CREATE INDEX idx_consumption_date ON ConsumptionHistory(consumption_date DESC);
CREATE INDEX idx_consumption_hospital_product ON ConsumptionHistory(hospital_id, product_code);

-- ============================================
-- Table: Alerts
-- Tracks stock alerts and their resolution
-- ============================================
CREATE TABLE Alerts (
    alert_id SERIAL PRIMARY KEY,
    hospital_id VARCHAR(50) NOT NULL DEFAULT 'Hospital-E',
    alert_type alert_type_enum NOT NULL,
    severity severity_enum NOT NULL,
    current_stock INTEGER NOT NULL,
    daily_consumption INTEGER NOT NULL,
    days_of_supply DECIMAL(10, 2) NOT NULL,
    threshold DECIMAL(10, 2) NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_created_at ON Alerts(created_at DESC);
CREATE INDEX idx_alerts_acknowledged ON Alerts(acknowledged);
CREATE INDEX idx_alerts_severity ON Alerts(severity);

-- ============================================
-- Trigger: Update last_updated on Stock changes
-- ============================================
CREATE OR REPLACE FUNCTION update_stock_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_stock_timestamp
    BEFORE UPDATE ON Stock
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_timestamp();

-- ============================================
-- Views for Reporting
-- ============================================

-- View: Current Stock Status
CREATE VIEW vw_current_stock_status AS
SELECT 
    stock_id,
    hospital_id,
    product_code,
    current_stock_units,
    daily_consumption_units,
    days_of_supply,
    reorder_threshold,
    CASE 
        WHEN days_of_supply < 1.0 THEN 'CRITICAL'
        WHEN days_of_supply < reorder_threshold THEN 'LOW'
        ELSE 'ADEQUATE'
    END as stock_status,
    last_updated
FROM Stock;

-- View: Recent Orders Summary
CREATE VIEW vw_recent_orders AS
SELECT 
    order_id,
    product_code,
    order_quantity,
    priority,
    order_status,
    estimated_delivery_date,
    received_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - received_at))/3600 as hours_since_received
FROM Orders
ORDER BY received_at DESC
LIMIT 50;

-- View: Communication Performance
CREATE VIEW vw_communication_performance AS
SELECT 
    architecture,
    status,
    COUNT(*) as event_count,
    AVG(latency_ms) as avg_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms
FROM EventLog
WHERE latency_ms IS NOT NULL
GROUP BY architecture, status;

-- ============================================
-- Initial Data Setup
-- ============================================
COMMENT ON TABLE Stock IS 'Current inventory levels for Hospital-E';
COMMENT ON TABLE Orders IS 'Received supply orders from central warehouse';
COMMENT ON TABLE EventLog IS 'Communication event logs for both SOA and Serverless paths';
COMMENT ON TABLE ConsumptionHistory IS 'Historical daily consumption tracking';
COMMENT ON TABLE Alerts IS 'Stock level alerts and their resolution status';