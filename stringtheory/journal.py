"""Trade journal + analytics.

The book is emphatic: logging every trade is "the thing that took me from an OK
trader to a world beater". After ~500 games you look for patterns and "find
your patch" — the market/league/time where YOU are actually profitable.

This module stores trades in a simple CSV (portable, opens in Excel/Sheets) and
computes the numbers the book cares about: strike rate, ROI/yield, and a
breakdown by league and by market so you can see where your edge really is.
"""

from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass, field
from datetime import date as _date
from typing import Dict, List, Optional

FIELDS = [
    "date", "match", "country", "competition", "market", "side",
    "minute", "price", "stake", "pnl", "result", "strategy", "notes",
]

DEFAULT_PATH = os.path.join("data", "trades.csv")


@dataclass
class Trade:
    match: str
    country: str = ""
    competition: str = "domestic"
    market: str = ""
    side: str = "back"                 # back | lay
    minute: Optional[int] = None
    price: Optional[float] = None
    stake: float = 0.0
    pnl: float = 0.0                    # realised profit (+) / loss (-)
    strategy: str = ""                 # e.g. "TIGER", "STRING-manual", "AUS-1H"
    notes: str = ""
    date: str = field(default_factory=lambda: _date.today().isoformat())

    @property
    def result(self) -> str:
        if self.pnl > 0:
            return "won"
        if self.pnl < 0:
            return "lost"
        return "scratch"

    def as_row(self) -> Dict[str, object]:
        row = asdict(self)
        row["result"] = self.result
        return {k: row.get(k, "") for k in FIELDS}


def append_trade(trade: Trade, path: str = DEFAULT_PATH) -> None:
    """Append a trade to the CSV, creating the file (and header) if needed."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(trade.as_row())


def load_trades(path: str = DEFAULT_PATH) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(row: dict, key: str) -> float:
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def summarise(rows: List[dict]) -> dict:
    """Overall performance: count, wins, strike rate, staked, profit, ROI."""
    settled = [r for r in rows if (r.get("result") or "") in ("won", "lost", "scratch")]
    n = len(settled)
    decisive = [r for r in settled if r.get("result") in ("won", "lost")]
    wins = sum(1 for r in decisive if r.get("result") == "won")
    staked = sum(_num(r, "stake") for r in settled)
    profit = sum(_num(r, "pnl") for r in settled)
    return {
        "trades": n,
        "wins": wins,
        "losses": len(decisive) - wins,
        "strike_rate": (wins / len(decisive)) if decisive else 0.0,
        "staked": round(staked, 2),
        "profit": round(profit, 2),
        "roi": (profit / staked) if staked else 0.0,   # yield on turnover
    }


def breakdown(rows: List[dict], by: str) -> Dict[str, dict]:
    """Group trades by a column (e.g. 'country', 'market', 'strategy')."""
    groups: Dict[str, List[dict]] = {}
    for r in rows:
        key = (r.get(by) or "?").strip() or "?"
        groups.setdefault(key, []).append(r)
    return {k: summarise(v) for k, v in sorted(groups.items())}


def find_your_patch(rows: List[dict], by: str = "market", min_trades: int = 5) -> List[tuple]:
    """Rank groups by profit to surface where your edge actually is.

    Returns (key, summary) sorted best-first, only including groups with at
    least ``min_trades`` settled trades (small samples lie).
    """
    ranked = [
        (k, s) for k, s in breakdown(rows, by).items() if s["trades"] >= min_trades
    ]
    ranked.sort(key=lambda kv: (kv[1]["roi"], kv[1]["profit"]), reverse=True)
    return ranked


def format_report(path: str = DEFAULT_PATH) -> str:
    rows = load_trades(path)
    if not rows:
        return f"No trades logged yet at {path}. Start logging — it's what makes you a world beater."

    overall = summarise(rows)
    lines = [
        "=" * 60,
        "TRADING REPORT",
        "=" * 60,
        f"Trades:      {overall['trades']}",
        f"Record:      {overall['wins']}W - {overall['losses']}L  "
        f"(strike rate {overall['strike_rate']:.1%})",
        f"Staked:      £{overall['staked']:,.2f}",
        f"Profit:      £{overall['profit']:+,.2f}",
        f"Yield/ROI:   {overall['roi']:+.1%} on turnover",
        "",
    ]

    for dim, title in (("market", "BY MARKET"), ("country", "BY LEAGUE"), ("strategy", "BY STRATEGY")):
        r0 = breakdown(rows, dim)
        if not r0:
            continue
        lines.append(f"--- {title} ---")
        for key, s in sorted(r0.items(), key=lambda kv: kv[1]["profit"], reverse=True):
            lines.append(
                f"  {key:<24} {s['trades']:>3} trades  "
                f"{s['strike_rate']:>5.0%} SR  £{s['profit']:>+9,.2f}  {s['roi']:>+6.1%}"
            )
        lines.append("")

    patch = find_your_patch(rows, "market")
    if patch:
        best_key, best = patch[0]
        lines += [
            "--- YOUR PATCH (best market, >=5 trades) ---",
            f"  {best_key}: {best['roi']:+.1%} ROI over {best['trades']} trades. "
            "Get really good at one thing.",
            "",
        ]
    return "\n".join(lines)
