from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from app.db.supabase import get_supabase
from app.services.leads import get_all_leads, get_lead
from app.services.inventory import get_lead_matches

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Leads API"])


@router.get("/leads")
async def fetch_leads(stage: str | None = Query(default=None)):
    """
    Returns all leads, optionally filtered by stage.
    Dashboard calls this on load and every 30 seconds.
    """
    leads = await get_all_leads(stage=stage)
    return {"leads": leads, "total": len(leads)}


@router.get("/leads/{phone_number}")
async def fetch_lead(phone_number: str):
    """
    Returns full profile + conversation log for one lead.
    """
    lead = await get_lead(phone_number)
    if not lead:
        return {"error": "Lead not found"}

    db = get_supabase()

    def _get_logs():
        return db.table("conversation_logs")\
            .select("*")\
            .eq("phone_number", phone_number)\
            .order("created_at")\
            .execute()

    logs = await asyncio.to_thread(_get_logs)

    matches = await get_lead_matches(phone_number)

    return {
        "lead": lead,
        "conversation": logs.data,
        "matched_units": matches,
    }


@router.get("/stats")
async def fetch_stats():
    """
    Returns KPI numbers for the top summary bar.
    """
    db = get_supabase()

    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    ).isoformat()

    def _get_all_leads():
        return db.table("leads").select("stage, created_at").execute()

    all_leads = await asyncio.to_thread(_get_all_leads)
    data = all_leads.data

    total = len(data)
    new = len([l for l in data if l.get("stage") == "new"])
    qualifying = len([l for l in data if l.get("stage") == "qualifying"])
    qualified = len([l for l in data if l.get("stage") == "qualified"])
    booked = len([l for l in data if l.get("stage") == "done"])
    today_leads = len([l for l in data if l.get("created_at", "") >= today])

    return {
        "total": total,
        "new": new,
        "qualifying": qualifying,
        "qualified": qualified,
        "booked": booked,
        "today": today_leads,
        "conversion_rate": round((booked / total * 100), 1) if total > 0 else 0,
    }
