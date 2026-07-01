"""Verify the shortlist scoring and the on-method filtering."""

from stringtheory import shortlist
from stringtheory.shortlist import Fixture, TeamForm


def _fx(country, comp="league", h_rank=1, a_rank=20, h_form="WWWWW", a_form="LLLLL",
        h_gf=40, h_ga=12, a_gf=12, a_ga=40, size=20):
    return Fixture(
        league_name=f"{country} League", country=country, competition_type=comp,
        league_size=size,
        home=TeamForm("Top", rank=h_rank, played=16, goals_for=h_gf, goals_against=h_ga, form=h_form),
        away=TeamForm("Whipping Boys", rank=a_rank, played=16, goals_for=a_gf, goals_against=a_ga, form=a_form),
    )


def test_strong_mismatch_scores_high():
    item = shortlist.score_fixture(_fx("England"))
    assert not item.off_method
    assert item.score > 60
    assert item.favourite == "Top"
    assert "GOALS" in item.angle


def test_internationals_are_off_method():
    item = shortlist.score_fixture(_fx("World", comp="international"))
    assert item.off_method
    assert item.score == 0.0


def test_cups_are_off_method():
    assert shortlist.score_fixture(_fx("Italy", comp="cup")).off_method


def test_avoid_league_off_method():
    assert shortlist.score_fixture(_fx("Brazil")).off_method


def test_japan_flips_to_unders():
    # Low-scoring Japanese sides -> unders angle, and should still score.
    item = shortlist.score_fixture(
        _fx("Japan", h_rank=6, a_rank=8, h_form="DDDLD", a_form="DDLWD",
            h_gf=16, h_ga=15, a_gf=15, a_ga=16, size=18)
    )
    assert not item.off_method
    assert "UNDERS" in item.angle


def test_build_shortlist_ranks_and_filters():
    fixtures = [
        _fx("England"),                       # strong on-method
        _fx("World", comp="international"),    # filtered out
        _fx("Sweden", h_rank=2, a_rank=15),    # on-method
        _fx("Brazil"),                         # filtered out
    ]
    items = shortlist.build_shortlist(fixtures)
    assert len(items) == 2                     # only the on-method games
    assert items[0].score >= items[1].score    # ranked best-first


def test_sample_file_parses():
    fixtures = shortlist.load_fixtures_json("data/fixtures_sample.json")
    assert len(fixtures) >= 6
    items = shortlist.build_shortlist(fixtures)
    assert all(not it.off_method for it in items)
