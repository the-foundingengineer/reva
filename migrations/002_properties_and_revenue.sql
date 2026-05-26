-- Properties Table
CREATE TABLE IF NOT EXISTS properties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,           -- apartment, duplex, land, commercial
    location TEXT NOT NULL,       -- Ajah, Lekki, VI, Ibeju-Lekki etc
    bedrooms INTEGER,
    bathrooms INTEGER,
    price NUMERIC NOT NULL,
    highlights TEXT,              -- "Swimming pool, 24hr security, BQ"
    images TEXT[],                -- Array of image URLs
    available BOOLEAN DEFAULT TRUE,
    payment_plan BOOLEAN DEFAULT FALSE,
    payment_plan_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed with realistic data
INSERT INTO properties (name, type, location, bedrooms, bathrooms, price, highlights, available, payment_plan, payment_plan_details) VALUES
('Lekki Gardens Phase 2', 'apartment', 'Lekki', 2, 2, 14500000, 'Swimming pool, 24hr security, fitted kitchen, estate', true, true, '30% upfront, balance over 12 months'),
('Atlantic View Apartments', 'apartment', 'Lekki', 2, 2, 16000000, 'Ocean view, gym, parking, backup power', true, false, null),
('Lekki Luxury Duplex', 'duplex', 'Lekki', 3, 3, 28000000, 'Private compound, boys quarter, 3 car garage', true, true, '40% upfront, balance over 18 months'),
('Sangotedo Court', 'apartment', 'Sangotedo', 2, 2, 12000000, 'Gated estate, backup power, security', true, false, null),
('Ajah Premier Flats', 'apartment', 'Ajah', 2, 2, 9500000, 'Tile floors, POP ceiling, close to highway', true, true, '25% upfront, balance over 12 months'),
('VI Executive Suite', 'apartment', 'Victoria Island', 2, 2, 45000000, 'Fully serviced, concierge, rooftop', true, false, null),
('Ibeju-Lekki Estate', 'land', 'Ibeju-Lekki', null, null, 8000000, 'C of O, dry land, gated estate', true, true, '50% upfront, balance over 6 months')
ON CONFLICT DO NOTHING;

-- Projected revenue view
CREATE OR REPLACE VIEW revenue_projection AS
SELECT
    COUNT(*) FILTER (WHERE stage = 'qualified') as hot_pipeline,
    COUNT(*) FILTER (WHERE stage = 'done') as meetings_booked,
    COUNT(*) FILTER (WHERE meeting_booked = true) as conversions,
    AVG(seriousness_score) as avg_lead_quality,
    -- Assume 20% of meetings convert at average unit price
    COUNT(*) FILTER (WHERE meeting_booked = true) * 0.20 * 15000000
        as projected_revenue_naira
FROM leads
WHERE created_at > NOW() - INTERVAL '30 days';
