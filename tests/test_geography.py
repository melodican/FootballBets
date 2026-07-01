"""Verify the geography rules match the book's league lists."""

from stringtheory import geography


def test_core_leagues_tradeable():
    for country in ["England", "Italy", "Spain", "France", "Portugal"]:
        v = geography.assess_country(country)
        assert v.tradeable
        assert v.tier == geography.CORE


def test_middle_tier_goal_fests():
    for country in ["Sweden", "Norway", "Finland", "Denmark", "Switzerland"]:
        v = geography.assess_country(country)
        assert v.tradeable
        assert v.bias == geography.GOALS


def test_japan_is_unders():
    v = geography.assess_country("Japan")
    assert v.bias == geography.UNDERS


def test_avoid_list():
    for country in ["Russia", "Brazil", "Argentina", "Paraguay", "China"]:
        v = geography.assess_country(country)
        assert v.tier == geography.AVOID
        assert not v.tradeable


def test_case_insensitive_lookup():
    assert geography.assess_country("sWeDeN").country == "Sweden"


def test_unknown_country_not_tradeable():
    v = geography.assess_country("Narnia")
    assert v.tier == geography.UNKNOWN
    assert not v.tradeable


def test_competition_type_domestic_only():
    assert geography.is_tradeable_competition("domestic")
    assert geography.is_tradeable_competition("league")
    for bad in ["cup", "friendly", "replay", "international"]:
        assert not geography.is_tradeable_competition(bad)
