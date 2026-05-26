# Reva

AI sales engine for Nigerian real estate developers — WhatsApp qualification, live inventory matching, and site-visit booking.

## Quick start

### One-Command Start (Recommended)
If you are on Windows, you can start the entire stack (Evolution API + Reva Engine) with:
```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

### Manual Setup
1. Copy `.env.example` → `.env` and fill in Supabase, Redis, LLM, and Calendly vars.
2. **Inventory setup** (pick one):

   ```bash
   python scripts/setup_inventory.py
   ```

   Or manually: run `migrations/001_inventory.sql` in Supabase SQL editor, then `python scripts/seed_inventory.py`.

   Optional: set `SUPABASE_DB_PASSWORD` in `.env` so `scripts/apply_migration.py` runs SQL for you.

4. Start the API:

   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

5. Run the WhatsApp simulator:

   ```bash
   python tests/simulate_webhook.py
   ```

## Mock developer inventory

**Atlantic Horizons Developments** — 4 Lagos projects, 16+ available units:

| Project | Location | Price range |
|---------|----------|-------------|
| Horizon Terraces (Phase 3) | Ikoyi | ₦78M – ₦320M |
| Marina View Residences | Victoria Island | ₦52M – ₦175M |
| GreenPark Estate | Sangotedo, Ajah | ₦18M – ₦68M |
| Lekki Skies | Ibeju-Lekki | ₦28M – ₦45M |

When a lead is fully qualified, Reva sends the top 3 matching units from this inventory, then a Calendly booking link (if `CALENDLY_EVENT_URL` is set).

## API

- `GET /dashboard` — live pipeline UI
- `GET /api/units` — available inventory
- `POST /api/inventory/match` — preview matches for a profile
- `GET /api/leads/{phone}/matches` — units offered to a lead

## Lead source tags (WhatsApp)

Prefix the first message: `[source:facebook_ad] Hi, I'm interested`
