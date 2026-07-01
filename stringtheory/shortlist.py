"""Daily "Watch These Games" shortlist — STRING steps T + G + R, automated.

Given today's fixtures with each side's league position, goals record and recent
form, this ranks the best **Top vs Whipping Boys** opportunities in the leagues
your book actually trades, and tells you the angle (goals, or unders for Japan).

It is a *pre-match funnel*: it points you at on-method games worth opening on
Bet365/Flashscore. The in-play S.T.R.I.N.G read (evaluate.py) still decides
whether you pull the trigger.

The scoring is deliberately transparent — every item carries the reasons behind
its score, because the book is all about understanding the jigsaw, not a black box.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional

from . import geography


@dataclass
class TeamForm:
    name: str
    rank: Optional[int] = None          # league position (1 = top)
    points: Optional[int] = None
    played: int = 0
    goals_for: int = 0
    goals_against: int = 0
    form: str = ""                      # recent results, most recent last, e.g. "WWDLW"

    @property
    def gf_pg(self) -> float:
        return self.goals_for / self.played if self.played else 0.0

    @property
    def ga_pg(self) -> float:
        return self.goals_against / self.played if self.played else 0.0

    def form_points(self, last: int = 5) -> int:
        pts = {"W": 3, "D": 1, "L": 0}
        return sum(pts.get(c, 0) for c in self.form[-last:].upper())

    def wins(self, last: int = 5) -> int:
        return self.form[-last:].upper().count("W")


@dataclass
class Fixture:
    league_name: str
    country: str
    competition_type: str               # "league" | "cup" | "international"
    home: TeamForm
    away: TeamForm
    kickoff: str = ""                    # ISO time or "HH:MM"
    league_size: int = 20               # teams in the division (for gap scaling)


def fixture_from_dict(d: dict) -> "Fixture":
    """Build a Fixture from a plain dict (normalised JSON cache)."""
    def team(t: dict) -> TeamForm:
        return TeamForm(
            name=t.get("name", "?"), rank=t.get("rank"), points=t.get("points"),
            played=t.get("played", 0), goals_for=t.get("goals_for", 0),
            goals_against=t.get("goals_against", 0), form=t.get("form", ""),
        )
    return Fixture(
        league_name=d.get("league_name", "?"), country=d.get("country", "?"),
        competition_type=d.get("competition_type", "league"),
        home=team(d.get("home", {})), away=team(d.get("away", {})),
        kickoff=d.get("kickoff", ""), league_size=d.get("league_size", 20),
    )


def load_fixtures_json(path: str) -> List["Fixture"]:
    with open(path, encoding="utf-8") as fh:
        return [fixture_from_dict(d) for d in json.load(fh)]


@dataclass
class ShortlistItem:
    fixture: Fixture
    score: float                        # 0-100 watch score
    angle: str                          # what to look to trade
    favourite: str                      # team name, or "" if even
    reasons: List[str] = field(default_factory=list)
    off_method: bool = False
    skip_reason: str = ""

    @property
    def match(self) -> str:
        return f"{self.fixture.home.name} v {self.fixture.away.name}"

    @property
    def summary(self) -> str:
        ko = f"{self.fixture.kickoff}  " if self.fixture.kickoff else ""
        return (
            f"{self.score:>5.0f}  {ko}{self.match:<34} "
            f"[{self.fixture.country}] — {self.angle}"
        )


# --- scoring helpers ---------------------------------------------------------

def _goals_expectancy(fx: Fixture) -> float:
    """Rough expected total goals: each side's attack vs the other's defence."""
    exp_home = (fx.home.gf_pg + fx.away.ga_pg) / 2
    exp_away = (fx.away.gf_pg + fx.home.ga_pg) / 2
    return exp_home + exp_away


def _mismatch(fx: Fixture) -> tuple[float, Optional[TeamForm]]:
    """Return (0-1 mismatch strength, favourite team) from league positions."""
    h, a = fx.home.rank, fx.away.rank
    if h is None or a is None:
        return 0.0, None
    gap = abs(a - h)
    strength = min(1.0, gap / max(1, fx.league_size - 1))
    favourite = fx.home if h < a else fx.away
    return strength, favourite


def _form_alignment(fx: Fixture, favourite: Optional[TeamForm]) -> float:
    """0-1: is the favourite in good nick and the underdog struggling, cleanly?

    The book warns against sporadic form (WLDWL). Reward the favourite winning
    most of the last 5 and the underdog losing most of them.
    """
    if favourite is None:
        return 0.0
    underdog = fx.away if favourite is fx.home else fx.home
    fav_ok = favourite.wins() / 5.0                 # more wins = better
    dog_bad = (5 - underdog.wins()) / 5.0            # fewer underdog wins = better
    return (fav_ok + dog_bad) / 2


def score_fixture(fx: Fixture) -> ShortlistItem:
    """Score a single fixture and produce its angle + reasons."""
    geo = geography.assess_country(fx.country)

    # Hard on-method gate.
    if not geography.is_tradeable_competition(fx.competition_type):
        return ShortlistItem(fx, 0.0, "SKIP — off-method competition", "",
                             off_method=True,
                             skip_reason=f"{fx.competition_type} (domestic leagues only)")
    if not geo.tradeable:
        return ShortlistItem(fx, 0.0, f"SKIP — {geo.tier} league", "",
                             off_method=True, skip_reason=geo.note)

    ge = _goals_expectancy(fx)
    mismatch, favourite = _mismatch(fx)
    form = _form_alignment(fx, favourite)
    reasons: List[str] = []

    if favourite is not None:
        reasons.append(
            f"Top vs Whipping Boys: {favourite.name} favoured "
            f"(#{fx.home.rank} v #{fx.away.rank}, gap {abs((fx.away.rank or 0)-(fx.home.rank or 0))})"
        )
    reasons.append(f"~{ge:.1f} expected goals ({fx.home.gf_pg:.1f}+{fx.away.gf_pg:.1f} for, "
                   f"{fx.home.ga_pg:.1f}/{fx.away.ga_pg:.1f} against)")
    if favourite is not None:
        reasons.append(f"Form: {favourite.name} {favourite.form[-5:]} vs "
                       f"{(fx.away if favourite is fx.home else fx.home).form[-5:]}")

    if geo.bias == geography.UNDERS:
        # Japan: reward LOW goals expectancy, angle is unders.
        ge_component = max(0.0, min(1.0, (2.6 - ge) / 1.6))   # ~1.0 at GE<=1.0, ~0 at GE>=2.6
        angle = "UNDERS lean (conservative league) — watch for 1-0/0-0 setups"
        strict_note = "" if geo.tier != geography.STRICT else " [strict: big games only]"
    else:
        ge_component = max(0.0, min(1.0, (ge - 1.8) / 2.2))   # ~0 at GE<=1.8, ~1.0 at GE>=4.0
        side = "back the favourite / lay the underdog + goals" if favourite is not None else "goals market"
        angle = f"GOALS + {side}"
        strict_note = "" if geo.tier != geography.STRICT else " [strict: big games only]"

    # Weighted, transparent score.
    score = 100 * (0.40 * ge_component + 0.30 * mismatch + 0.30 * form)
    if geo.tier == geography.STRICT:
        score *= 0.85   # be pickier in strict leagues

    return ShortlistItem(
        fixture=fx,
        score=round(score, 1),
        angle=angle + strict_note,
        favourite=favourite.name if favourite else "",
        reasons=reasons,
    )


def build_shortlist(fixtures: List[Fixture], min_score: float = 0.0) -> List[ShortlistItem]:
    """Score all fixtures, drop off-method ones, and rank best-first."""
    items = [score_fixture(fx) for fx in fixtures]
    live = [it for it in items if not it.off_method and it.score >= min_score]
    live.sort(key=lambda it: it.score, reverse=True)
    return live


def format_shortlist(fixtures: List[Fixture], top: int = 15, min_score: float = 0.0,
                     show_reasons: bool = True) -> str:
    items = [score_fixture(fx) for fx in fixtures]
    live = [it for it in items if not it.off_method and it.score >= min_score]
    skipped = [it for it in items if it.off_method]
    live.sort(key=lambda it: it.score, reverse=True)

    lines = [
        "=" * 68,
        "WATCH THESE GAMES  —  Top vs Whipping Boys shortlist",
        "=" * 68,
    ]
    if not live:
        lines.append("No on-method games cleared the bar today.")
    for it in live[:top]:
        lines.append(it.summary)
        if show_reasons:
            for r in it.reasons:
                lines.append(f"        · {r}")
    if skipped:
        lines.append("")
        lines.append(f"Skipped {len(skipped)} off-method game(s): "
                     + ", ".join(sorted({f'{it.match} ({it.skip_reason})' for it in skipped}))[:400])
    return "\n".join(lines)


def format_telegram(fixtures: List[Fixture], top: int = 8, min_score: float = 0.0,
                    header: str = "Watch These Games") -> str:
    """A compact message for Oracle to push to Telegram (short, scannable)."""
    live = build_shortlist(fixtures, min_score=min_score)
    n_skip = sum(1 for fx in fixtures if score_fixture(fx).off_method)
    if not live:
        return (f"⚽ *{header}*\nNo on-method games today"
                + (f" ({n_skip} off-method skipped)." if n_skip else "."))
    out = [f"⚽ *{header}*"]
    for i, it in enumerate(live[:top], 1):
        fire = "🔥" if it.score >= 80 else ("✅" if it.score >= 60 else "•")
        bias = "UNDERS" if "UNDERS" in it.angle else "GOALS"
        out.append(f"{i}. {fire}{it.score:.0f} {it.match} ({it.fixture.country}) — {bias}")
    if n_skip:
        out.append(f"_{n_skip} off-method skipped._")
    return "\n".join(out)
