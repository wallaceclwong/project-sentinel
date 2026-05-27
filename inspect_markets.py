import asyncio
import httpx

async def fetch_todays_markets():
    client = httpx.AsyncClient(timeout=15.0)

    # Try without active/closed filter to see what's there
    for params in [
        {"tag_slug": "temperature", "limit": 20},
        {"tag_slug": "temperature", "active": "true", "limit": 20},
        {"tag_slug": "temperature", "closed": "false", "limit": 20},
    ]:
        resp = await client.get("https://gamma-api.polymarket.com/events", params=params)
        events = resp.json()
        print(f"\nParams {params} -> {len(events)} events")
        for e in events[:3]:
            print(f"  title: {e.get('title','')}")
            print(f"  active={e.get('active')} closed={e.get('closed')} archived={e.get('archived')}")
            for m in e.get("markets", [])[:2]:
                print(f"    Q: {m.get('question','')[:70]}")
                print(f"       prices={m.get('outcomePrices')} active={m.get('active')} closed={m.get('closed')}")

    await client.aclose()

asyncio.run(fetch_todays_markets())
