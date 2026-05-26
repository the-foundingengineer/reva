#!/usr/bin/env python3
"""
Apply migrations/002_properties_and_revenue.sql to Supabase Postgres.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

MIGRATION = ROOT / "migrations" / "002_properties_and_revenue.sql"


def _build_url_from_password() -> str | None:
    password = os.getenv("SUPABASE_DB_PASSWORD")
    base = os.getenv("SUPABASE_URL", "")
    if not password or not base:
        return None
    ref = urlparse(base).netloc.split(".")[0]
    return (
        f"postgresql://postgres:{password}@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"
    )


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

    # Use the direct connection if pooler fails or is slow
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Migration applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
