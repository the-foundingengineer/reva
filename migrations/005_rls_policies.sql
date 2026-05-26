-- Enable RLS on all core tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE developments ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs ENABLE ROW LEVEL SECURITY;

-- 1. Tenants can only see their own record
CREATE POLICY tenant_isolation ON tenants
    FOR ALL USING (id = current_setting('app.current_tenant_id')::uuid);

-- 2. Developments isolation
CREATE POLICY development_isolation ON developments
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 3. Properties isolation
CREATE POLICY property_isolation ON properties
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 4. Agents isolation
CREATE POLICY agent_isolation ON agents
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 5. Leads isolation
CREATE POLICY lead_isolation ON leads
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 6. Conversation Logs isolation
CREATE POLICY log_isolation ON conversation_logs
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
