import logging
import os

from supabase import Client, create_client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    """
    Returns a configured singleton Supabase client.
    Requires SUPABASE_URL and SUPABASE_KEY to be set in the environment.
    """
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

        _client = create_client(url, key)
        logger.info("Supabase client initialized.")
        
    return _client
