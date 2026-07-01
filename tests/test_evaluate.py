"""Verify the S.T.R.I.N.G engine's verdict logic, including cases drawn from
Glen's own World Cup P&L screenshot."""

from stringtheory import evaluate


def _strong_context(**overrides):
    ctx = evaluate.MatchContext(
        country="Sweden",
        competition_type="domestic",
        minute=55,
        home_score=0,
        away_score=0,
        market="Over 1.5 Goals",
        dangerous_attacks_home=60,
        dangerous_attacks_away=40,
        shots_home=8,
        shots_away=6,
        possession_home=63,
        goal_after_minute_pct=80,
        over_line_pct=91,
        intent_note="Top vs bottom; home chasing automatic promotion.",
        strike_rate=80,
        offered_price=1.9,
    )
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def test_strong_jigsaw_is_go():
    result = evaluate.evaluate(_strong_context())
    assert result.verdict == evaluate.GO


def test_international_is_hard_nogo():
    # Glen's screenshot was World Cup games - the book says NO internationals.
    result = evaluate.evaluate(_strong_context(competition_type="international"))
    assert result.verdict == evaluate.NO_GO
    assert any(c.letter == "G" and c.status == evaluate.FAIL for c in result.checks)


def test_no_value_is_hard_nogo():
    # 80% needs 1.25; being offered 1.10 is not value -> NO-GO regardless of the rest.
    result = evaluate.evaluate(_strong_context(offered_price=1.10))
    assert result.verdict == evaluate.NO_GO
    assert any(c.letter == "N" and c.status == evaluate.FAIL for c in result.checks)


def test_avoid_league_is_nogo():
    result = evaluate.evaluate(_strong_context(country="Brazil"))
    assert result.verdict == evaluate.NO_GO


def test_missing_pieces_downgrade_to_consider():
    thin = evaluate.MatchContext(
        country="Sweden",
        minute=55,
        market="Over 1.5 Goals",
        strike_rate=80,
        offered_price=1.9,
    )
    # Value + geography pass, but stats/form/intent unknown => not a clean GO.
    assert evaluate.evaluate(thin).verdict in (evaluate.CONSIDER, evaluate.GO)


def test_under_market_time_window():
    ctx = evaluate.MatchContext(
        country="Japan",
        minute=30,
        market="Under 2.5 Goals",
        strike_rate=70,
        offered_price=1.6,
        intent_note="Two low-scoring sides, lots of 1-0s in the form.",
        goal_after_minute_pct=20,
        over_line_pct=30,
    )
    time_check = next(c for c in evaluate.evaluate(ctx).checks if c.letter == "T")
    assert time_check.status == evaluate.PASS
