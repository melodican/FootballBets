"""Verify the Betfair export parser reconstructs positions and reconciles to
the account statement figures from Glen's real data."""

import textwrap

from stringtheory import betfair

# A slice of the real export: the France -1.5 AH (traded to a green), the
# O3.5 (traded to a scratch), and the Germany MO (let-ride loser).
SAMPLE = textwrap.dedent(
    """\
    Placed,Settled,Description,Type,Odds,Stake (£),Liability (£),Profit/Loss,Status
    30-Jun-26 20:42:56,30-Jun-26 23:54:26,France v Sweden France -1.5-Asian Handicap | Betfair Bet ID 1:1,Back,1.83,250.00, -- , 207.50 ,Won
    30-Jun-26 23:19:25,30-Jun-26 23:54:26,France v Sweden France -1.5-Asian Handicap | Betfair Bet ID 1:2,Lay,1.12,250.00, 30.00 , -30.00 ,Lost
    30-Jun-26 20:45:15,30-Jun-26 23:54:25,France v Sweden Over 3.5 Goals-Over/Under 3.5 Goals | Betfair Bet ID 1:3,Back,2.12,250.00, -- , -250.00 ,Lost
    30-Jun-26 23:29:36,30-Jun-26 23:54:25,France v Sweden Over 3.5 Goals-Over/Under 3.5 Goals | Betfair Bet ID 1:4,Back,3.15,100.00, -- , -100.00 ,Lost
    30-Jun-26 23:34:40,30-Jun-26 23:54:25,France v Sweden Over 3.5 Goals-Over/Under 3.5 Goals | Betfair Bet ID 1:5,Lay,1.58,350.00, 203.00 , 350.00 ,Won
    29-Jun-26 22:17:31,29-Jun-26 23:29:21,Germany v Paraguay Germany-Match Odds | Betfair Bet ID 1:6,Back,2.44,355.36, -- , -355.36 ,Lost
    """
)


def _positions(tmp_path):
    p = tmp_path / "export.csv"
    p.write_text(SAMPLE, encoding="utf-8")
    return {pos.market: pos for pos in betfair.load_positions(str(p))}


def test_france_ah_reconciles_to_statement(tmp_path):
    pos = _positions(tmp_path)["Asian Handicap"]
    assert pos.traded                       # backed then laid
    assert pos.gross_pnl == 177.50          # 207.50 - 30.00
    assert pos.net_pnl == 173.95            # after 2% commission -> matches screenshot
    assert pos.result == "won"


def test_over35_traded_to_a_scratch(tmp_path):
    pos = _positions(tmp_path)["Over/Under 3.5 Goals"]
    assert pos.traded
    # -250 -100 +350 = 0 exactly: a losing directional bet rescued to a scratch.
    assert pos.gross_pnl == 0.0
    assert pos.result == "scratch"


def test_germany_mo_is_let_ride_loser(tmp_path):
    pos = _positions(tmp_path)["Match Odds"]
    assert not pos.traded                   # only a back leg, never traded out
    assert pos.style == "let-ride"
    assert pos.net_pnl == -355.36           # no commission on a loss
    assert pos.result == "lost"


def test_internationals_flagged_off_method(tmp_path):
    for pos in _positions(tmp_path).values():
        assert pos.is_international         # France/Sweden, Germany/Paraguay are nations
        assert pos.off_method


def test_grouping_counts(tmp_path):
    positions = betfair.load_positions(str(tmp_path / "export.csv")) if False else None
    p = tmp_path / "export.csv"
    p.write_text(SAMPLE, encoding="utf-8")
    positions = betfair.load_positions(str(p))
    assert len(positions) == 3             # 6 legs -> 3 positions
