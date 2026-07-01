"""G - Geography.  Where to trade (Chapter 12).

The book's league selection rules, encoded. Each country carries:

* a **tier**   - how much the book trusts it,
* a **bias**   - GOALS (look for overs), UNDERS (look for unders, e.g. Japan),
                 or NEUTRAL,
* a **note**   - the book's own reasoning.

Golden rule of thumb from the book:
    "If the country has at least one representative in the Champions League,
     they're a good nation to trade... (Except Russia)."

And, importantly:
    "Mens Domestic Matches Only!  No cups, No friendlies, No replays,
     No Internationals."
"""

from __future__ import annotations

from dataclasses import dataclass

# Tiers, best -> worst.
CORE = "core"        # top European leagues - trade freely
MIDDLE = "middle"    # goal-fest middle tier - a lot of the profit lives here
STRICT = "strict"    # only the big games, all S.T.R.I.N.G criteria must be met
AVOID = "avoid"      # the book stays away
UNKNOWN = "unknown"  # not covered - treat with maximum caution

# Bias.
GOALS = "goals"
UNDERS = "unders"
NEUTRAL = "neutral"

# Competition types - only domestic league is on-method.
TRADEABLE_COMPETITIONS = {"domestic", "league"}
OFF_METHOD_COMPETITIONS = {"cup", "friendly", "replay", "international"}


def _c(country, tier, bias, note):
    return (country.lower(), {"country": country, "tier": tier, "bias": bias, "note": note})


COUNTRIES = dict(
    [
        # --- Core European leagues (top 3 tiers; more caution lower down) ---
        _c("England", CORE, GOALS, "Trade freely. More even money distribution than Spain."),
        _c("Italy", CORE, GOALS, "Top European league, trade freely."),
        _c("Spain", CORE, GOALS, "Trade freely, but big-2 dominance makes some games very one-sided."),
        _c("France", CORE, GOALS, "Top European league, trade freely."),
        _c("Portugal", CORE, GOALS, "Top European league, trade freely."),
        _c("Germany", CORE, GOALS, "Major European league (UCL nation), solid to trade."),
        _c("Netherlands", CORE, GOALS, "Major European league (UCL nation), solid to trade."),
        # --- Middle tier - goal-fests, big class gaps, majority of the profit ---
        _c("Austria", MIDDLE, GOALS, "Middle-tier goal-fest."),
        _c("Croatia", MIDDLE, GOALS, "Middle-tier goal-fest."),
        _c("Belgium", MIDDLE, GOALS, "Middle-tier goal-fest."),
        _c("Finland", MIDDLE, GOALS, "Middle-tier goal-fest; big gulf in class."),
        _c("Turkey", MIDDLE, GOALS, "Middle-tier goal-fest; TIGER fires here often."),
        _c("Norway", MIDDLE, GOALS, "Middle-tier goal-fest; big gulf in class."),
        _c("Switzerland", MIDDLE, GOALS, "Middle-tier goal-fest; huge haves/have-nots gap."),
        _c("Denmark", MIDDLE, GOALS, "Middle-tier goal-fest; Midtjylland a favourite."),
        _c("Greece", MIDDLE, GOALS, "Middle-tier goal-fest."),
        _c("Sweden", MIDDLE, GOALS, "Middle-tier goal-fest; big gulf in class."),
        _c("Iceland", MIDDLE, GOALS, "Middle-tier goal-fest."),
        # --- Middle East / North Africa - only the big games, strict criteria ---
        _c("Egypt", STRICT, GOALS, "Only big games; TIGER's been a strong performer here."),
        _c("Israel", STRICT, GOALS, "Only big games, all criteria met."),
        _c("Libya", STRICT, GOALS, "Only big games, all criteria met."),
        _c("Algeria", STRICT, GOALS, "Only big games, all criteria met."),
        _c("Tunisia", STRICT, GOALS, "Only big games, all criteria met."),
        _c("Malta", STRICT, GOALS, "Only big games, all criteria met."),
        _c("Morocco", STRICT, GOALS, "Only big games, all criteria met."),
        # --- Asia ---
        _c("Japan", CORE, UNDERS, "Conservative league - BACK UNDERS when form shows 1s and 0s. Opposite of everywhere else."),
        _c("South Korea", MIDDLE, GOALS, "Good for goals; TIGER fires often (e.g. Pohang Steelers)."),
        # --- Oceania ---
        _c("Australia", MIDDLE, GOALS, "Most profitable of all per the book; first-half goal markets. Note: few games on Betfair (use Bet365)."),
        # --- North America ---
        _c("USA", STRICT, GOALS, "MLS is generally sound; avoid lower US leagues (crap shoot)."),
        _c("Canada", STRICT, GOALS, "MLS-level only; treat lower divisions with caution."),
        _c("Mexico", MIDDLE, GOALS, "West-of-the-Americas pick the book trades."),
        # --- South America - ONLY 'the West' ---
        _c("Cuba", STRICT, GOALS, "West Americas - tradeable with strict criteria."),
        _c("Peru", MIDDLE, GOALS, "One of the book's favourites in South America."),
        _c("Venezuela", STRICT, GOALS, "West Americas - tradeable with strict criteria."),
        _c("Ecuador", STRICT, GOALS, "West Americas - tradeable with strict criteria."),
        # --- Explicit AVOID list ---
        _c("Russia", AVOID, NEUTRAL, "Don't touch with your longest barge pole."),
        _c("Brazil", AVOID, NEUTRAL, "Unpredictable; lower/U20 leagues especially. Book loses money here."),
        _c("Argentina", AVOID, NEUTRAL, "Steer well clear (South America, not 'the West')."),
        _c("Uruguay", AVOID, NEUTRAL, "Steer well clear (South America, not 'the West')."),
        _c("Paraguay", AVOID, NEUTRAL, "Steer well clear (South America, not 'the West')."),
        _c("China", AVOID, NEUTRAL, "A minefield."),
        _c("Belarus", AVOID, NEUTRAL, "Minor institutional interest / financial structure."),
        _c("Estonia", AVOID, NEUTRAL, "Minor institutional interest / financial structure."),
        _c("Romania", AVOID, NEUTRAL, "Tread very carefully - book errs away."),
        _c("South Africa", AVOID, NEUTRAL, "Stats often tempting but book stays away without local knowledge."),
    ]
)


@dataclass
class GeographyVerdict:
    country: str
    tier: str
    bias: str
    note: str
    tradeable: bool

    @property
    def summary(self) -> str:
        icon = {CORE: "✅", MIDDLE: "✅", STRICT: "⚠️", AVOID: "❌", UNKNOWN: "❓"}[self.tier]
        bias_txt = {
            GOALS: "look for OVERS/goals",
            UNDERS: "look for UNDERS",
            NEUTRAL: "-",
        }[self.bias]
        return f"{icon} {self.country} [{self.tier}] {bias_txt} — {self.note}"


def assess_country(country: str) -> GeographyVerdict:
    """Look up the book's stance on a country."""
    entry = COUNTRIES.get((country or "").strip().lower())
    if entry is None:
        return GeographyVerdict(
            country=country,
            tier=UNKNOWN,
            bias=NEUTRAL,
            note="Not in the book's list. The lesser you know a league, the stronger the "
            "criteria must be. Default: leave it alone.",
            tradeable=False,
        )
    return GeographyVerdict(
        country=entry["country"],
        tier=entry["tier"],
        bias=entry["bias"],
        note=entry["note"],
        tradeable=entry["tier"] in (CORE, MIDDLE, STRICT),
    )


def is_tradeable_competition(competition_type: str) -> bool:
    """Men's domestic league only: no cups, friendlies, replays or internationals."""
    return (competition_type or "").strip().lower() in TRADEABLE_COMPETITIONS
