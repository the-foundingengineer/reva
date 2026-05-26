import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.db.supabase import get_supabase

logger = logging.getLogger(__name__)


async def upsert_lead(phone_number: str, extracted_data: dict[str, Any], stage: str) -> dict | None:
    """
    Creates a lead if it's their first time, or updates them if they're returning.
    Only updates fields that have actual values (ignores None/null).
    """
    try:
        db = get_supabase()

        # Fetch existing lead data first
        def _get_existing():
            return db.table("leads").select("*").eq("phone_number", phone_number).execute()
        
        existing = await asyncio.to_thread(_get_existing)
        existing_data = existing.data[0] if existing.data else {}

        # Merge — never overwrite existing values with null
        payload = {"phone_number": phone_number, "stage": stage}
        fields = [
            "budget",
            "location",
            "property_type",
            "timeline",
            "language",
            "seriousness_score",
            "assigned_agent_id",
            "name",
            "source",
            "utm_campaign",
            "tenant_id",
            "development_id",
            "attribution",
            "closing_revenue",
            "is_paused",
        ]

        for field in fields:
            new_value = extracted_data.get(field)
            old_value = existing_data.get(field)
            payload[field] = new_value if new_value is not None else old_value

        now = datetime.now(timezone.utc).isoformat()
        if extracted_data.get("first_response_at") and not existing_data.get("first_response_at"):
            payload["first_response_at"] = extracted_data["first_response_at"]
        if stage == "qualified" and not existing_data.get("qualified_at"):
            payload["qualified_at"] = now

        def _do_upsert():
            return db.table("leads").upsert(
                payload,
                on_conflict="phone_number"
            ).execute()

        result = await asyncio.to_thread(_do_upsert)

        logger.info("Lead upserted: %s | Stage: %s", phone_number, stage)
        return result.data[0] if result.data else None

    except Exception as exc:
        logger.error("Failed to upsert lead %s: %s", phone_number, exc)
        return None


async def get_lead(phone_number: str) -> dict | None:
    """Fetches a lead's full profile by phone number."""
    try:
        db = get_supabase()
        
        def _get():
            return db.table("leads")\
                .select("*")\
                .eq("phone_number", phone_number)\
                .single()\
                .execute()
                
        result = await asyncio.to_thread(_get)

        return result.data

    except Exception as exc:
        logger.error("Failed to fetch lead %s: %s", phone_number, exc)
        return None


async def log_message(phone_number: str, role: str, message: str) -> None:
    """
    Logs every message to the conversation_logs table.
    Provides a full audit trail of the conversation for dashboard review.
    """
    try:
        db = get_supabase()
        
        def _log():
            return db.table("conversation_logs").insert({
                "phone_number": phone_number,
                "role": role,
                "message": message
            }).execute()
            
        await asyncio.to_thread(_log)
        
    except Exception as exc:
        logger.error("Failed to log message for %s: %s", phone_number, exc)


async def get_all_leads(stage: str | None = None) -> list:
    """
    Fetches all leads, optionally filtered by stage.
    Useful for populating a CRM dashboard.
    """
    try:
        db = get_supabase()
        
        def _get_all():
            query = db.table("leads").select("*").order("created_at", desc=True)
            if stage:
                query = query.eq("stage", stage)
            return query.execute()

        result = await asyncio.to_thread(_get_all)
        return result.data

    except Exception as exc:
        logger.error("Failed to fetch leads: %s", exc)
        return []


async def mark_meeting_booked(phone_number: str, meeting_url: str) -> None:
    """Marks a lead as booked once they schedule through Calendly/similar."""
    try:
        db = get_supabase()
        
        def _update():
            return db.table("leads").update({
                "meeting_booked": True,
                "meeting_url": meeting_url,
                "stage": "done"
            }).eq("phone_number", phone_number).execute()
            
        await asyncio.to_thread(_update)

        logger.info("Meeting booked for %s", phone_number)

    except Exception as exc:
        logger.error("Failed to mark meeting booked for %s: %s", phone_number, exc)
