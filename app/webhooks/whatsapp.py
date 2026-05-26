from __future__ import annotations

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.logger import get_logger
from app.models.lead import IncomingMessage, WebhookAckResponse
from app.webhooks.gateway import gateway

logger = get_logger(__name__)
router = APIRouter(tags=["WhatsApp Webhook"])

# ---------------------------------------------------------------------------
# 360dialog payload parsing
# ---------------------------------------------------------------------------

MEDIA_RESPONSES = {
    "image": "I can see you sent an image! Our agent will take a look when you speak. For now, can you tell me what area you're looking at? 😊",
    "audio": "I noticed you sent a voice note — I can't listen just yet, but our agent will hear it. Meanwhile, can you tell me your budget range?",
    "document": "Got your document! Our agent will review it. Can I ask — what type of property are you looking for?",
    "video": "Thanks for the video! Our agent will check it out. What location are you considering?"
}

def parse_360dialog_payload(payload: dict) -> Optional[IncomingMessage]:
    """
    Parse a 360dialog inbound webhook payload into our IncomingMessage model.
    """
    try:
        messages = payload.get("messages")
        if not messages:
            logger.warning("Received status-update payload — no messages to process.")
            return None

        msg = messages[0]
        msg_type = msg.get("type", "text")
        media_url = None

        if msg_type == "text":
            body = msg["text"]["body"].strip()
        elif msg_type in MEDIA_RESPONSES:
            body = f"[{msg_type.upper()}_MESSAGE]"  # Sentinel for media
            if msg_type in msg:
                media_url = msg[msg_type].get("link") # 360dialog style
        else:
            return None

        # Optional lead source tag: "[source:facebook_ad] Hi there"
        source = "360dialog"
        source_match = re.match(r"^\[source:([a-z0-9_]+)\]\s*", body, re.IGNORECASE)
        if source_match:
            source = source_match.group(1).lower()
            body = body[source_match.end():].strip()

        return IncomingMessage(
            phone_number=msg["from"],
            message=body,
            message_id=msg["id"],
            message_type=msg_type,
            source=source,
            media_url=media_url,
        )

    except (KeyError, TypeError, ValueError) as exc:
        logger.error("Failed to parse 360dialog payload: %s | payload=%s", exc, payload)
        return None

def parse_evolution_payload(payload: dict) -> Optional[IncomingMessage]:
    """
    Parse an Evolution API (Baileys) inbound webhook payload.
    Expected event: messages.upsert
    """
    try:
        event = payload.get("event")
        data = payload.get("data")

        # We only process message upserts
        if event != "messages.upsert" or not data:
            logger.debug("Skipping non-message Evolution event: %s", event)
            return None

        # Ignore messages sent by the bot itself
        if data.get("key", {}).get("fromMe"):
            return None

        message_content = data.get("message", {})
        if not message_content:
            return None

        # Extract text from conversation or extendedTextMessage
        body = ""
        if "conversation" in message_content:
            body = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            body = message_content["extendedTextMessage"].get("text", "")
        
        # Handle media types mapping
        msg_type = "text"
        media_types = ["imageMessage", "audioMessage", "videoMessage", "documentMessage"]
        for mt in media_types:
            if mt in message_content:
                msg_type = mt.replace("Message", "")
                body = f"[{msg_type.upper()}_MESSAGE]"
                break

        if not body:
            return None

        # Clean phone number (remove @s.whatsapp.net)
        remote_jid = data["key"]["remoteJid"]
        phone_number = remote_jid.split("@")[0]

        return IncomingMessage(
            phone_number=phone_number,
            message=body,
            message_id=data["key"]["id"],
            message_type=msg_type,
            source="evolution",
        )

    except (KeyError, TypeError, ValueError) as exc:
        logger.error("Failed to parse Evolution payload: %s | payload=%s", exc, payload)
        return None


# ---------------------------------------------------------------------------
# Routes — All traffic flows through the unified gateway
# ---------------------------------------------------------------------------

@router.get(
    "/whatsapp",
    summary="Webhook verification",
    response_class=JSONResponse,
)
async def verify_webhook():
    """
    Some WhatsApp / 360dialog setups issue a GET to verify the endpoint exists.
    """
    return {"status": "Reva webhook active"}


@router.post("/360dialog", response_model=WebhookAckResponse)
async def whatsapp_360dialog_webhook(request: Request):
    """
    Inbound message webhook for 360dialog.
    Parses payload, then delegates to the gateway for signature verification,
    rate limiting, deduplication, and Celery dispatch.
    """
    payload = await request.json()
    incoming = parse_360dialog_payload(payload)
    return await gateway.ingest(request, incoming)


@router.post("/evolution", response_model=WebhookAckResponse)
async def whatsapp_evolution_webhook(request: Request):
    """
    Inbound message webhook for Evolution API.
    Parses payload, then delegates to the gateway for security and dispatch.
    """
    payload = await request.json()
    incoming = parse_evolution_payload(payload)
    return await gateway.ingest(request, incoming)
