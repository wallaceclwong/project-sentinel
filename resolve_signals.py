"""Resolve logged signals against Polymarket Gamma API /markets/{id}."""
import json, time, sys
from pathlib import Path
from datetime import datetime, timezone
import httpx

SIGNALS_PATH = Path("data/signals.jsonl")
GAMMA_URL = "https://gamma-api.polymarket.com"


def resolve():
    lines = [json.loads(l) for l in SIGNALS_PATH.read_text().splitlines() if l.strip()]
    pending = [s for s in lines if s.get("outcome") is None]
    unique_ids = sorted(set(s["market_id"] for s in pending))
    print(f"Signals: {len(lines)} total, {len(pending)} pending, {len(unique_ids)} unique markets", flush=True)

    if not unique_ids:
        print("Nothing to resolve.", flush=True)
        return

    outcomes = {}
    client = httpx.Client(timeout=15.0)
    for i, mid in enumerate(unique_ids):
        for attempt in range(3):
            try:
                resp = client.get(f"{GAMMA_URL}/markets/{mid}")
                if resp.status_code >= 500:
                    if attempt < 2:
                        time.sleep(1.5 ** attempt)
                        continue
                    break
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                mkt = resp.json()
                if not isinstance(mkt, dict):
                    break
                if mkt.get("closed"):
                    raw = mkt.get("outcomePrices", "[]")
                    prices = json.loads(raw) if isinstance(raw, str) else raw
                    if prices and len(prices) >= 1:
                        yes = float(prices[0])
                        if yes >= 0.99:
                            outcomes[mid] = 1.0
                        elif yes <= 0.01:
                            outcomes[mid] = 0.0
                break
            except Exception:
                if attempt < 2:
                    time.sleep(1.5 ** attempt)
                    continue

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(unique_ids)} checked, {len(outcomes)} resolved", flush=True)
        time.sleep(0.08)

    client.close()

    updated = 0
    for s in lines:
        if s.get("outcome") is None and s["market_id"] in outcomes:
            s["outcome"] = outcomes[s["market_id"]]
            s["resolved_at"] = datetime.now(timezone.utc).isoformat()
            updated += 1

    if updated:
        tmp = SIGNALS_PATH.with_suffix(".tmp")
        with open(tmp, "w") as f:
            for s in lines:
                f.write(json.dumps(s) + "\n")
        tmp.replace(SIGNALS_PATH)
        print(f"\nUpdated {updated}/{len(pending)} signals with resolved outcomes", flush=True)
    else:
        print(f"\nNo new outcomes to apply (checked {len(unique_ids)} markets)", flush=True)


if __name__ == "__main__":
    resolve()
