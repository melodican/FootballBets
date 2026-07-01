"""Hedging - "back high, lay low" (Chapter 15).

Once the market moves in your favour (usually after a goal), you lay the same
market at the lower price to either:

* **green**   - lock in the SAME profit whatever happens next (equalise), or
* **freebet** - lay for the same stake you backed, so you scratch (£0) if
                nothing else happens and win big if it does. This is the book's
                "bring your soldiers back to the trenches and leave a free bet".

Given a back stake ``S`` at back price ``B``, laying at price ``L`` (< B):

    green   :  lay_stake = S * B / L
               guaranteed profit either way = S * (B - L) / L
    freebet :  lay_stake = S
               profit if event happens  = S * (B - L)
               profit if it doesn't      = 0  (scratch)

Commission (default 2%) is applied to net winnings on whichever side wins.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_COMMISSION = 0.02


@dataclass
class HedgeResult:
    mode: str
    back_stake: float
    back_price: float
    lay_price: float
    lay_stake: float
    liability: float            # what the lay bet risks
    profit_if_event: float      # net profit if the backed outcome happens
    profit_if_no_event: float   # net profit if it does not
    guaranteed: bool            # True when both outcomes yield the same profit

    @property
    def summary(self) -> str:
        if self.guaranteed:
            return (
                f"GREEN UP: lay £{self.lay_stake:.2f} @ {self.lay_price:.2f} → "
                f"locked £{self.profit_if_event:+.2f} either way "
                f"(liability £{self.liability:.2f})."
            )
        return (
            f"FREE BET: lay £{self.lay_stake:.2f} @ {self.lay_price:.2f} → "
            f"£{self.profit_if_event:+.2f} if it hits, "
            f"£{self.profit_if_no_event:+.2f} if not "
            f"(liability £{self.liability:.2f})."
        )


def _lay_liability(lay_stake: float, lay_price: float) -> float:
    return lay_stake * (lay_price - 1.0)


def hedge(
    back_stake: float,
    back_price: float,
    lay_price: float,
    mode: str = "green",
    commission: float = DEFAULT_COMMISSION,
) -> HedgeResult:
    """Compute the lay stake and resulting P/L for a back-then-lay hedge."""
    if back_price <= 1 or lay_price <= 1:
        raise ValueError("decimal prices must be > 1")
    if lay_price > back_price:
        raise ValueError(
            "lay_price should be lower than back_price (back high, lay low). "
            "If the price drifted up, you have a loss to trade out of, not a green-up."
        )
    mode = mode.lower()

    if mode == "green":
        lay_stake = back_stake * back_price / lay_price
    elif mode == "freebet":
        lay_stake = back_stake
    else:
        raise ValueError("mode must be 'green' or 'freebet'")

    liability = _lay_liability(lay_stake, lay_price)

    # Backed outcome HAPPENS: back bet wins, lay bet loses its liability.
    back_win = back_stake * (back_price - 1.0) * (1.0 - commission)
    profit_if_event = back_win - liability

    # Backed outcome does NOT happen: back stake lost, lay bet wins its stake.
    lay_win = lay_stake * (1.0 - commission)
    profit_if_no_event = lay_win - back_stake

    return HedgeResult(
        mode=mode,
        back_stake=round(back_stake, 2),
        back_price=back_price,
        lay_price=lay_price,
        lay_stake=round(lay_stake, 2),
        liability=round(liability, 2),
        profit_if_event=round(profit_if_event, 2),
        profit_if_no_event=round(profit_if_no_event, 2),
        guaranteed=(mode == "green"),
    )
