"""Verify hedging maths, including the book's LION worked example."""

import math

import pytest

from stringtheory import hedging


def test_green_up_is_guaranteed_both_ways():
    r = hedging.hedge(back_stake=100, back_price=2.0, lay_price=1.5, mode="green", commission=0.0)
    # Equalised profit: same either way.
    assert r.guaranteed
    assert math.isclose(r.profit_if_event, r.profit_if_no_event, abs_tol=1e-6)
    # lay_stake = S * B / L = 100 * 2 / 1.5
    assert math.isclose(r.lay_stake, 100 * 2 / 1.5, abs_tol=0.01)


def test_green_up_profit_formula():
    # Pre-commission green profit = S * (B - L) / L.
    S, B, L = 100, 2.0, 1.5
    r = hedging.hedge(S, B, L, mode="green", commission=0.0)
    assert math.isclose(r.profit_if_event, S * (B - L) / L, abs_tol=0.02)


def test_freebet_scratches_if_no_event():
    # Lay the same stake -> £0 if nothing else happens, a free bet if it does.
    r = hedging.hedge(back_stake=100, back_price=2.0, lay_price=1.5, mode="freebet", commission=0.0)
    assert math.isclose(r.profit_if_no_event, 0.0, abs_tol=1e-6)
    # Free-bet upside = S * (B - L).
    assert math.isclose(r.profit_if_event, 100 * (2.0 - 1.5), abs_tol=1e-6)


def test_books_lion_over35_example():
    # Book: backed £588.91 @ 1.43, laid same stake @ 1.20 -> free bet ~£123-135.
    # The book quotes pre-commission. With Betfair's real 2% commission, laying the
    # SAME stake isn't a perfect scratch: it leaves a small residual (~ -£12) if no
    # further goal comes, and ~£130 upside if it does. That honesty is the point.
    r = hedging.hedge(back_stake=588.91, back_price=1.43, lay_price=1.20, mode="freebet", commission=0.02)
    assert -15 <= r.profit_if_no_event <= 0.5      # near-scratch, slight cost of commission
    assert 115 <= r.profit_if_event <= 140


def test_lay_must_be_lower_than_back():
    with pytest.raises(ValueError):
        hedging.hedge(100, 1.5, 2.0, mode="green")   # price drifted up, not a green-up


def test_cash_out_caps_a_loser():
    # Belgium MO backed £150 @ 2.0; drifted to 5.0 against you -> red up.
    r = hedging.cash_out(back_stake=150, back_price=2.0, current_lay_price=5.0, commission=0.0)
    assert r.profit_if_event == r.profit_if_no_event      # equalised both ways
    assert r.profit_if_event < 0                          # it's a capped loss
    assert r.profit_if_event > -150                       # but smaller than the -£150 full loss


def test_cash_out_greens_a_winner():
    r = hedging.cash_out(back_stake=100, back_price=2.0, current_lay_price=1.5, commission=0.0)
    assert r.profit_if_event > 0                          # price shortened -> locked profit
