-- 1. Create Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create Developments Table (Multi-property support)
CREATE TABLE IF NOT EXISTS developments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    min_price NUMERIC,
    max_price NUMERIC,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Update Properties Table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE properties ADD COLUMN IF NOT EXISTS development_id UUID REFERENCES developments(id);

-- 4. Update Agents Table
-- Assuming an 'agents' table exists or will be created
CREATE TABLE IF NOT EXISTS agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    full_name TEXT NOT NULL,
    whatsapp_number TEXT NOT NULL UNIQUE,
    email TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Junction Table for Agents and Developments
CREATE TABLE IF NOT EXISTS agent_developments (
    agent_id UUID REFERENCES agents(id),
    development_id UUID REFERENCES developments(id),
    PRIMARY KEY (agent_id, development_id)
);

-- 6. Update Leads Table for Multi-tenancy and attribution
ALTER TABLE leads ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS development_id UUID REFERENCES developments(id);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS attribution TEXT DEFAULT 'reva'; -- 'reva', 'walk-in', 'referral'
ALTER TABLE leads ADD COLUMN IF NOT EXISTS closing_revenue NUMERIC;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_paused BOOLEAN DEFAULT FALSE;

-- 7. Update Conversation Logs for Multi-tenancy
ALTER TABLE conversation_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

-- 8. Row Level Security (RLS)
-- Enable RLS on all tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE developments ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs ENABLE ROW LEVEL SECURITY;

-- 9. Revenue Projection View
CREATE OR REPLACE VIEW revenue_intelligence AS
SELECT 
    tenant_id,
    COUNT(*) FILTER (WHERE stage = 'qualified') as hot_pipeline,
    COUNT(*) FILTER (WHERE stage = 'confirmed') as meetings_booked,
    COUNT(*) FILTER (WHERE stage = 'closed') as conversions,
    AVG(seriousness_score) as avg_lead_quality,
    SUM(closing_revenue) as actual_revenue,
    -- Projected: 20% of qualified leads convert at 15M avg if revenue not set
    COALESCE(SUM(closing_revenue), 0) + 
    (COUNT(*) FILTER (WHERE stage = 'qualified' AND closing_revenue IS NULL) * 0.20 * 15000000)
        as projected_revenue_naira
FROM leads
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY tenant_id;
