import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.inventory import search_properties

async def test_search():
    print("Testing FTS search for 'Lekki apartment' under 20M...")
    results = await search_properties("Lekki", "apartment", 20_000_000, 2)
    for r in results:
        print(f"Match: {r['name']} - {r['location']} - ₦{r['price']} (Source: {r['source']}, Rank: {r.get('rank')})")

    print("\nTesting FTS search for 'duplex' under 80M...")
    results2 = await search_properties("", "duplex", 80_000_000, 4)
    for r in results2:
        print(f"Match: {r['name']} - {r['location']} - ₦{r['price']} (Source: {r['source']}, Rank: {r.get('rank')})")

if __name__ == "__main__":
    asyncio.run(test_search())
