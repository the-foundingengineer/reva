-- 006_unified_inventory_fts.sql
-- Creates a unified view of all available inventory and a Full-Text Search RPC endpoint

CREATE OR REPLACE VIEW v_available_inventory AS
SELECT 
    id,
    name as title,
    location,
    type as property_type,
    bedrooms,
    price as price_naira,
    highlights,
    'properties' as source_table
FROM properties
WHERE available = true

UNION ALL

SELECT 
    u.id,
    dev.name || ' - ' || u.title as title,
    dev.location,
    u.property_type,
    u.bedrooms,
    u.price_naira,
    u.highlights,
    'units' as source_table
FROM units u
JOIN developments dev ON u.development_id = dev.id
WHERE u.status = 'available'

UNION ALL

SELECT 
    id,
    name as title,
    location,
    array_to_string(available_types, ', ') as property_type,
    NULL::integer as bedrooms,
    price_min as price_naira,
    description as highlights,
    'developments' as source_table
FROM developments
WHERE price_min IS NOT NULL;

-- Drop existing if any changes to signature
DROP FUNCTION IF EXISTS search_inventory_fts(text, numeric, integer);

-- Create an RPC to search against this view using Postgres FTS
CREATE OR REPLACE FUNCTION search_inventory_fts(
    search_query TEXT,
    max_budget NUMERIC DEFAULT NULL,
    target_bedrooms INTEGER DEFAULT NULL
) 
RETURNS TABLE (
    id UUID,
    name TEXT,
    location TEXT,
    property_type TEXT,
    bedrooms INTEGER,
    price NUMERIC,
    highlights TEXT,
    source TEXT,
    rank REAL
) AS $$
DECLARE
    formatted_query tsquery;
    budget_stretch NUMERIC;
BEGIN
    -- Format query for FTS (e.g., "lekki apartment" -> "lekki" & "apartment")
    -- We use plainto_tsquery to safely handle user input
    formatted_query := plainto_tsquery('english', COALESCE(search_query, ''));
    
    -- Allow a 20% stretch on the budget (industry standard fuzziness)
    IF max_budget IS NOT NULL THEN
        budget_stretch := max_budget * 1.2;
    END IF;

    RETURN QUERY
    SELECT 
        v.id,
        v.title as name,
        v.location,
        v.property_type,
        v.bedrooms,
        v.price_naira as price,
        v.highlights,
        v.source_table as source,
        CASE 
            WHEN formatted_query::text = '' THEN 1.0::REAL
            ELSE ts_rank(
                setweight(to_tsvector('english', COALESCE(v.location, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(v.property_type, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(v.title, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(v.highlights, '')), 'C'),
                formatted_query
            )::REAL 
        END as rank
    FROM v_available_inventory v
    WHERE 
        (max_budget IS NULL OR v.price_naira <= budget_stretch) AND
        (target_bedrooms IS NULL OR v.bedrooms = target_bedrooms OR v.bedrooms IS NULL) AND
        (formatted_query::text = '' OR (
            setweight(to_tsvector('english', COALESCE(v.location, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(v.property_type, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(v.title, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(v.highlights, '')), 'C')
        ) @@ formatted_query)
    ORDER BY 
        rank DESC, 
        (CASE WHEN max_budget IS NOT NULL THEN abs(v.price_naira - max_budget) ELSE v.price_naira END) ASC
    LIMIT 3;
END;
$$ LANGUAGE plpgsql;
