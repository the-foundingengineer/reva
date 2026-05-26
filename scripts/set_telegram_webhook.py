import os
import sys
import httpx
from dotenv import load_dotenv

def set_webhook(url: str):
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return

    # Remove quotes if present
    token = token.strip('"').strip("'")
    
    webhook_url = f"{url.rstrip('/')}/webhook/telegram"
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    print(f"Setting webhook to: {webhook_url}")
    
    try:
        response = httpx.post(api_url, json={"url": webhook_url})
        result = response.json()
        if result.get("ok"):
            print("Success: Webhook set successfully!")
        else:
            print(f"Failed: {result.get('description')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/set_telegram_webhook.py <your_tunnel_url>")
        print("Example: python scripts/set_telegram_webhook.py https://166005a49d3866.lhr.life")
    else:
        set_webhook(sys.argv[1])
