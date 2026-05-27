import asyncio
import httpx

async def find_weather_markets():
    client = httpx.AsyncClient(timeout=15.0)
    found = {}

    keywords = ["temperature", "temp", "celsius", "weather", "heat"]
    for kw in keywords:
        resp = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": 50, "search": kw}
        )
        if resp.status_code == 200:
            for m in resp.json():
                if m["id"] not in found:
                    found[m["id"]] = m

    print(f"Found {len(found)} unique active weather/temp markets:\n")
    for m in sorted(found.values(), key=lambda x: float(x.get("liquidity", 0)), reverse=True):
        liq = float(m.get("liquidity", 0))
        print(f"  slug:      {m.get('slug', '?')}")
        print(f"  question:  {m.get('question', '?')[:90]}")
        print(f"  liquidity: ${liq:,.0f}")
        print(f"  prices:    {m.get('outcomePrices', '?')}")
        print()

    await client.aclose()

asyncio.run(find_weather_markets())
