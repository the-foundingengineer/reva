"""
Unit tests for Reva inventory matching (no DB required).
"""

import pytest

from app.services.inventory import (
    format_matches_whatsapp,
    parse_budget_naira,
    parse_bedrooms,
    _normalize_areas,
    _score_unit,
)
from app.models.inventory import UnitMatch


class TestBudgetParser:
    def test_million_shorthand(self):
        lo, hi = parse_budget_naira("15 million naira")
        assert lo is not None and hi is not None
        assert 12_000_000 <= lo <= 16_000_000
        assert 14_000_000 <= hi <= 18_000_000

    def test_m_suffix(self):
        lo, hi = parse_budget_naira("about 15M")
        assert lo is not None
        assert 12_000_000 <= lo <= 18_000_000

    def test_range(self):
        lo, hi = parse_budget_naira("12-18 million")
        assert lo == 12_000_000
        assert hi == 18_000_000


class TestBedrooms:
    def test_two_bed_apartment(self):
        assert parse_bedrooms("2 bedroom apartment") == 2

    def test_duplex(self):
        assert parse_bedrooms("duplex") == 4


class TestAreaNormalize:
    def test_ikoyi_alias(self):
        areas = _normalize_areas("Ikoyi, Lagos")
        assert "ikoyi" in areas

    def test_lekki_phase(self):
        areas = _normalize_areas("Lekki Phase 1")
        assert "lekki" in areas


class TestScoring:
    def _unit(self, price: int, location: str, tags: list[str], beds: int):
        return {
            "price_naira": price,
            "bedrooms": beds,
            "property_type": "flat",
            "developments": {
                "location": location,
                "area_tags": tags,
            },
        }

    def test_ikoyi_match_scores_higher(self):
        lead_budget = parse_budget_naira("15 million")
        areas = _normalize_areas("Ikoyi")
        beds = parse_bedrooms("2 bedroom apartment")

        ikoyi = _score_unit(
            self._unit(145_000_000, "Ikoyi, Lagos", ["ikoyi"], 2),
            lead_budget[0], lead_budget[1], areas, beds, "2 bedroom",
        )
        ajah = _score_unit(
            self._unit(38_500_000, "Sangotedo, Ajah", ["ajah"], 2),
            lead_budget[0], lead_budget[1], areas, beds, "2 bedroom",
        )
        assert ikoyi > ajah


class TestWhatsAppFormat:
    def test_format_three_matches(self):
        matches = [
            UnitMatch(
                unit_id="1",
                unit_code="HT-201",
                title="2-Bed Executive",
                development_name="Horizon Terraces",
                phase="Phase 3",
                location="Ikoyi",
                property_type="flat",
                bedrooms=2,
                price_naira=145_000_000,
                price_display="₦145M",
                match_score=88,
                rank=1,
            )
        ]
        msg = format_matches_whatsapp(matches)
        assert "Reva" not in msg
        assert "AI" not in msg
        assert "Horizon Terraces" in msg
        assert "₦145M" in msg
