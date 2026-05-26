-- Update developments table with price ranges
ALTER TABLE developments ADD COLUMN IF NOT EXISTS price_min NUMERIC;
ALTER TABLE developments ADD COLUMN IF NOT EXISTS price_max NUMERIC;
ALTER TABLE developments ADD COLUMN IF NOT EXISTS available_types TEXT[]; -- e.g. ['apartment', 'duplex']

-- Update existing developments with sample data
UPDATE developments SET 
    price_min = 120000000, 
    price_max = 450000000, 
    available_types = ARRAY['apartment', 'penthouse'] 
WHERE name = 'Horizon Terraces';

UPDATE developments SET 
    price_min = 95000000, 
    price_max = 280000000, 
    available_types = ARRAY['apartment'] 
WHERE name = 'Marina View Residences';

UPDATE developments SET 
    price_min = 15000000, 
    price_max = 45000000, 
    available_types = ARRAY['apartment', 'terrace'] 
WHERE name = 'GreenPark Estate';

UPDATE developments SET 
    price_min = 8000000, 
    price_max = 25000000, 
    available_types = ARRAY['land', 'apartment'] 
WHERE name = 'Lekki Skies';
