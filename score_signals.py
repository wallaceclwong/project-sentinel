"""
WeatherNext Pro — Signal Scoring
Computes Brier scores to compare our predictions vs. the market.

Usage:
    python score_signals.py              # Full report
    python score_signals.py --by-city    # Breakdown by city
    python score_signals.py --by-bracket # Breakdown by bracket type
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

SIGNALS_PATH = Path("data/signals.jsonl")


def load_resolved() -> list[dict]:
    """Load only resolved signals."""
    if not SIGNALS_PATH.exists():
        return []
    resolved = []
    for line in SIGNALS_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        s = json.loads(line)
        if s.get("outcome") is not None:
            resolved.append(s)
    return resolved


def brier_score(prob: float, outcome: float) -> float:
    """Brier score: (probability - outcome)^2. Lower is better."""
    return (prob - outcome) ** 2


def report(signals: list[dict], group_key: str | None = None):
    """Print scoring report, optionally grouped by a key."""
    if not signals:
        print("No resolved signals found. Run resolve_signals.py first.")
        return

    groups: dict[str, list[dict]] = defaultdict(list)
    if group_key:
        for s in signals:
            groups[s.get(group_key, "unknown")].append(s)
    else:
        groups["ALL"] = signals

    print(f"{'Group':<20} {'N':>5} {'Our Brier':>10} {'Mkt Brier':>10} {'Edge':>8} {'Verdict':>10}")
    print("-" * 70)

    total_our = 0.0
    total_mkt = 0.0
    total_n = 0

    for group_name in sorted(groups):
        group = groups[group_name]
        n = len(group)
        our_brier = sum(brier_score(s["our_prob"], s["outcome"]) for s in group) / n
        mkt_brier = sum(brier_score(s["market_prob"], s["outcome"]) for s in group) / n
        edge = mkt_brier - our_brier  # positive = we're better

        total_our += our_brier * n
        total_mkt += mkt_brier * n
        total_n += n

        if edge > 0.005:
            verdict = "✅ US"
        elif edge < -0.005:
            verdict = "❌ MARKET"
        else:
            verdict = "➖ TIE"

        print(f"{group_name:<20} {n:>5} {our_brier:>10.4f} {mkt_brier:>10.4f} {edge:>+8.4f} {verdict:>10}")

    if total_n > 0 and group_key:
        avg_our = total_our / total_n
        avg_mkt = total_mkt / total_n
        avg_edge = avg_mkt - avg_our
        print("-" * 70)
        print(f"{'OVERALL':<20} {total_n:>5} {avg_our:>10.4f} {avg_mkt:>10.4f} {avg_edge:>+8.4f}")

    # Summary
    print()
    if total_n > 0:
        avg_our = total_our / total_n
        avg_mkt = total_mkt / total_n
        print(f"Our Brier score:    {avg_our:.4f}")
        print(f"Market Brier score: {avg_mkt:.4f}")
        if avg_our < avg_mkt:
            pct = (1 - avg_our / avg_mkt) * 100
            print(f"🎯 We beat the market by {pct:.1f}% (lower Brier = better)")
        elif avg_our > avg_mkt:
            pct = (1 - avg_mkt / avg_our) * 100
            print(f"📉 Market beats us by {pct:.1f}%")
        else:
            print("➖ Tied with the market")

    # Actionable signals only
    actionable = [s for s in signals if s["action"] != "SKIP"]
    if actionable:
        wins = sum(1 for s in actionable
                   if (s["action"] == "BUY_YES" and s["outcome"] == 1.0)
                   or (s["action"] == "BUY_NO" and s["outcome"] == 0.0))
        print(f"\nActionable trades: {len(actionable)} signals, {wins} correct = {wins/len(actionable):.0%} hit rate")

        # Simulated P&L (buy at market price, resolve at 0 or 1)
        pnl = 0.0
        for s in actionable:
            if s["action"] == "BUY_YES":
                pnl += (s["outcome"] - s["market_prob"])  # profit per $1 of YES
            elif s["action"] == "BUY_NO":
                pnl += ((1 - s["outcome"]) - (1 - s["market_prob"]))
        print(f"Simulated P&L (per $1 position): ${pnl:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score WeatherNext Pro predictions")
    parser.add_argument("--by-city", action="store_true", help="Breakdown by city")
    parser.add_argument("--by-bracket", action="store_true", help="Breakdown by bracket type")
    args = parser.parse_args()

    signals = load_resolved()

    if args.by_city:
        report(signals, group_key="city")
    elif args.by_bracket:
        report(signals, group_key="bracket_type")
    else:
        report(signals)
