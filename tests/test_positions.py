"""Verify the discipline guardrail catches Glen's real mistakes and allows his
proven winning style (the goal-ladder)."""

from stringtheory import positions
from stringtheory.positions import Position


def test_stake_comes_from_golden_equation():
    p = positions.propose_entry(
        bankroll=500,
        candidate=Position("A v B", "Over 2.5", "Over/Under 2.5 Goals", price=1.9),
    )
    assert p.recommended_unit == 5.0    # £500 -> 10% frontline -> £5 unit


def test_no_value_is_blocked():
    # 80% strike needs 1.25; offered 1.10 is not value.
    p = positions.propose_entry(
        bankroll=500,
        candidate=Position("A v B", "Over 0.5", "Over/Under 0.5 Goals", price=1.10),
        strike_rate=80,
    )
    assert p.verdict == positions.BLOCK


def test_germany_correlation_is_caught():
    # Real mistake: already on Germany Match Odds, now adding Germany -1.5.
    open_pos = [Position("Germany v Paraguay", "Germany", "Match Odds")]
    p = positions.propose_entry(
        bankroll=1000,
        candidate=Position("Germany v Paraguay", "Germany -1.5", "Asian Handicap", price=2.26),
        open_positions=open_pos,
    )
    assert p.correlation_warnings
    assert p.verdict == positions.CAUTION


def test_goal_ladder_is_not_nagged():
    # Backing multiple Over lines in one game is Glen's winning style, not a stack.
    open_pos = [Position("France v Sweden", "Over 0.5", "Over/Under 0.5 Goals")]
    p = positions.propose_entry(
        bankroll=1000,
        candidate=Position("France v Sweden", "Over 1.5", "Over/Under 1.5 Goals", price=1.9),
        open_positions=open_pos,
    )
    assert p.correlation_warnings == []


def test_directional_back_requires_exit():
    p = positions.propose_entry(
        bankroll=500,
        candidate=Position("A v B", "A", "Match Odds", side="back", price=2.0),
    )
    assert p.requires_exit is True


def test_exit_supplied_clears_requirement():
    p = positions.propose_entry(
        bankroll=500,
        candidate=Position("A v B", "A", "Match Odds", side="back", price=2.0,
                           exit_minute=70),
    )
    assert p.requires_exit is False


def test_team_root_strips_handicap():
    assert Position("x", "Germany -1.5", "Asian Handicap").team_root == "germany"
    assert Position("x", "Bayern Munich +0.5", "Asian Handicap").team_root == "bayern munich"
    assert Position("x", "Over 2.5", "Over/Under 2.5 Goals").team_root == ""
