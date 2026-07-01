"""N - Numbers.  The maths behind the trade.

The single most important idea in the book: the relationship between **Price**
and **Strike Rate**.

    "We ultimately want to ensure that we are getting a better price than the
     likelihood of the thing happening."

Betfair uses decimal odds. The break-even price for something you win a
fraction ``p`` of the time is ``1 / p`` (ignoring commission).  You are +EV
(long-term profitable) whenever the price on offer is *higher* than that.

The book's table (Chapter 11) is exactly ``1 / p``:

    Strike Rate   Min price required
        10%            10.0
        20%             5.0
        30%             3.33
        40%             2.5
        50%             2.0
        60%             1.66
        70%             1.42
        80%             1.25
        90%             1.11
"""

from __future__ import annotations

from dataclasses import dataclass

# Betfair takes 2% commission on net winnings by default.
DEFAULT_COMMISSION = 0.02

# The book's reference table (Chapter 11), strike-rate% -> min break-even price.
STRIKE_RATE_TABLE = {
    10: 10.0,
    20: 5.0,
    30: 3.33,
    40: 2.5,
    50: 2.0,
    60: 1.66,
    70: 1.42,
    80: 1.25,
    90: 1.11,
}


def _as_probability(strike_rate: float) -> float:
    """Accept a strike rate as either a percentage (0-100) or a fraction (0-1)."""
    if strike_rate <= 0:
        raise ValueError("strike_rate must be > 0")
    p = strike_rate / 100.0 if strike_rate > 1 else strike_rate
    if not 0 < p <= 1:
        raise ValueError("strike_rate must resolve to a probability in (0, 1]")
    return p


def implied_probability(price: float) -> float:
    """The market's implied probability for a decimal price: ``1 / price``."""
    if price <= 1:
        raise ValueError("decimal price must be > 1")
    return 1.0 / price


def required_price(strike_rate: float, commission: float = 0.0) -> float:
    """Minimum decimal price to break even at a given strike rate.

    With no commission this is the book's ``1 / p``.  When ``commission`` is
    supplied the winning side is taxed, so you need a slightly bigger price:

        p * (price - 1) * (1 - c)  ==  (1 - p) * 1
        price = 1 + (1 - p) / (p * (1 - c))
    """
    p = _as_probability(strike_rate)
    if commission:
        return 1.0 + (1.0 - p) / (p * (1.0 - commission))
    return 1.0 / p


def back_profit(stake: float, price: float, commission: float = DEFAULT_COMMISSION) -> float:
    """Net profit on a winning BACK bet, after commission on winnings.

    The book's own shortcut: at a price under 2 the digits after the point are
    your ROI (``£10 @ 1.4 = 40% = £4``); at 2+ it's ``stake * price - stake``.
    Both are just ``stake * (price - 1)``, which this returns (less commission).
    """
    if price <= 1:
        raise ValueError("decimal price must be > 1")
    gross = stake * (price - 1.0)
    return gross * (1.0 - commission)


def back_roi(price: float, commission: float = DEFAULT_COMMISSION) -> float:
    """Return-on-investment fraction for a winning back bet at ``price``."""
    return back_profit(1.0, price, commission)


@dataclass
class ValueVerdict:
    """The result of comparing an offered price to what a strike rate needs."""

    strike_rate: float          # as a fraction 0-1
    offered_price: float
    required_price: float       # break-even price (no commission, book style)
    required_price_after_commission: float
    is_value: bool              # offered price beats the break-even price
    edge_probability: float     # your strike rate minus the market's implied prob
    edge_ticks: float           # offered price minus required price
    roi_if_win: float           # ROI % on a winning bet at the offered price

    @property
    def summary(self) -> str:
        verdict = "VALUE ✅" if self.is_value else "NO VALUE ❌"
        return (
            f"{verdict}  offered {self.offered_price:.2f} vs required "
            f"{self.required_price:.2f} "
            f"(you win {self.strike_rate * 100:.0f}%, market implies "
            f"{implied_probability(self.offered_price) * 100:.0f}%). "
            f"Edge {self.edge_probability * 100:+.1f}pp, "
            f"{self.roi_if_win * 100:.0f}% ROI if it lands."
        )


def assess_value(
    strike_rate: float,
    offered_price: float,
    commission: float = 0.0,
) -> ValueVerdict:
    """Compare an offered price against the strike rate needed to justify it.

    This is the beating heart of the "Numbers" chapter: only pull the trigger
    when the offered price is *above* the price your strike rate requires.
    """
    p = _as_probability(strike_rate)
    req = required_price(p)
    req_comm = required_price(p, commission or DEFAULT_COMMISSION)
    return ValueVerdict(
        strike_rate=p,
        offered_price=offered_price,
        required_price=req,
        required_price_after_commission=req_comm,
        is_value=offered_price > (req_comm if commission else req),
        edge_probability=p - implied_probability(offered_price),
        edge_ticks=offered_price - req,
        roi_if_win=back_roi(offered_price, commission),
    )
