import asyncio
import uuid
import pytest
from app.webhooks.gateway import IncomingMessage
from app.workers.tasks import process_incoming_message
from app.db.supabase import get_supabase_client
from app.core.state_machine import LeadStage

@pytest.mark.asyncio
async def test_full_pipeline_success():
    """
    Test 1: Normal path - Lead sends message, AI responds, lead qualifies.
    """
    tenant_id = str(uuid.uuid4())
    lead_phone = f"234{uuid.uuid4().int % 10**10}"
    
    # 1. Simulate Incoming Webhook
    msg = IncomingMessage(
        source="whatsapp_360",
        sender_phone=lead_phone,
        message_id=str(uuid.uuid4()),
        content="I want to buy a house in Lekki, budget is 150M naira.",
        timestamp=1700000000,
        tenant_id=tenant_id
    )
    
    # 2. Trigger worker task synchronously for testing
    # (Mocking outbound messaging to avoid real WhatsApp calls)
    from unittest.mock import patch, AsyncMock
    with patch("app.services.messaging.send_outbound_message", new_callable=AsyncMock) as mock_send:
        await process_incoming_message(msg.dict())
        
        # Verify AI responded
        assert mock_send.called
        logger_call = mock_send.call_args[0]
        assert lead_phone in logger_call
        
    # 3. Verify Lead entry in Supabase
    supabase = get_supabase_client()
    res = supabase.table("leads").select("*").eq("phone_number", lead_phone).execute()
    assert len(res.data) > 0
    lead = res.data[0]
    
    # 4. Check scoring & extraction
    assert lead["budget"] is not None
    assert lead["seriousness_score"] > 0
    assert lead["tenant_id"] == tenant_id

@pytest.mark.asyncio
async def test_tenant_isolation():
    """
    Test 2: Ensure leads from Tenant A are NOT visible to Tenant B queries.
    """
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    
    # Insert lead for Tenant A
    supabase = get_supabase_client()
    supabase.table("leads").insert({
        "phone_number": "1111111111",
        "tenant_id": tenant_a,
        "stage": "new"
    }).execute()
    
    # Query as Tenant B (Simulating RLS via set_tenant_context)
    from app.db.supabase import set_tenant_context
    await set_tenant_context(tenant_b)
    
    res = supabase.table("leads").select("*").execute()
    # Should not see Tenant A's lead
    for lead in res.data:
        assert lead["tenant_id"] != tenant_a

if __name__ == "__main__":
    asyncio.run(test_full_pipeline_success())
    asyncio.run(test_tenant_isolation())
