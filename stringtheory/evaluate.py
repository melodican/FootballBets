"""The full S.T.R.I.N.G checklist -> a GO / CONSIDER / NO-GO verdict.

    S - Stats        (in-play: dangerous attacks, shots, possession)
    T - Time         (2nd half for goals; 45-75 min sweet spot)
    R - Recent form  (last-5 goals; % of games with a goal after this minute)
    I - Intent       (motivation: fixtures, points, competition)
    N - Numbers      (offered price beats the price your strike rate needs)
    G - Geography    (a league the book actually trades, right bias)

Feed in what you can see across Bet365 / Flashscore / Betfair and the engine
builds the "jigsaw" the book keeps talking about: the more pieces that line up,
the stronger the trade. It never bets for you - it enforces the checklist so
you don't blow your load on one compelling piece of the puzzle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import geography, numbers

# Verdicts.
GO = "GO"
CONSIDER = "CONSIDER"
NO_GO = "NO-GO"

# A single check's status.
PASS = "pass"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    letter: str
    status: str
    message: str

    @property
    def icon(self) -> str:
        return {PASS: "✅", WARN: "⚠️", FAIL: "❌"}[self.status]


@dataclass
class MatchContext:
    """Everything the engine needs to weigh a trade. Unknown fields can be None."""

    # G + T + competition
    country: str
    competition_type: str = "domestic"     # domestic | cup | friendly | replay | international
    minute: Optional[int] = None
    home_score: int = 0
    away_score: int = 0
    market: str = "Over 0.5 Goals"          # free text; "under" in the name flags an unders play

    # S - in-play stats (Bet365)
    dangerous_attacks_home: Optional[int] = None
    dangerous_attacks_away: Optional[int] = None
    shots_home: Optional[int] = None
    shots_away: Optional[int] = None
    possession_home: Optional[float] = None  # percent 0-100

    # R - recent form (Flashscore)
    goal_after_minute_pct: Optional[float] = None   # % of last-5 games with a goal after `minute`
    over_line_pct: Optional[float] = None           # % of recent games hitting the market line

    # I - intent
    intent_note: str = ""

    # N - numbers
    strike_rate: Optional[float] = None    # your estimate (0-1 or 0-100)
    offered_price: Optional[float] = None
    commission: float = numbers.DEFAULT_COMMISSION

    @property
    def total_goals(self) -> int:
        return self.home_score + self.away_score

    @property
    def is_under_market(self) -> bool:
        return "under" in self.market.lower()


@dataclass
class Evaluation:
    verdict: str
    checks: List[Check] = field(default_factory=list)
    value: Optional[numbers.ValueVerdict] = None
    reasons: List[str] = field(default_factory=list)

    @property
    def fails(self) -> int:
        return sum(1 for c in self.checks if c.status == FAIL)

    @property
    def warns(self) -> int:
        return sum(1 for c in self.checks if c.status == WARN)

    def describe(self) -> str:
        head = {GO: "🟢 GO", CONSIDER: "🟡 CONSIDER", NO_GO: "🔴 NO-GO"}[self.verdict]
        lines = [f"{head}  —  {self.summary_line()}", ""]
        for c in self.checks:
            lines.append(f"  {c.icon} {c.letter}: {c.message}")
        if self.value:
            lines += ["", f"  {self.value.summary}"]
        return "\n".join(lines)

    def summary_line(self) -> str:
        return f"{self.fails} fail(s), {self.warns} warning(s) across the 6 pieces of the jigsaw."


def _check_geography(ctx: MatchContext) -> Check:
    if not geography.is_tradeable_competition(ctx.competition_type):
        return Check(
            "G",
            FAIL,
            f"'{ctx.competition_type}' is off-method. The book trades men's DOMESTIC "
            "leagues only — no cups, friendlies, replays or internationals.",
        )
    geo = geography.assess_country(ctx.country)
    if geo.tier == geography.AVOID:
        return Check("G", FAIL, f"{geo.summary}")
    if geo.tier in (geography.STRICT, geography.UNKNOWN):
        return Check("G", WARN, f"{geo.summary}")
    return Check("G", PASS, f"{geo.summary}")


def _check_time(ctx: MatchContext) -> Check:
    if ctx.minute is None:
        return Check("T", WARN, "No match minute given — can't judge timing.")
    if ctx.is_under_market:
        # Book: backing unders ~30 min at 0-0 in conservative games.
        if ctx.minute <= 35 and ctx.total_goals == 0:
            return Check("T", PASS, f"{ctx.minute}' and 0-0 — a classic window for an UNDERS play.")
        return Check("T", WARN, f"{ctx.minute}' — unders plays are best earlier (~30') at 0-0.")
    # Goal markets: second half, 45-75 sweet spot, can stretch to ~85 if watching.
    if 45 <= ctx.minute <= 75:
        return Check("T", PASS, f"{ctx.minute}' — in the 45-75' goal-market sweet spot.")
    if ctx.minute < 45:
        return Check("T", WARN, f"{ctx.minute}' — book waits for the 2nd half for goal markets.")
    if ctx.minute <= 85:
        return Check("T", WARN, f"{ctx.minute}' — late; only fire if you're watching and it's all-out attack.")
    return Check("T", FAIL, f"{ctx.minute}' — too late; the price rarely justifies the risk.")


def _check_stats(ctx: MatchContext) -> Check:
    if ctx.minute is None or (
        ctx.dangerous_attacks_home is None and ctx.shots_home is None
    ):
        return Check("S", WARN, "No in-play stats given — can't confirm intent on the pitch.")

    notes: List[str] = []
    status = PASS

    da = [x for x in (ctx.dangerous_attacks_home, ctx.dangerous_attacks_away) if x is not None]
    if da and ctx.minute:
        # Book: like to see dangerous attacks near/above the match minutes.
        if max(da) >= ctx.minute:
            notes.append(f"dangerous attacks ({max(da)}) ≥ minute ({ctx.minute})")
        else:
            notes.append(f"dangerous attacks ({max(da)}) below minute ({ctx.minute}) — mini red flag")
            status = WARN

    shots = [x for x in (ctx.shots_home, ctx.shots_away) if x is not None]
    if shots:
        total_shots = sum(shots)
        projected = round(total_shots * 90 / ctx.minute) if ctx.minute else total_shots
        notes.append(f"{total_shots} shots (~{projected} projected full-time)")
        if not ctx.is_under_market and projected < 15:
            notes.append("low shot volume for a goals play")
            status = WARN if status == PASS else status

    if ctx.possession_home is not None:
        dom = max(ctx.possession_home, 100 - ctx.possession_home)
        if dom >= 60:
            notes.append(f"clear possession dominance ({dom:.0f}%)")
        else:
            notes.append(f"even possession ({ctx.possession_home:.0f}%) — no one in control")

    return Check("S", status, "; ".join(notes))


def _check_form(ctx: MatchContext) -> Check:
    if ctx.goal_after_minute_pct is None and ctx.over_line_pct is None:
        return Check("R", WARN, "No recent-form % given — the glue that holds the jigsaw together.")
    bits = []
    if ctx.goal_after_minute_pct is not None:
        bits.append(f"{ctx.goal_after_minute_pct:.0f}% of last-5 had a goal after this minute")
    if ctx.over_line_pct is not None:
        bits.append(f"{ctx.over_line_pct:.0f}% of recent games hit the line")
    strong = max(v for v in (ctx.goal_after_minute_pct, ctx.over_line_pct) if v is not None)
    status = PASS if strong >= 70 else WARN
    return Check("R", status, "; ".join(bits))


def _check_intent(ctx: MatchContext) -> Check:
    if not ctx.intent_note:
        return Check("I", WARN, "No intent note. Ask: what's the motivation here? (fixtures, points, competition)")
    return Check("I", PASS, ctx.intent_note)


def _check_numbers(ctx: MatchContext) -> tuple[Check, Optional[numbers.ValueVerdict]]:
    if ctx.strike_rate is None or ctx.offered_price is None:
        return Check("N", WARN, "No strike-rate estimate and/or price — can't check value."), None
    value = numbers.assess_value(ctx.strike_rate, ctx.offered_price, ctx.commission)
    status = PASS if value.is_value else FAIL
    return Check("N", status, value.summary), value


def evaluate(ctx: MatchContext) -> Evaluation:
    """Run the S.T.R.I.N.G checklist and return an overall verdict.

    Rules for the verdict:
      * Any FAIL on G (wrong league/competition) or N (no value) => NO-GO.
        Those two are non-negotiable: the book never trades a league it avoids
        and never takes a price below what the strike rate needs.
      * Otherwise any FAIL, or 3+ warnings => CONSIDER (do more research).
      * A clean-enough jigsaw => GO.
    """
    stats = _check_stats(ctx)
    time = _check_time(ctx)
    form = _check_form(ctx)
    intent = _check_intent(ctx)
    numbers_check, value = _check_numbers(ctx)
    geo = _check_geography(ctx)

    checks = [stats, time, form, intent, numbers_check, geo]

    hard_fail = (geo.status == FAIL) or (numbers_check.status == FAIL)
    reasons: List[str] = []

    if hard_fail:
        verdict = NO_GO
        if geo.status == FAIL:
            reasons.append("Geography/competition rule broken — off-method.")
        if numbers_check.status == FAIL:
            reasons.append("No value — the price doesn't beat your strike rate.")
    elif any(c.status == FAIL for c in checks) or sum(1 for c in checks if c.status == WARN) >= 3:
        verdict = CONSIDER
        reasons.append("Jigsaw incomplete — gather the missing pieces before entering.")
    else:
        verdict = GO
        reasons.append("The pieces line up. Trust the reading and follow your staking plan.")

    return Evaluation(verdict=verdict, checks=checks, value=value, reasons=reasons)
