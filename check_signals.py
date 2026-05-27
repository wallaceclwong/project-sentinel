"""Quick check: how many signals have been logged."""
import json
from pathlib import Path
from collections import Counter

p = Path("data/signals.jsonl")
if not p.exists():
    print("No signals file yet")
    exit()

lines = [l for l in p.read_text().splitlines() if l.strip()]
print(f"{len(lines)} signals logged")

actions = Counter()
cities = Counter()
for l in lines:
    s = json.loads(l)
    actions[s["action"]] += 1
    if s["action"] != "SKIP":
        cities[s["city"]] += 1

print(f"  BUY_YES: {actions['BUY_YES']}")
print(f"  BUY_NO:  {actions['BUY_NO']}")
print(f"  SKIP:    {actions['SKIP']}")
print(f"\nTop cities with actionable signals:")
for city, count in cities.most_common(10):
    print(f"  {city}: {count}")
