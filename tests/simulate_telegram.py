import asyncio
import httpx
import uuid

async def simulate_telegram_message(text: str, chat_id: str = "123456789"):
    url = "http://localhost:8000/webhook/telegram"
    message_id = str(uuid.uuid4())
    
    payload = {
        "update_id": 10000,
        "message": {
            "message_id": message_id,
            "from": {
                "id": chat_id,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": chat_id,
                "first_name": "Test",
                "type": "private"
            },
            "date": 1600000000,
            "text": text
        }
    }
    
    # We might need the secret header if TELEGRAM_WEBHOOK_SECRET is set
    headers = {
        "X-Telegram-Bot-Api-Secret-Token": "" # Empty for now as it's not set in .env
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hello, I am looking for a property in Lekki."
    asyncio.run(simulate_telegram_message(msg))
