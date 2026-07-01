"""Verify the Golden Equation staking against the book's chapter-14 example."""

import math

import pytest

from stringtheory import staking


def test_books_worked_example_500_bankroll():
    # Book: £500 bankroll, 10% frontline = £50, 10 units of £5.
    plan = staking.StakingPlan(bankroll=500, frontline_pct=0.10)
    assert plan.frontline == 50.0
    assert plan.unit == 5.0
    assert plan.cycle_exposure == 50.0


def test_frontline_scales():
    plan = staking.StakingPlan(bankroll=1000, frontline_pct=0.10)
    assert plan.frontline == 100.0
    assert plan.unit == 10.0


def test_warns_above_hard_ceiling():
    plan = staking.StakingPlan(bankroll=500, frontline_pct=0.50)
    assert any("hard ceiling" in w for w in plan.warnings)


def test_no_warning_at_default():
    plan = staking.StakingPlan(bankroll=500, frontline_pct=0.10)
    assert plan.warnings == []


def test_cycle_enforces_constant_unit():
    tracker = staking.CycleTracker(unit=5.0)
    tracker.record(pnl=2.0)          # a £2 win on a £5 unit
    with pytest.raises(ValueError):
        tracker.record(pnl=10.0, stake=20.0)   # changing stake mid-cycle is banned


def test_cycle_pnl_matches_book_80pct_example():
    # Book: 8 wins @ +£2, 2 losses @ -£5 => +£6 over the cycle.
    tracker = staking.CycleTracker(unit=5.0)
    for _ in range(8):
        tracker.record(pnl=2.0)
    for _ in range(2):
        tracker.record(pnl=-5.0)
    assert tracker.complete
    assert math.isclose(tracker.profit, 6.0, abs_tol=1e-9)
    assert math.isclose(tracker.strike_rate, 0.8, abs_tol=1e-9)


def test_cycle_rejects_eleventh_trade():
    tracker = staking.CycleTracker(unit=5.0)
    for _ in range(10):
        tracker.record(pnl=1.0)
    with pytest.raises(ValueError):
        tracker.record(pnl=1.0)
