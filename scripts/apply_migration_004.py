#!/usr/bin/env python3
"""
Apply migrations/004_multi_tenancy_and_closing.sql to Supabase Postgres.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

MIGRATION = ROOT / "migrations" / "004_multi_tenancy_and_closing.sql"

def _build_url_from_password() -> str | None:
    password = os.getenv("SUPABASE_DB_PASSWORD")
    base = os.getenv("SUPABASE_URL", "")
    if not password or not base:
        return None
    return f"postgresql://postgres.uwrowssbpjwjquqehpyn:{password}@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"

def main() -> None:
    db_url = (
        os.getenv("SUPABASE_DB_URL")
        or os.getenv("DATABASE_URL")
        or _build_url_from_password()
    )

    if not db_url:
        print("No database URL configured.")
        raise SystemExit(1)

    try:
        import psycopg2
    except ImportError:
        print("Installing psycopg2-binary...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary -q")
        import psycopg2

    sql = MIGRATION.read_text(encoding="utf-8")
    print(f"Applying {MIGRATION.name} ...")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")
        raise SystemExit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
