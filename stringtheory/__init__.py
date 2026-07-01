"""S.T.R.I.N.G Theory - a software toolkit that operationalises the football
trading method from Glen Kirkham's book *The Six Figure Football Trader*.

Modules
-------
numbers    Price <-> Strike Rate maths (the "N" of S.T.R.I.N.G) and value/edge.
staking    The "Golden Equation" staking plan (Bankroll -> Frontline -> Cycle -> Unit).
hedging    Back-high / lay-low green-up and free-bet calculations.
geography  Which leagues to trade, and their goal/under bias (the "G").
evaluate   The full S.T.R.I.N.G checklist -> GO / CONSIDER / NO-GO verdict.
journal    Trade logging + analytics (strike rate, ROI, "find your patch").

Nothing here places bets. It is a decision-support and discipline tool: it does
the maths and enforces the rules from the book so the human makes better calls.
"""

__version__ = "0.1.0"

from . import numbers, staking, hedging, geography, evaluate, journal  # noqa: F401
