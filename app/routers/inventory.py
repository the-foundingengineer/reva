from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from app.models.inventory import LeadMatchRequest
from app.services.inventory import fetch_available_units, get_lead_matches, match_units

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Inventory"])


@router.get("/units")
async def list_units(status: str = Query(default="available")):
    """List inventory units (for dashboard / admin)."""
    units = await fetch_available_units()
    if status != "available":
        return {"units": units, "total": len(units)}
    return {"units": units, "total": len(units)}


@router.post("/inventory/match")
async def match_inventory(body: LeadMatchRequest):
    """Preview unit matches for a lead profile (testing / dashboard)."""
    matches = await match_units(
        budget=body.budget,
        location=body.location,
        property_type=body.property_type,
        limit=body.limit,
    )
    return {"matches": [m.model_dump() for m in matches], "total": len(matches)}


@router.get("/leads/{phone_number}/matches")
async def lead_matches(phone_number: str):
    """Units previously offered to a lead."""
    matches = await get_lead_matches(phone_number)
    return {"phone_number": phone_number, "matches": matches}
