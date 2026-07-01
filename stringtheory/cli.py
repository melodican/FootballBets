"""Command-line interface for the S.T.R.I.N.G toolkit.

Examples
--------
  # Is the price value for a strike rate you expect?
  python -m stringtheory value --strike 70 --price 1.8

  # What should I stake?
  python -m stringtheory stake --bankroll 500 --frontline 10

  # A goal came - how do I green up / leave a free bet?
  python -m stringtheory hedge --stake 500 --back 1.43 --lay 1.20 --mode green

  # Run the whole S.T.R.I.N.G checklist on a live game
  python -m stringtheory evaluate --country Sweden --minute 55 --score 0-0 \
      --market "Over 1.5 Goals" --shots 8-6 --da 60-40 --possession 63 \
      --form-goal 80 --form-line 91 --strike 80 --price 1.9 \
      --intent "Top vs bottom, home side chasing automatic promotion"

  # Log a settled trade and see your report
  python -m stringtheory log --match "France v Sweden" --country France \
      --market "Over 0.5 Goals" --price 2.05 --stake 500 --pnl 514.52 --strategy STRING
  python -m stringtheory report
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import Optional, Tuple

from . import betfair, evaluate, geography, hedging, journal, numbers, positions, shortlist, staking


def _parse_pair(text: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not text:
        return None, None
    parts = text.replace(":", "-").split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"expected 'home-away', got '{text}'")
    return float(parts[0]), float(parts[1])


def cmd_value(args) -> int:
    v = numbers.assess_value(args.strike, args.price, args.commission)
    print(v.summary)
    print(f"  Break-even price (no commission): {v.required_price:.3f}")
    print(f"  Break-even price (after {args.commission:.0%} comm.): {v.required_price_after_commission:.3f}")
    return 0


def cmd_stake(args) -> int:
    plan = staking.StakingPlan(bankroll=args.bankroll, frontline_pct=args.frontline / 100.0)
    print(plan.describe())
    return 0


def cmd_hedge(args) -> int:
    result = hedging.hedge(args.stake, args.back, args.lay, mode=args.mode, commission=args.commission)
    print(result.summary)
    return 0


def cmd_geo(args) -> int:
    print(geography.assess_country(args.country).summary)
    return 0


def _emit_json(payload) -> None:
    print(json.dumps(payload, default=lambda o: dataclasses.asdict(o)
                     if dataclasses.is_dataclass(o) else str(o), indent=2))


def cmd_evaluate(args) -> int:
    home_shots, away_shots = _parse_pair(args.shots)
    da_home, da_away = _parse_pair(args.da)
    hs, as_ = _parse_pair(args.score)
    ctx = evaluate.MatchContext(
        country=args.country,
        competition_type=args.competition,
        minute=args.minute,
        home_score=int(hs or 0),
        away_score=int(as_ or 0),
        market=args.market,
        dangerous_attacks_home=int(da_home) if da_home is not None else None,
        dangerous_attacks_away=int(da_away) if da_away is not None else None,
        shots_home=int(home_shots) if home_shots is not None else None,
        shots_away=int(away_shots) if away_shots is not None else None,
        possession_home=args.possession,
        goal_after_minute_pct=args.form_goal,
        over_line_pct=args.form_line,
        intent_note=args.intent,
        strike_rate=args.strike,
        offered_price=args.price,
        commission=args.commission,
    )
    result = evaluate.evaluate(ctx)
    if getattr(args, "json", False):
        _emit_json({
            "verdict": result.verdict,
            "checks": [{"letter": c.letter, "status": c.status, "message": c.message}
                       for c in result.checks],
            "value": dataclasses.asdict(result.value) if result.value else None,
            "reasons": result.reasons,
        })
    else:
        print(result.describe())
    return 0


def cmd_log(args) -> int:
    trade = journal.Trade(
        match=args.match,
        country=args.country,
        competition=args.competition,
        market=args.market,
        side=args.side,
        minute=args.minute,
        price=args.price,
        stake=args.stake,
        pnl=args.pnl,
        strategy=args.strategy,
        notes=args.notes,
    )
    journal.append_trade(trade, args.path)
    print(f"Logged: {trade.match} | {trade.market} | £{trade.pnl:+.2f} ({trade.result}) -> {args.path}")
    return 0


def cmd_report(args) -> int:
    print(journal.format_report(args.path))
    return 0


def cmd_analyse(args) -> int:
    print(betfair.format_analysis(args.path, commission=args.commission))
    return 0


def cmd_position(args) -> int:
    open_positions = []
    if args.open:
        for spec in args.open:
            # format: "Match|Selection|Market[|side]"
            parts = spec.split("|")
            open_positions.append(positions.Position(
                match=parts[0], selection=parts[1] if len(parts) > 1 else "",
                market=parts[2] if len(parts) > 2 else "",
                side=parts[3] if len(parts) > 3 else "back",
            ))
    candidate = positions.Position(
        match=args.match, selection=args.selection, market=args.market,
        side=args.side, price=args.price,
        exit_price=args.exit_price, exit_minute=args.exit_minute,
    )
    proposal = positions.propose_entry(
        bankroll=args.bankroll, candidate=candidate, open_positions=open_positions,
        frontline_pct=args.frontline / 100.0, strike_rate=args.strike,
        commission=args.commission,
    )
    print(proposal.telegram)
    return 0


def cmd_shortlist(args) -> int:
    if args.date:
        from . import apifootball
        try:
            fixtures = apifootball.fixtures_for_date(args.date)
        except Exception as exc:  # network blocked here; runs on your machine
            print(f"Live fetch failed ({exc}). Falling back to --file if given.")
            if not args.file:
                return 1
            fixtures = shortlist.load_fixtures_json(args.file)
    else:
        fixtures = shortlist.load_fixtures_json(args.file)
    if getattr(args, "json", False):
        items = shortlist.build_shortlist(fixtures, min_score=args.min_score)[:args.top]
        _emit_json([{
            "match": it.match, "country": it.fixture.country,
            "league": it.fixture.league_name, "kickoff": it.fixture.kickoff,
            "score": it.score, "angle": it.angle, "favourite": it.favourite,
            "reasons": it.reasons,
        } for it in items])
    elif getattr(args, "telegram", False):
        print(shortlist.format_telegram(fixtures, top=args.top, min_score=args.min_score))
    else:
        print(shortlist.format_shortlist(fixtures, top=args.top, min_score=args.min_score,
                                         show_reasons=not args.no_reasons))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stringtheory", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("value", help="Check if a price is value for a strike rate")
    v.add_argument("--strike", type=float, required=True, help="Strike rate (0-1 or 0-100)")
    v.add_argument("--price", type=float, required=True, help="Offered decimal price")
    v.add_argument("--commission", type=float, default=0.0)
    v.set_defaults(func=cmd_value)

    s = sub.add_parser("stake", help="Golden Equation staking plan")
    s.add_argument("--bankroll", type=float, required=True)
    s.add_argument("--frontline", type=float, default=10.0, help="Frontline %% of bankroll")
    s.set_defaults(func=cmd_stake)

    h = sub.add_parser("hedge", help="Green-up / free-bet calculator")
    h.add_argument("--stake", type=float, required=True, help="Original back stake")
    h.add_argument("--back", type=float, required=True, help="Back price you got on")
    h.add_argument("--lay", type=float, required=True, help="Current (lower) lay price")
    h.add_argument("--mode", choices=["green", "freebet"], default="green")
    h.add_argument("--commission", type=float, default=hedging.DEFAULT_COMMISSION)
    h.set_defaults(func=cmd_hedge)

    g = sub.add_parser("geo", help="Look up the book's stance on a country")
    g.add_argument("country")
    g.set_defaults(func=cmd_geo)

    e = sub.add_parser("evaluate", help="Run the full S.T.R.I.N.G checklist")
    e.add_argument("--country", required=True)
    e.add_argument("--competition", default="domestic")
    e.add_argument("--minute", type=int)
    e.add_argument("--score", default="0-0", help="home-away, e.g. 1-0")
    e.add_argument("--market", default="Over 0.5 Goals")
    e.add_argument("--shots", help="home-away, e.g. 8-6")
    e.add_argument("--da", help="dangerous attacks home-away, e.g. 60-40")
    e.add_argument("--possession", type=float, help="home possession %%")
    e.add_argument("--form-goal", type=float, dest="form_goal", help="%% last-5 with goal after this minute")
    e.add_argument("--form-line", type=float, dest="form_line", help="%% recent games hitting the line")
    e.add_argument("--intent", default="")
    e.add_argument("--strike", type=float, help="your strike-rate estimate")
    e.add_argument("--price", type=float, help="offered decimal price")
    e.add_argument("--commission", type=float, default=numbers.DEFAULT_COMMISSION)
    e.add_argument("--json", action="store_true", help="Machine-readable output for agents")
    e.set_defaults(func=cmd_evaluate)

    lg = sub.add_parser("log", help="Log a settled trade")
    lg.add_argument("--match", required=True)
    lg.add_argument("--country", default="")
    lg.add_argument("--competition", default="domestic")
    lg.add_argument("--market", default="")
    lg.add_argument("--side", default="back", choices=["back", "lay"])
    lg.add_argument("--minute", type=int)
    lg.add_argument("--price", type=float)
    lg.add_argument("--stake", type=float, default=0.0)
    lg.add_argument("--pnl", type=float, default=0.0)
    lg.add_argument("--strategy", default="")
    lg.add_argument("--notes", default="")
    lg.add_argument("--path", default=journal.DEFAULT_PATH)
    lg.set_defaults(func=cmd_log)

    rp = sub.add_parser("report", help="Show your trading analytics")
    rp.add_argument("--path", default=journal.DEFAULT_PATH)
    rp.set_defaults(func=cmd_report)

    an = sub.add_parser("analyse", help="Analyse a Betfair settled-bets CSV export")
    an.add_argument("--path", required=True, help="Path to the ExchangeBets_Settled CSV")
    an.add_argument("--commission", type=float, default=betfair.DEFAULT_COMMISSION)
    an.set_defaults(func=cmd_analyse)

    po = sub.add_parser("position", help="Vet an entry: stake, value, exit + correlation guardrail")
    po.add_argument("--bankroll", type=float, required=True)
    po.add_argument("--frontline", type=float, default=10.0)
    po.add_argument("--match", required=True)
    po.add_argument("--selection", required=True, help="e.g. 'Germany', 'Germany -1.5', 'Over 2.5'")
    po.add_argument("--market", required=True, help="e.g. 'Match Odds', 'Asian Handicap', 'Over/Under 2.5 Goals'")
    po.add_argument("--side", default="back", choices=["back", "lay"])
    po.add_argument("--price", type=float)
    po.add_argument("--strike", type=float, help="your strike-rate estimate (value check)")
    po.add_argument("--commission", type=float, default=0.0)
    po.add_argument("--exit-price", type=float, dest="exit_price")
    po.add_argument("--exit-minute", type=int, dest="exit_minute")
    po.add_argument("--open", action="append", help="Open position 'Match|Selection|Market[|side]' (repeatable)")
    po.set_defaults(func=cmd_position)

    sl = sub.add_parser("shortlist", help="Daily 'Watch These Games' Top-vs-Whipping-Boys shortlist")
    sl.add_argument("--date", help="YYYY-MM-DD for a live API-Football fetch (needs API_FOOTBALL_KEY)")
    sl.add_argument("--file", default="data/fixtures_sample.json", help="Cached/normalised fixtures JSON")
    sl.add_argument("--top", type=int, default=15)
    sl.add_argument("--min-score", type=float, default=0.0, dest="min_score")
    sl.add_argument("--no-reasons", action="store_true")
    sl.add_argument("--json", action="store_true", help="Machine-readable output for agents")
    sl.add_argument("--telegram", action="store_true", help="Compact message for Telegram push")
    sl.set_defaults(func=cmd_shortlist)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
