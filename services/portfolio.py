"""
Portfolio tracker: simulates live trading with position limits and risk management.
Tracks open positions, P&L, and enforces max exposure rules.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


@dataclass
class Position:
    """Open trade position."""
    market_id: str
    city: str
    question: str
    action: str  # "BUY_YES" or "BUY_NO"
    entry_price: float
    entry_size: float  # USDC
    entry_time: str
    our_prob: float
    market_prob: float
    edge_pct: float


@dataclass
class Portfolio:
    """Track open positions and P&L."""
    positions: list[Position] = field(default_factory=list)
    cash: float = 1000.0  # Starting capital in USDC
    max_position_size: float = 50.0  # Max per trade
    max_total_exposure: float = 500.0  # Max total at risk
    max_daily_loss: float = 100.0  # Stop loss per day
    daily_loss: float = 0.0

    def can_trade(self, size: float) -> tuple[bool, str]:
        """Check if we can execute this trade."""
        # Check individual position size
        if size > self.max_position_size:
            return False, f"Position ${size:.0f} exceeds max ${self.max_position_size:.0f}"

        # Check total exposure
        total_exposure = sum(p.entry_size for p in self.positions) + size
        if total_exposure > self.max_total_exposure:
            return False, f"Total exposure ${total_exposure:.0f} exceeds max ${self.max_total_exposure:.0f}"

        # Check cash
        if size > self.cash:
            return False, f"Insufficient cash: ${self.cash:.0f} < ${size:.0f}"

        # Check daily loss limit
        if self.daily_loss >= self.max_daily_loss:
            return False, f"Daily loss limit hit: ${self.daily_loss:.0f} >= ${self.max_daily_loss:.0f}"

        return True, ""

    def add_position(self, pos: Position) -> None:
        """Open a new position."""
        self.positions.append(pos)
        self.cash -= pos.entry_size
        logger.info(f"LIVE: Opened {pos.action} {pos.city} | ${pos.entry_size:.0f} @ {pos.entry_price:.3f}")

    def close_position(self, market_id: str, exit_price: float, outcome: int) -> Optional[float]:
        """
        Close a position and realize P&L.
        outcome: 1 if YES won, 0 if NO won.
        Returns realized P&L in USDC.
        """
        pos = next((p for p in self.positions if p.market_id == market_id), None)
        if not pos:
            return None

        # Calculate P&L based on action and outcome
        if pos.action == "BUY_YES":
            # Bought YES: profit if outcome=1
            pnl = pos.entry_size * (exit_price - pos.entry_price) if outcome == 1 else -pos.entry_size * pos.entry_price
        else:  # BUY_NO
            # Bought NO: profit if outcome=0
            pnl = pos.entry_size * (exit_price - pos.entry_price) if outcome == 0 else -pos.entry_size * pos.entry_price

        self.positions.remove(pos)
        self.cash += pos.entry_size + pnl
        if pnl < 0:
            self.daily_loss += abs(pnl)

        logger.info(f"LIVE: Closed {pos.action} {pos.city} | P&L: ${pnl:+.0f} | Cash: ${self.cash:.0f}")
        return pnl

    def get_summary(self) -> dict:
        """Return portfolio snapshot."""
        return {
            "cash": round(self.cash, 2),
            "open_positions": len(self.positions),
            "total_exposure": round(sum(p.entry_size for p in self.positions), 2),
            "daily_loss": round(self.daily_loss, 2),
            "positions": [
                {
                    "city": p.city,
                    "action": p.action,
                    "size": p.entry_size,
                    "entry_price": p.entry_price,
                    "edge": p.edge_pct,
                }
                for p in self.positions
            ],
        }
