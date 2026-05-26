"""
Redis integration validation script.

Usage (with Redis running locally):
    python tests/test_redis.py

Expected output:
    ✅ Conversation history — save & retrieve
    ✅ History trimming
    ✅ Stage tracking — set & get
    ✅ Invalid stage rejected
    ✅ Lead data — update & merge
    ✅ Conversation reset
    ✅ All Redis checks passed
"""

import asyncio
import sys

from app.cache.redis import (
    clear_conversation,
    get_conversation_history,
    get_lead_data,
    get_lead_stage,
    save_conversation_history,
    set_lead_stage,
    update_lead_data,
    MAX_HISTORY_LENGTH,
)
from app.services.conversation import (
    build_conversation_context,
    save_ai_response,
    advance_stage_if_ready,
    reset_lead,
)
from app.models.lead import IncomingMessage

PHONE = "2348012345678_test"  # dedicated test number — won't collide with real data


async def run() -> None:
    errors: list[str] = []

    # ── 1. Conversation history save & retrieve ──────────────────────────────
    await clear_conversation(PHONE)
    history = [
        {"role": "user",      "content": "I need a flat in Ajah"},
        {"role": "assistant", "content": "What is your budget?"},
    ]
    await save_conversation_history(PHONE, history)
    retrieved = await get_conversation_history(PHONE)
    if retrieved != history:
        errors.append(f"History mismatch: {retrieved}")
    else:
        print("✅ Conversation history — save & retrieve")

    # ── 2. History trimming ──────────────────────────────────────────────────
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(MAX_HISTORY_LENGTH + 20)]
    await save_conversation_history(PHONE, long_history)
    trimmed = await get_conversation_history(PHONE)
    if len(trimmed) > MAX_HISTORY_LENGTH:
        errors.append(f"History not trimmed: length={len(trimmed)}")
    else:
        print("✅ History trimming")

    # ── 3. Stage tracking ────────────────────────────────────────────────────
    await set_lead_stage(PHONE, "qualifying")
    stage = await get_lead_stage(PHONE)
    if stage != "qualifying":
        errors.append(f"Stage mismatch: got {stage!r}")
    else:
        print("✅ Stage tracking — set & get")

    # ── 4. Invalid stage rejected ────────────────────────────────────────────
    await set_lead_stage(PHONE, "invalid_stage")
    stage_after = await get_lead_stage(PHONE)
    if stage_after == "invalid_stage":
        errors.append("Invalid stage was accepted!")
    else:
        print("✅ Invalid stage rejected")

    # ── 5. Lead data — update & merge ───────────────────────────────────────
    await update_lead_data(PHONE, {"budget": "1.5m", "location": "Ajah"})
    await update_lead_data(PHONE, {"property_type": "flat", "budget": "2m"})  # budget overwrite
    data = await get_lead_data(PHONE)
    if data.get("location") != "Ajah" or data.get("budget") != "2m":
        errors.append(f"Lead data merge failed: {data}")
    else:
        print("✅ Lead data — update & merge")

    # ── 6. build_conversation_context ───────────────────────────────────────
    await clear_conversation(PHONE)
    await set_lead_stage(PHONE, "new")
    msg = IncomingMessage(phone_number=PHONE, message="Hello!", message_id="m1")
    ctx = await build_conversation_context(msg)
    if ctx["history"][-1]["content"] != "Hello!" or ctx["stage"] != "new":
        errors.append(f"Context build failed: {ctx}")

    # save AI response
    await save_ai_response(PHONE, ctx["history"], "Hi! I'm Reva.")
    hist = await get_conversation_history(PHONE)
    if hist[-1]["content"] != "Hi! I'm Reva.":
        errors.append("AI response not persisted")

    # ── 7. Stage auto-advance ────────────────────────────────────────────────
    full_data = {"budget": "1.5m", "location": "Ajah", "property_type": "flat", "timeline": "3 months"}
    new_stage = await advance_stage_if_ready(PHONE, "qualifying", full_data)
    if new_stage != "qualified":
        errors.append(f"Expected 'qualified', got {new_stage!r}")

    # ── 8. Reset ─────────────────────────────────────────────────────────────
    await reset_lead(PHONE)
    if await get_lead_stage(PHONE) != "new" or await get_conversation_history(PHONE) != []:
        errors.append("Reset failed")
    else:
        print("✅ Conversation reset")

    # ── Result ───────────────────────────────────────────────────────────────
    if errors:
        print("\n❌ Failures:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("\n✅ All Redis checks passed")


if __name__ == "__main__":
    asyncio.run(run())
