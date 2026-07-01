"""Parse a Betfair 'Exchange Bets — Settled' CSV export and reconstruct
*positions* from their individual back/lay legs.

The export has one row per matched bet (a leg). A position is every leg on the
same match + selection + market. Grouping them lets us see what the raw rows
hide: whether you **traded** a market (backed then laid to green up / scratch)
or **let it ride** as a straight directional bet — and how each style actually
performs.

Reconciliation: Betfair's settled P/L is the sum of a position's leg P/L, with
~2% commission taken on net winnings. That reproduces the figures on the
account statement exactly (verified against Glen's World Cup screenshot).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_COMMISSION = 0.02

_BET_ID_RE = re.compile(r"\s*\|\s*Betfair Bet ID.*$")
# National-team names that appear as "teams" -> the fixture is an international.
_NATIONS = {
    "france", "sweden", "ivory coast", "norway", "germany", "paraguay",
    "brazil", "japan", "panama", "england", "argentina", "spain", "portugal",
    "netherlands", "belgium", "croatia", "morocco", "senegal", "usa", "mexico",
    "uruguay", "switzerland", "denmark", "poland", "wales", "ecuador", "ghana",
    "cameroon", "serbia", "south korea", "canada", "qatar", "tunisia", "iran",
    "costa rica", "saudi arabia", "australia", "italy",
}
# Market phrases that only exist in knockout/cup ties -> off-method.
_CUP_MARKETS = {"to qualify"}


def _to_float(text: str) -> float:
    text = (text or "").strip().strip('"').replace(",", "")
    if text in ("", "--", "-"):
        return 0.0
    return float(text)


@dataclass
class Leg:
    placed: str
    settled: str
    description: str      # full description minus the bet-id tail (the position key)
    match: str            # "Home v Away"
    selection: str
    market: str           # e.g. "Over/Under 2.5 Goals", "Asian Handicap", "Match Odds"
    side: str             # "back" | "lay"
    odds: float
    stake: float
    liability: float
    pnl: float            # gross P/L for this leg (pre-commission)
    status: str           # "Won" | "Lost"
    bet_id: str = ""


def _split_description(raw: str) -> tuple[str, str, str, str]:
    """Return (position_key, match, selection, market) from a raw description.

    Format: "Home v Away Selection-Market | Betfair Bet ID ...".
    Market is the text after the LAST hyphen; the match is the "Home v Away"
    prefix (best-effort); the selection is what sits between.
    """
    key = _BET_ID_RE.sub("", raw).strip()
    body, _, market = key.rpartition("-")
    market = market.strip()
    if not body:                       # no hyphen at all
        body, market = key, ""
    # Best-effort match vs selection split on the last " v " occurrence.
    match = body
    selection = ""
    if " v " in body:
        # away team + selection follow " v "; we keep the whole "Home v Away ..."
        # as match context and treat the trailing words as the selection guess.
        head = body[: body.index(" v ")]
        rest = body[body.index(" v ") + 3:]
        parts = rest.split(" ", 1)
        away = parts[0]
        selection = parts[1] if len(parts) > 1 else ""
        match = f"{head} v {away}"
    return key, match.strip(), selection.strip(), market


def parse_export(path: str) -> List[Leg]:
    legs: List[Leg] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            desc = row.get("Description", "")
            if not desc.strip():
                continue
            key, match, selection, market = _split_description(desc)
            bet_id = ""
            m = re.search(r"Betfair Bet ID\s*(\S+)", desc)
            if m:
                bet_id = m.group(1)
            legs.append(
                Leg(
                    placed=row.get("Placed", "").strip(),
                    settled=row.get("Settled", "").strip(),
                    description=key,
                    match=match,
                    selection=selection,
                    market=market,
                    side=(row.get("Type", "").strip().lower() or "back"),
                    odds=_to_float(row.get("Odds", "")),
                    stake=_to_float(row.get("Stake (£)", "")),
                    liability=_to_float(row.get("Liability (£)", "")),
                    pnl=_to_float(row.get("Profit/Loss", "")),
                    status=row.get("Status", "").strip(),
                    bet_id=bet_id,
                )
            )
    return legs


@dataclass
class Position:
    key: str
    match: str
    market: str
    legs: List[Leg] = field(default_factory=list)
    commission: float = DEFAULT_COMMISSION

    @property
    def n_back(self) -> int:
        return sum(1 for leg in self.legs if leg.side == "back")

    @property
    def n_lay(self) -> int:
        return sum(1 for leg in self.legs if leg.side == "lay")

    @property
    def traded(self) -> bool:
        """True if the position has BOTH back and lay legs (i.e. traded in-play)."""
        return self.n_back > 0 and self.n_lay > 0

    @property
    def style(self) -> str:
        if self.traded:
            return "traded"
        return "let-ride"

    @property
    def gross_pnl(self) -> float:
        return round(sum(leg.pnl for leg in self.legs), 2)

    @property
    def net_pnl(self) -> float:
        """Settled P/L after ~2% commission on net winnings (matches statement)."""
        g = self.gross_pnl
        return round(g * (1 - self.commission), 2) if g > 0 else round(g, 2)

    @property
    def total_staked(self) -> float:
        return round(sum(leg.stake for leg in self.legs if leg.side == "back"), 2)

    @property
    def result(self) -> str:
        if abs(self.net_pnl) < 0.01:
            return "scratch"
        return "won" if self.net_pnl > 0 else "lost"

    @property
    def is_international(self) -> bool:
        teams = [t.strip().lower() for t in self.match.split(" v ")]
        return len(teams) == 2 and all(t in _NATIONS for t in teams)

    @property
    def is_cup(self) -> bool:
        return self.market.strip().lower() in _CUP_MARKETS

    @property
    def off_method(self) -> bool:
        """Off the book's rules: internationals or cup/knockout ties."""
        return self.is_international or self.is_cup


def group_positions(legs: List[Leg], commission: float = DEFAULT_COMMISSION) -> List[Position]:
    order: List[str] = []
    by_key: dict[str, Position] = {}
    for leg in legs:
        pos = by_key.get(leg.description)
        if pos is None:
            pos = Position(key=leg.description, match=leg.match, market=leg.market,
                           commission=commission)
            by_key[leg.description] = pos
            order.append(leg.description)
        pos.legs.append(leg)
    return [by_key[k] for k in order]


def load_positions(path: str, commission: float = DEFAULT_COMMISSION) -> List[Position]:
    return group_positions(parse_export(path), commission)


# --------------------------- analytics ---------------------------------------

def _summ(positions: List[Position]) -> dict:
    decisive = [p for p in positions if p.result in ("won", "lost")]
    wins = sum(1 for p in decisive if p.result == "won")
    profit = sum(p.net_pnl for p in positions)
    staked = sum(p.total_staked for p in positions)
    return {
        "positions": len(positions),
        "wins": wins,
        "losses": len(decisive) - wins,
        "scratches": sum(1 for p in positions if p.result == "scratch"),
        "strike_rate": (wins / len(decisive)) if decisive else 0.0,
        "profit": round(profit, 2),
        "staked": round(staked, 2),
        "roi": (profit / staked) if staked else 0.0,
    }


def _group(positions: List[Position], keyfn) -> dict:
    groups: dict[str, List[Position]] = {}
    for p in positions:
        groups.setdefault(keyfn(p), []).append(p)
    return {k: _summ(v) for k, v in groups.items()}


def analyse(positions: List[Position]) -> dict:
    return {
        "overall": _summ(positions),
        "by_style": _group(positions, lambda p: p.style),
        "by_market": _group(positions, lambda p: p.market or "?"),
        "by_method": _group(positions, lambda p: "off-method" if p.off_method else "on-method"),
    }


def format_analysis(path: str, commission: float = DEFAULT_COMMISSION) -> str:
    positions = load_positions(path, commission)
    if not positions:
        return f"No positions parsed from {path}."
    a = analyse(positions)
    o = a["overall"]

    def block(title, table, order_by_profit=True):
        rows = sorted(table.items(), key=lambda kv: kv[1]["profit"], reverse=order_by_profit)
        lines = [f"--- {title} ---"]
        for k, s in rows:
            lines.append(
                f"  {k:<26} {s['positions']:>3} pos  {s['strike_rate']:>5.0%} SR  "
                f"£{s['profit']:>+9,.2f}  {s['roi']:>+7.1%}"
            )
        return "\n".join(lines)

    lines = [
        "=" * 66,
        "BETFAIR POSITION ANALYSIS  (legs reconstructed into positions)",
        "=" * 66,
        f"Positions:   {o['positions']}  "
        f"({o['wins']}W / {o['losses']}L / {o['scratches']} scratch)",
        f"Strike rate: {o['strike_rate']:.1%}",
        f"Turnover:    £{o['staked']:,.2f}",
        f"Net profit:  £{o['profit']:+,.2f}  (after {commission:.0%} commission)",
        f"Yield:       {o['roi']:+.1%}",
        "",
        block("TRADED (hedged in-play) vs LET-RIDE (directional)", a["by_style"]),
        "",
        block("ON-METHOD vs OFF-METHOD (book: domestic only, no internationals/cups)", a["by_method"]),
        "",
        block("BY MARKET", a["by_market"]),
    ]
    return "\n".join(lines)
