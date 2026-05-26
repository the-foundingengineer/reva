import asyncio
import hmac
import hashlib
import json
import os
import uuid
import httpx
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.environ.get("WHATSAPP_WEBHOOK_SECRET", "")
URL = "http://127.0.0.1:8080/webhook/whatsapp"

async def send_simulated_message(phone: str, text: str):
    """
    Simulates exactly what 360dialog forces into the webhook,
    creating a signed payload mimicking the real production funnel.
    """
    payload = {
        "messages": [
            {
                "from": phone,
                "id": f"gBGGJ{uuid.uuid4().hex[:6]}",
                "type": "text",
                "text": {"body": text}
            }
        ]
    }
    
    body = json.dumps(payload).encode()
    
    # 360dialog HMAC-SHA256 Signature
    signature = ""
    if WEBHOOK_SECRET:
        signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    
    headers = {"Content-Type": "application/json"}
    if signature:
        headers["D360-Signature"] = signature
        
    print(f"\n[You]: {text}")
        
    try:
        async with httpx.AsyncClient() as client:
            # Webhook returns 200 immediately; AI runs in the background (Ollama can take minutes).
            res = await client.post(URL, content=body, headers=headers, timeout=10.0)
            if res.status_code == 200:
                print("[✔] Webhook acknowledged 200 OK — watch Uvicorn logs for AI replies (may take 1–2 min on first Ollama run)")
            else:
                print(f"[!] Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Network error trying to hit {URL}: {repr(e)}")

async def main():
    print("=========================================")
    print("🔥 Reva Lead Qualification API Simulator")
    print("=========================================\n")
    print("Ensure Uvicorn is actively running on port 8080!")
    print("This mimics a live lead going through the entire funnnel.\n")
    
    phone = "23481234567"
    
    # Simulate a full user flow testing intent extraction
    await asyncio.sleep(1)
    await send_simulated_message(phone, "Hi, my name is John. Can you help me find a place?")
    
    await asyncio.sleep(90)
    await send_simulated_message(phone, "I'm looking for a 2 bedroom apartment in Ikoyi, Lagos.")
    
    await asyncio.sleep(90)
    await send_simulated_message(phone, "My budget is about 15 million naira.")
    
    await asyncio.sleep(90)
    await send_simulated_message(phone, "I am looking to move in next month if possible.")
    
    print("\n[i] The AI should now formally qualify the lead natively and invoke the Inline Booking Engine.")
    print("[i] Checking AI Slot Options in your Uvicorn logs.. (Reply with '1', '2' or '3')")
    
    await asyncio.sleep(120)
    await send_simulated_message(phone, "2")
    
    print("\n[✔] Simulation complete. Booking should be marked as done natively in Supabase.")

if __name__ == "__main__":
    asyncio.run(main())
