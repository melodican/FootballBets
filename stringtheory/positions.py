"""In-play discipline guardrail — the leak-plugger.

Your real data showed two recurring, expensive mistakes, both when a bet was a
directional punt rather than a traded position:

1. **No exit** — bets let ride to a full loss (Germany −£355, Juventus −£235).
2. **Correlated stacking** — Germany Match Odds *and* Germany −1.5 both ride on
   Germany; one upset sank both (−£605 together).

This module is what Oracle runs before you enter a bet. Given your bankroll and
what's already open, it:

* sizes the stake from the Golden Equation,
* checks the price is value for your strike rate,
* **requires a pre-set exit** on any directional (let-ride) back,
* **flags correlated stacking** on the same team across outcome markets —
  but does NOT nag your goal-ladder (multiple Over lines), which is your
  proven winning style.

Oracle holds the state (your open positions) and passes it in; the maths and the
rules live here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from . import numbers, staking

# Markets whose result rides on a TEAM's outcome — stacking these on the same
# team is correlated (the Germany mistake).
TEAM_OUTCOME_MARKETS = (
    "match odds", "asian handicap", "handicap", "draw no bet",
    "to qualify", "half time", "double chance", "win",
)
# Goal markets — laddering multiple Over lines on one game is fine (your style).
GOAL_MARKETS = ("over", "under", "goal", "goals")

PROCEED, CAUTION, BLOCK = "PROCEED", "CAUTION", "BLOCK"


@dataclass
class Position:
    match: str
    selection: str                 # "Germany", "Germany -1.5", "Over 2.5", ...
    market: str                    # "Match Odds", "Asian Handicap", "Over/Under 2.5 Goals"
    side: str = "back"             # back | lay
    stake: float = 0.0
    price: Optional[float] = None
    exit_price: Optional[float] = None
    exit_minute: Optional[int] = None

    @property
    def is_team_outcome(self) -> bool:
        m = self.market.lower()
        return any(k in m for k in TEAM_OUTCOME_MARKETS) and not self._is_goal_market

    @property
    def _is_goal_market(self) -> bool:
        m = self.market.lower()
        return any(k in m for k in GOAL_MARKETS)

    @property
    def team_root(self) -> str:
        """The team a selection is on, minus any handicap suffix. '' for goal bets."""
        if self._is_goal_market:
            return ""
        # strip trailing handicap like " -1.5" / " +0.5"
        return re.sub(r"\s*[+-]?\d+(\.\d+)?\s*$", "", self.selection).strip().lower()

    @property
    def has_exit(self) -> bool:
        return self.exit_price is not None or self.exit_minute is not None


@dataclass
class EntryProposal:
    candidate: Position
    recommended_unit: float
    verdict: str
    value: Optional[numbers.ValueVerdict] = None
    correlation_warnings: List[str] = field(default_factory=list)
    staking_warnings: List[str] = field(default_factory=list)
    requires_exit: bool = True

    @property
    def telegram(self) -> str:
        icon = {PROCEED: "🟢", CAUTION: "🟡", BLOCK: "🔴"}[self.verdict]
        lines = [f"{icon} *{self.verdict}* — {self.candidate.selection} "
                 f"({self.candidate.market}) @ {self.candidate.price}"]
        lines.append(f"Stake: £{self.recommended_unit:.2f} (1 unit)")
        if self.value:
            lines.append(("✅ value" if self.value.is_value else "❌ no value")
                         + f": need {self.value.required_price:.2f}, got {self.candidate.price}")
        for w in self.correlation_warnings:
            lines.append(f"⚠️ {w}")
        for w in self.staking_warnings:
            lines.append(f"⚠️ {w}")
        if self.requires_exit:
            lines.append("📌 Set your exit BEFORE you enter (price or minute to red up).")
        return "\n".join(lines)


def _correlation_warnings(candidate: Position, open_positions: List[Position]) -> List[str]:
    warnings: List[str] = []
    if not candidate.is_team_outcome:
        return warnings   # goal-ladder entries are fine, don't nag
    root = candidate.team_root
    for p in open_positions:
        if p.match.strip().lower() != candidate.match.strip().lower():
            continue
        if p.is_team_outcome and p.team_root == root and root:
            warnings.append(
                f"CORRELATED: already on {p.selection} ({p.market}) in this match. "
                f"Backing {candidate.selection} too is one bet in two coats — "
                f"an upset sinks both. This is the Germany −£605 pattern."
            )
    return warnings


def propose_entry(
    bankroll: float,
    candidate: Position,
    open_positions: Optional[List[Position]] = None,
    frontline_pct: float = 0.10,
    strike_rate: Optional[float] = None,
    commission: float = 0.0,
) -> EntryProposal:
    """Vet a proposed entry against staking, value and correlation rules."""
    open_positions = open_positions or []
    plan = staking.StakingPlan(bankroll=bankroll, frontline_pct=frontline_pct)

    value = None
    if strike_rate is not None and candidate.price:
        value = numbers.assess_value(strike_rate, candidate.price, commission)

    corr = _correlation_warnings(candidate, open_positions)
    stake_warn = list(plan.warnings)

    # A directional back with no plan to trade out MUST carry an exit.
    requires_exit = candidate.side == "back" and not candidate.has_exit

    if value is not None and not value.is_value:
        verdict = BLOCK                      # no value → no bet, full stop
    elif corr:
        verdict = CAUTION                    # correlated stack → make Glen confirm
    elif stake_warn:
        verdict = CAUTION
    else:
        verdict = PROCEED

    return EntryProposal(
        candidate=candidate,
        recommended_unit=plan.unit,
        verdict=verdict,
        value=value,
        correlation_warnings=corr,
        staking_warnings=stake_warn,
        requires_exit=requires_exit,
    )
