import json
from pathlib import Path
from datetime import datetime, timezone

lines = [json.loads(l) for l in Path("data/signals.jsonl").read_text().splitlines() if l.strip()]
dates = sorted(set(s.get("forecast_date", "") for s in lines))
cities = sorted(set(s["city"] for s in lines))
markets = set(s["market_id"] for s in lines)

first = lines[0]["logged_at"]
last = lines[-1]["logged_at"]

print(f"Signals: {len(lines)} across {len(markets)} unique markets")
print(f"Cities: {', '.join(cities)}")
print(f"Forecast dates: {', '.join(dates)}")
print(f"Logging since: {first}")
print(f"Latest:        {last}")

# ETA: when do today's markets resolve?
now = datetime.now(timezone.utc)
print(f"\nCurrent time (UTC): {now.strftime('%H:%M')}")
print(f"\nMarket resolution schedule (approximate):")
print(f"  May 12 markets → resolve ~16:00 UTC (midnight HKT)")
print(f"  May 13 markets → resolve ~16:00 UTC tomorrow")
print(f"\nYou can run 'python resolve_signals.py' after midnight HKT tonight")
print(f"to score today's May 12 predictions.")
