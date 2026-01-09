-- ============================================
-- Hospital-E Initial Data
-- Initialize stock with Hospital-E specific values
-- ============================================

-- Insert initial stock for Hospital-E
INSERT INTO Stock (
    hospital_id,
    product_code,
    current_stock_units,
    daily_consumption_units,
    days_of_supply,
    reorder_threshold,
    max_stock_level
) VALUES (
    'Hospital-E',
    'PHYSIO-SALINE-500ML',
    200,                    -- Initial stock: 200 units
    68,                     -- Daily consumption: 68 units/day (from project requirements)
    ROUND(200.0 / 68, 2),   -- Days of supply: ~2.94 days
    2.0,                    -- Reorder threshold: 2 days
    680                     -- Max stock: 10 days supply (68 * 10)
) ON CONFLICT (hospital_id, product_code) DO NOTHING;

-- Insert sample consumption history (last 7 days)
INSERT INTO ConsumptionHistory (
    hospital_id,
    product_code,
    consumption_date,
    units_consumed,
    opening_stock,
    closing_stock,
    day_of_week,
    is_weekend,
    notes
) VALUES
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '7 days', 65, 465, 400, 'Monday', false, 'Historical data'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '6 days', 70, 400, 330, 'Tuesday', false, 'Historical data'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '5 days', 68, 330, 262, 'Wednesday', false, 'Historical data'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '4 days', 72, 262, 190, 'Thursday', false, 'Historical data'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '3 days', 55, 190, 135, 'Friday', false, 'Historical data'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '2 days', 50, 135, 85, 'Saturday', true, 'Weekend - lower consumption'),
    ('Hospital-E', 'PHYSIO-SALINE-500ML', CURRENT_DATE - INTERVAL '1 day', 45, 85, 40, 'Sunday', true, 'Weekend - lower consumption')
ON CONFLICT (hospital_id, product_code, consumption_date) DO NOTHING;

-- Verify data was inserted
DO $$
DECLARE
    stock_count INTEGER;
    consumption_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO stock_count FROM Stock WHERE hospital_id = 'Hospital-E';
    SELECT COUNT(*) INTO consumption_count FROM ConsumptionHistory WHERE hospital_id = 'Hospital-E';
    
    RAISE NOTICE 'Initial data loaded:';
    RAISE NOTICE '  Stock entries: %', stock_count;
    RAISE NOTICE '  Consumption history: %', consumption_count;
END $$;