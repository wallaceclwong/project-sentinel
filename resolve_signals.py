"""
WeatherNext Pro — Signal Resolution Checker
Polls Polymarket for resolved markets, matches them to logged predictions,
and fills in the outcome field in data/signals.jsonl.

Usage:
    python resolve_signals.py           # Check all unresolved signals
    python resolve_signals.py --dry-run # Show what would be updated
"""
import argparse
import json
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx

SIGNALS_PATH = Path("data/signals.jsonl")
GAMMA_URL = "https://gamma-api.polymarket.com"


def load_signals() -> list[dict]:
    """Load all logged signals from JSONL."""
    if not SIGNALS_PATH.exists():
        return []
    signals = []
    for line in SIGNALS_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            signals.append(json.loads(line))
    return signals


def save_signals(signals: list[dict]):
    """Atomically rewrite the signals file."""
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mktemp(dir=SIGNALS_PATH.parent, suffix=".tmp"))
    with open(tmp, "w") as f:
        for s in signals:
            f.write(json.dumps(s) + "\n")
    shutil.move(str(tmp), str(SIGNALS_PATH))


def fetch_resolved_market(condition_id: str, client: httpx.Client) -> dict | None:
    """Fetch a single market by condition_id from Gamma API."""
    try:
        resp = client.get(
            f"{GAMMA_URL}/markets",
            params={"condition_id": condition_id, "limit": 1},
        )
        resp.raise_for_status()
        markets = resp.json()
        if markets:
            return markets[0]
    except Exception as e:
        print(f"  ⚠ Failed to fetch {condition_id}: {e}")
    return None


def determine_outcome(market_data: dict) -> float | None:
    """
    Determine YES outcome from resolved market.
    Returns 1.0 (YES won), 0.0 (NO won), or None (not yet resolved).
    """
    if not market_data.get("closed"):
        return None

    # Resolved prices: [YES_price, NO_price] — winner gets 1.0
    raw = market_data.get("outcomePrices", "[]")
    try:
        prices = json.loads(raw) if isinstance(raw, str) else raw
        yes_price = float(prices[0])
        # Resolved markets snap to 0.0 or 1.0
        if yes_price >= 0.99:
            return 1.0
        elif yes_price <= 0.01:
            return 0.0
        else:
            return None  # Not fully resolved yet
    except Exception:
        return None


def resolve(dry_run: bool = False):
    signals = load_signals()
    if not signals:
        print("No signals found in data/signals.jsonl")
        return

    unresolved = [s for s in signals if s.get("outcome") is None]
    already = len(signals) - len(unresolved)
    print(f"Signals: {len(signals)} total, {already} resolved, {len(unresolved)} pending")

    if not unresolved:
        print("Nothing to resolve.")
        return

    # Deduplicate condition_ids to minimize API calls
    unique_conditions = {s["condition_id"] for s in unresolved}
    print(f"Checking {len(unique_conditions)} unique markets on Polymarket...\n")

    resolved_count = 0
    outcomes: dict[str, float] = {}

    with httpx.Client(timeout=15.0) as client:
        for cid in unique_conditions:
            market_data = fetch_resolved_market(cid, client)
            if not market_data:
                continue

            outcome = determine_outcome(market_data)
            if outcome is not None:
                outcomes[cid] = outcome
                question = market_data.get("question", "")[:60]
                print(f"  ✅ {question}... → YES={outcome}")

    # Apply outcomes to signals
    for s in signals:
        if s.get("outcome") is None and s["condition_id"] in outcomes:
            s["outcome"] = outcomes[s["condition_id"]]
            s["resolved_at"] = datetime.now(timezone.utc).isoformat()
            resolved_count += 1

    if resolved_count == 0:
        print("\nNo new resolutions found. Markets may still be open.")
        return

    if dry_run:
        print(f"\n[DRY RUN] Would update {resolved_count} signals. No file changes made.")
    else:
        save_signals(signals)
        print(f"\n✅ Updated {resolved_count} signals in {SIGNALS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve logged Polymarket signals")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    resolve(dry_run=args.dry_run)
