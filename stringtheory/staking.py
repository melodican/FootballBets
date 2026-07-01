"""The Golden Equation - staking (Chapter 14).

    Bankroll  ->  Frontline  ->  Cycle (10 trades)  ->  Unit

* **Bankroll**  - whatever is in your Betfair account right now.
* **Frontline** - the slice you are willing to risk over the next cycle.
                  Start at 10% of bankroll. Slide up to 25% when consistently
                  profitable. NEVER past ~30% ("really, no more than 30% at an
                  extreme push").
* **Cycle**     - a block of 10 trades.
* **Unit**      - one trade = 10% of the frontline. This MUST stay constant for
                  the whole cycle. Firing 3 times on one market = 3 units.

The whole point is to make revenge-betting and emotional stake-hiking
impossible. Discipline wins this game, not feelings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

UNITS_PER_CYCLE = 10
RECOMMENDED_MAX_FRONTLINE = 0.25   # book: slide up to 25% when strong
HARD_MAX_FRONTLINE = 0.30          # book: never past ~30%, extreme push only


@dataclass
class StakingPlan:
    """A frontline/cycle/unit plan derived from a bankroll."""

    bankroll: float
    frontline_pct: float = 0.10

    def __post_init__(self) -> None:
        if self.bankroll <= 0:
            raise ValueError("bankroll must be > 0")
        if not 0 < self.frontline_pct <= 1:
            raise ValueError("frontline_pct must be a fraction in (0, 1]")

    @property
    def frontline(self) -> float:
        return round(self.bankroll * self.frontline_pct, 2)

    @property
    def unit(self) -> float:
        """One unit = 10% of the frontline = the stake for every trade in a cycle."""
        return round(self.frontline / UNITS_PER_CYCLE, 2)

    @property
    def cycle_exposure(self) -> float:
        """Total staked if all 10 units are deployed (the frontline)."""
        return round(self.unit * UNITS_PER_CYCLE, 2)

    @property
    def warnings(self) -> List[str]:
        w: List[str] = []
        if self.frontline_pct > HARD_MAX_FRONTLINE:
            w.append(
                f"Frontline {self.frontline_pct:.0%} is above the book's hard "
                f"ceiling of {HARD_MAX_FRONTLINE:.0%}. This is how banks get blown."
            )
        elif self.frontline_pct > RECOMMENDED_MAX_FRONTLINE:
            w.append(
                f"Frontline {self.frontline_pct:.0%} is above the recommended "
                f"{RECOMMENDED_MAX_FRONTLINE:.0%}. Only go here with a proven strike rate."
            )
        if self.unit <= 0:
            w.append("Unit rounds to £0 - your bankroll is too small for this frontline %.")
        return w

    def describe(self) -> str:
        lines = [
            f"Bankroll:  £{self.bankroll:,.2f}",
            f"Frontline: £{self.frontline:,.2f}  ({self.frontline_pct:.0%} of bankroll)",
            f"Cycle:     {UNITS_PER_CYCLE} trades",
            f"Unit:      £{self.unit:,.2f}  (same stake every trade this cycle)",
        ]
        for warning in self.warnings:
            lines.append(f"⚠️  {warning}")
        return "\n".join(lines)


@dataclass
class CycleTracker:
    """Tracks a live cycle: enforces a constant unit and reports P/L.

    A trade's ``pnl`` is the realised profit (+) or loss (-) for that unit.
    ``stake`` should equal the plan's unit; a mismatch raises, because changing
    your stake mid-cycle breaks the whole system.
    """

    unit: float
    tolerance: float = 0.01
    trades: List[dict] = field(default_factory=list)

    def record(self, pnl: float, stake: float | None = None, note: str = "") -> None:
        if stake is None:
            stake = self.unit
        if abs(stake - self.unit) > self.tolerance:
            raise ValueError(
                f"Stake £{stake:.2f} != unit £{self.unit:.2f}. "
                "The unit MUST stay constant for the whole cycle."
            )
        if self.complete:
            raise ValueError("Cycle already has 10 trades. Start a new cycle.")
        self.trades.append({"pnl": round(pnl, 2), "stake": stake, "note": note})

    @property
    def count(self) -> int:
        return len(self.trades)

    @property
    def complete(self) -> bool:
        return self.count >= UNITS_PER_CYCLE

    @property
    def remaining(self) -> int:
        return max(0, UNITS_PER_CYCLE - self.count)

    @property
    def profit(self) -> float:
        return round(sum(t["pnl"] for t in self.trades), 2)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t["pnl"] > 0)

    @property
    def strike_rate(self) -> float:
        return self.wins / self.count if self.count else 0.0

    @property
    def roi(self) -> float:
        staked = sum(t["stake"] for t in self.trades)
        return self.profit / staked if staked else 0.0

    def describe(self) -> str:
        status = "COMPLETE" if self.complete else f"{self.remaining} trade(s) left"
        return (
            f"Cycle {self.count}/{UNITS_PER_CYCLE} ({status})  "
            f"P/L £{self.profit:+,.2f}  "
            f"Strike {self.strike_rate:.0%}  ROI {self.roi:+.1%}"
        )
