# FootballBets — a S.T.R.I.N.G Theory trading system

Working software that operationalises the football-trading method from
**Glen Kirkham's _The Six Figure Football Trader_**. It turns the book's
S.T.R.I.N.G Theory, the Golden Equation staking, hedging and geography rules
into tools you can actually use while trading.

> **It does not place bets and it makes no promise of profit.** It's a
> decision-support and discipline system: it does the maths and enforces the
> rules from the book so you make better, calmer, more consistent calls — which
> is exactly what the book says separates winners from losers.

## What's in the box

| Piece | What it does |
|---|---|
| `stringtheory/numbers.py` | **N** — price vs strike-rate maths, value/edge detection. |
| `stringtheory/staking.py` | The **Golden Equation** — bankroll → frontline → cycle → unit, with guardrails. |
| `stringtheory/hedging.py` | **Back-high/lay-low** green-up and free-bet calculator. |
| `stringtheory/geography.py` | **G** — every league in the book, with goals/unders bias. |
| `stringtheory/evaluate.py` | The full **S.T.R.I.N.G checklist** → GO / CONSIDER / NO-GO. |
| `stringtheory/journal.py` | Trade log + analytics ("log everything / find your patch"). |
| `stringtheory/betfair.py` | Parse a Betfair settled-bets export → rebuild positions from legs → analyse traded-vs-let-ride. |
| `stringtheory/cli.py` | Command line for all of the above. |
| `tools/trade-calculator.html` | A single-file, offline browser calculator for live use. |
| `docs/STRING_METHOD.md` | The method, distilled into a spec. |

## Quick start

No dependencies for the core (Python 3.9+). Tests use `pytest`.

```bash
# Is a price value for the strike rate you expect?
python -m stringtheory value --strike 70 --price 1.8

# What should I stake? (Golden Equation)
python -m stringtheory stake --bankroll 500 --frontline 10

# A goal came — green up or leave a free bet
python -m stringtheory hedge --stake 500 --back 1.43 --lay 1.20 --mode green

# Run the whole S.T.R.I.N.G checklist on a live game
python -m stringtheory evaluate --country Sweden --minute 55 --score 0-0 \
    --market "Over 1.5 Goals" --shots 8-6 --da 60-40 --possession 63 \
    --form-goal 80 --form-line 91 --strike 80 --price 1.9 \
    --intent "Top vs bottom, home chasing automatic promotion"

# Log trades and see where your edge really is
python -m stringtheory log --match "France v Sweden" --country France \
    --market "Over 0.5 Goals" --price 2.05 --stake 500 --pnl 514.52 --strategy STRING
python -m stringtheory report

# Analyse a raw Betfair settled-bets export (rebuilds positions from legs)
python -m stringtheory analyse --path data/betfair_export.csv
```

**Drop your own `ExchangeBets_Settled.csv` into `data/`** and run `analyse`: it
reconstructs positions from your back/lay legs, applies commission (reconciles
to your statement to the penny) and shows traded-vs-let-ride, on/off-method and
per-market performance. See [`docs/INSIGHTS.md`](docs/INSIGHTS.md) for the
findings from your real export — the short version: **your edge is trading out
(hedging), and the leak is un-exited directional bets.**

For live trading, open `tools/trade-calculator.html` in a browser tab next to
Betfair / Bet365 / Flashscore — it works offline and needs nothing installed.

## What the journal shows (example)

Seeded from a real World Cup P&L screenshot (`data/example_trades.csv`,
`python -m stringtheory report --path data/example_trades.csv`), the analytics
break your results down by market and by league. In that one night the losses
clustered entirely in the **Germany v Paraguay** match — and the two Germany
bets (Match Odds **and** −1.5 handicap) were **correlated**: both rode on
Germany, so a single upset sank them together. That's a concentration-risk
lesson the numbers surface for you. (One night is far too small to judge any
market *type* — the point of logging is to let a real sample tell you the truth
over hundreds of trades.)

Also note: those World Cup games are **internationals**, which the book itself
says to avoid — and the `evaluate` engine flags them as NO-GO for exactly that
reason.

## Running the tests

```bash
pip install pytest
python -m pytest -q
```

The tests check the maths against the book's own worked examples (the strike-
rate table, the £500/10%/£5 staking cycle, the LION hedge, etc.).

## Roadmap (ask and I'll build)

- **Live data feed** — pull fixtures/in-play stats so `evaluate` runs itself
  (needs a data API/key).
- **Betfair integration** — read live prices via the Betfair Exchange API
  (read-only first; automated staking only if you want it).
- **A TIGER-style scanner** — watch 0-0-at-HT games in your leagues and alert
  when the S.T.R.I.N.G jigsaw lines up.
- **Web dashboard** — the calculator plus your live journal and running strike
  rate in one screen.

## Responsible gambling

18+. Betting carries real financial risk and can be harmful. This project is a
personal tool, not financial advice, and cannot guarantee profit. If it stops
being fun, please reach out: **BeGambleAware.org**, **GamStop.co.uk**,
**GamCare** (0808 8020 133), **Gordon Moody**.
