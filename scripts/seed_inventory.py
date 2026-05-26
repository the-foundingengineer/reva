#!/usr/bin/env python3
"""
Seed Atlantic Horizons mock inventory into Supabase.

Prerequisites:
  migrations/001_inventory.sql applied (or run scripts/setup_inventory.py)

Usage:
  python scripts/seed_inventory.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.data.catalog import DEVELOPER, DEVELOPMENTS, UNITS  # noqa: E402
from app.db.supabase import get_supabase  # noqa: E402


def main() -> None:
    db = get_supabase()

    try:
        db.table("developers").select("id").limit(1).execute()
    except Exception as exc:
        print(
            "\nERROR: Inventory tables not found.\n"
            "Run migrations/001_inventory.sql in Supabase SQL editor, or:\n"
            "  python scripts/setup_inventory.py\n"
        )
        raise SystemExit(1) from exc

    existing = db.table("developers").select("id").eq("slug", DEVELOPER["slug"]).execute()
    if existing.data:
        developer_id = existing.data[0]["id"]
        print(f"Developer exists: {DEVELOPER['name']}")
    else:
        row = db.table("developers").insert(DEVELOPER).execute()
        developer_id = row.data[0]["id"]
        print(f"Created developer: {DEVELOPER['name']}")

    dev_ids: dict[str, str] = {}
    for d in DEVELOPMENTS:
        found = (
            db.table("developments")
            .select("id")
            .eq("developer_id", developer_id)
            .eq("name", d["name"])
            .eq("phase", d["phase"])
            .execute()
        )
        payload = {
            "developer_id": developer_id,
            "name": d["name"],
            "phase": d["phase"],
            "location": d["location"],
            "area_tags": d["area_tags"],
            "description": d["description"],
        }
        if found.data:
            dev_ids[d["key"]] = found.data[0]["id"]
        else:
            row = db.table("developments").insert(payload).execute()
            dev_ids[d["key"]] = row.data[0]["id"]
            print(f"  + {d['name']} {d['phase']}")

    inserted = skipped = 0
    for u in UNITS:
        development_id = dev_ids[u["dev"]]
        exists = (
            db.table("units")
            .select("id")
            .eq("development_id", development_id)
            .eq("unit_code", u["unit_code"])
            .execute()
        )
        if exists.data:
            skipped += 1
            continue
        payload = {
            "development_id": development_id,
            "unit_code": u["unit_code"],
            "title": u["title"],
            "property_type": u["property_type"],
            "bedrooms": u.get("bedrooms"),
            "price_naira": u["price_naira"],
            "status": u.get("status", "available"),
            "size_sqm": u.get("size_sqm"),
            "highlights": u.get("highlights"),
            "payment_plan_notes": u.get("payment_plan_notes"),
        }
        db.table("units").insert(payload).execute()
        inserted += 1

    available = db.table("units").select("id").eq("status", "available").execute()
    count = len(available.data or [])
    print(f"\nDone — {inserted} inserted, {skipped} skipped. Available units: {count}")


if __name__ == "__main__":
    main()
