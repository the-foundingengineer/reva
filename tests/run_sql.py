import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

sql_file = ROOT / "migrations" / "006_unified_inventory_fts.sql"
sql_content = sql_file.read_text()

def get_db_url():
    url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not url:
        password = os.getenv("SUPABASE_DB_PASSWORD")
        base = os.getenv("SUPABASE_URL", "")
        if password and base:
            from urllib.parse import urlparse
            ref = urlparse(base).netloc.split(".")[0]
            url = f"postgresql://postgres:{password}@db.{ref}.supabase.co:5432/postgres"
    return url

db_url = get_db_url()
if not db_url:
    print("Could not find database URL.")
    exit(1)

try:
    print("Connecting to DB...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        print("Executing SQL...")
        cur.execute(sql_content)
        print("Reloading postgrest schema...")
        cur.execute("NOTIFY pgrst, 'reload schema';")
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
