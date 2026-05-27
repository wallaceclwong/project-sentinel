"""
Daily summary report: analyze resolved signals and compute edge metrics.
Run this after markets close (midnight HKT) to see if you beat the market.

Usage:
  python daily_summary.py [--date YYYY-MM-DD]
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from argparse import ArgumentParser


def load_signals(date_str: str = None) -> list[dict]:
    """Load signals from JSONL file, optionally filtered by date."""
    signals_file = Path("data/signals.jsonl")
    if not signals_file.exists():
        print("No signals file found. Run the scanner first.")
        return []

    signals = []
    for line in signals_file.read_text().splitlines():
        if not line.strip():
            continue
        s = json.loads(line)
        if date_str:
            # Filter by forecast_date
            if s.get("forecast_date") != date_str:
                continue
        signals.append(s)
    return signals


def compute_brier_score(signals: list[dict]) -> dict:
    """
    Compute Brier score for resolved signals.
    Brier = mean((forecast - outcome)^2)
    Lower is better. 0 = perfect, 0.25 = random guessing.
    """
    resolved = [s for s in signals if s.get("outcome") is not None]
    if not resolved:
        return {"count": 0, "brier": None, "accuracy": None}

    outcomes = []
    for s in resolved:
        outcome = s["outcome"]
        our_prob = s["our_prob"]
        # outcome is 1 (YES won) or 0 (NO won)
        outcomes.append((our_prob, outcome))

    brier = sum((prob - outcome) ** 2 for prob, outcome in outcomes) / len(outcomes)
    accuracy = sum(1 for prob, outcome in outcomes if (prob > 0.5) == (outcome == 1)) / len(outcomes)

    return {
        "count": len(resolved),
        "brier": round(brier, 4),
        "accuracy": round(accuracy, 4),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--date", default=None, help="Filter by forecast date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Default to today
    if not args.date:
        args.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    signals = load_signals(args.date)
    if not signals:
        print(f"No signals for {args.date}")
        return

    # Summary stats
    total = len(signals)
    actionable = len([s for s in signals if s["action"] != "SKIP"])
    buy_yes = len([s for s in signals if s["action"] == "BUY_YES"])
    buy_no = len([s for s in signals if s["action"] == "BUY_NO"])
    resolved = len([s for s in signals if s.get("outcome") is not None])

    print(f"\n{'='*70}")
    print(f"  DAILY SUMMARY — {args.date}")
    print(f"{'='*70}\n")

    print(f"Signals collected:      {total}")
    print(f"  Actionable (edge>10%): {actionable} ({actionable/total*100:.0f}%)")
    print(f"    BUY_YES:            {buy_yes}")
    print(f"    BUY_NO:             {buy_no}")
    print(f"  SKIP (edge<10%):       {total - actionable}")
    print(f"\nResolved markets:       {resolved}/{actionable}")

    # Brier score
    brier_data = compute_brier_score(signals)
    if brier_data["count"] > 0:
        print(f"\nBrier Score (lower=better):")
        print(f"  Score:                {brier_data['brier']}")
        print(f"  Accuracy:             {brier_data['accuracy']:.1%}")
        if brier_data["brier"] < 0.25:
            print(f"  Status:               ✅ BEATING RANDOM (0.25)")
        else:
            print(f"  Status:               ❌ WORSE THAN RANDOM")

    # Top edges by city
    by_city = defaultdict(list)
    for s in signals:
        if s["action"] != "SKIP":
            by_city[s["city"]].append(s)

    if by_city:
        print(f"\nTop edges by city:")
        for city in sorted(by_city.keys(), key=lambda c: max(s["edge_pct"] for s in by_city[c]), reverse=True)[:5]:
            signals_city = by_city[city]
            max_edge = max(s["edge_pct"] for s in signals_city)
            count = len(signals_city)
            print(f"  {city:15s} | {count:2d} signals | max edge {max_edge:+6.1f}%")

    # Source comparison (Google vs Ensemble)
    google_edges = []
    ensemble_edges = []
    for s in signals:
        if s.get("google_prob") is not None:
            google_edges.append(abs(s["google_prob"] - s["market_prob"]) * 100)
        if s.get("ensemble_prob") is not None:
            ensemble_edges.append(abs(s["ensemble_prob"] - s["market_prob"]) * 100)

    if google_edges and ensemble_edges:
        avg_google = sum(google_edges) / len(google_edges)
        avg_ensemble = sum(ensemble_edges) / len(ensemble_edges)
        print(f"\nSource comparison (average edge):")
        print(f"  Google Weather:       {avg_google:6.2f}%")
        print(f"  Open-Meteo Ensemble:  {avg_ensemble:6.2f}%")
        if avg_ensemble > avg_google:
            print(f"  Winner:               Ensemble (+{avg_ensemble - avg_google:.2f}%)")
        else:
            print(f"  Winner:               Google (+{avg_google - avg_ensemble:.2f}%)")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
