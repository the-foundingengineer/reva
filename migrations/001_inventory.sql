-- Reva inventory schema (run in Supabase SQL editor)
-- Mock developer: Atlantic Horizons Developments

-- ─── Developer ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS developers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    tagline     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── Developments (projects / phases) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS developments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id    UUID NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    phase           TEXT,
    location        TEXT NOT NULL,
    area_tags       TEXT[] NOT NULL DEFAULT '{}',
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_developments_area_tags ON developments USING GIN (area_tags);

-- ─── Units (sellable inventory) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS units (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    development_id      UUID NOT NULL REFERENCES developments(id) ON DELETE CASCADE,
    unit_code           TEXT NOT NULL,
    title               TEXT NOT NULL,
    property_type       TEXT NOT NULL,
    bedrooms            INT,
    price_naira         BIGINT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'available'
                            CHECK (status IN ('available', 'reserved', 'sold')),
    size_sqm            INT,
    highlights          TEXT,
    payment_plan_notes  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (development_id, unit_code)
);

CREATE INDEX IF NOT EXISTS idx_units_status ON units (status);
CREATE INDEX IF NOT EXISTS idx_units_price ON units (price_naira);

-- ─── Which units Reva offered each lead ────────────────────────────────────
CREATE TABLE IF NOT EXISTS lead_unit_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number    TEXT NOT NULL,
    unit_id         UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    match_score     REAL NOT NULL DEFAULT 0,
    rank            INT NOT NULL DEFAULT 1,
    offered_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lead_unit_matches_phone ON lead_unit_matches (phone_number);

-- ─── Lead extensions ───────────────────────────────────────────────────────
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'whatsapp_organic';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS first_response_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualified_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm_campaign TEXT;
