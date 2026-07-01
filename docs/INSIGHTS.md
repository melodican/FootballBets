# What your real Betfair data says

Generated from your `ExchangeBets_Settled` export (35 positions rebuilt from 55
individual legs, 25 Apr – 30 Jun 2026). Reproduce any time with:

```bash
python -m stringtheory analyse --path data/betfair_export.csv
```

**First, a correctness check.** The parser groups your back/lay legs back into
positions and applies Betfair's 2% commission. Your World Cup ("off-method")
positions total **£1,241.62** — exactly the "All Profit/Loss" figure on your
screenshot. The maths ties out to the penny, so the findings below sit on solid
ground.

## Headline: your edge is *trading out*, not picking winners

| Style | Positions | Strike rate | Net P/L | Yield |
|---|---|---|---|---|
| **Traded** (backed then laid to green/scratch) | 8 | **100%** | **+£749.70** | +35.7% |
| **Let-ride** (directional, never traded out) | 27 | 41% | +£101.93 | +2.7% |

Every single position you actively traded was a green or a scratch — **not one
loss**. The France v Sweden game is a masterclass: even Over 3.5, which was a
**−£350 losing** directional position, you laid back to a perfect **£0 scratch**.
That's the hedging chapter of your own book, working in real money.

**The honest caveat:** part of that 100% is a selection effect — you can only
green up when the market moves your way (a goal comes). When it doesn't, the
position gets let-ride… and that's where the money leaks. So the real lesson
isn't "hedging magically wins", it's:

## The leak: un-exited directional punts

Your six worst positions were **all let-ride**, with no exit plan:

| Net P/L | Match | Market |
|---|---|---|
| −£355.36 | Germany v Paraguay | Match Odds |
| −£250.00 | Germany v Paraguay | Asian Handicap |
| −£235.02 | Juventus v Verona | Match Odds |
| −£100.00 | Juventus v Verona | Over/Under 2.5 |
| −£69.00 | Justo/Roncadelli v Cigarran/Falabella | Match Odds *(not even football)* |
| −£60.43 | Vasco da Gama v Paysandu | Over/Under 4.5 *(Brazil — your book's avoid list)* |

Two recurring mistakes, both from your own book:

1. **No exit.** These rode to a full loss. On France you traded out of a losing
   O3.5 for scratch; on Germany/Juventus you didn't. A pre-set exit (red up for
   a small loss) would have turned −£355 into −£30-ish.
2. **Correlated stacking.** Germany Match Odds **and** Germany −1.5 both ride on
   Germany not losing — one upset sank both (−£605 together). Same with backing
   Juventus Match Odds **three times** (−£235). That's the opposite of spreading
   your soldiers.

Your on-method (domestic) let-ride positions bled **−£454.69** across 18 bets.

## Market view — but read it through the style lens

Match Odds is your worst market on paper (−£464.79). But your France Match Odds
(traded) *won* +£72.52 — the losers were Germany and Juventus **let-ride**. So
it isn't "Match Odds is bad", it's "**directional Match Odds with no exit** is
bad". Your goal markets (O0.5/1.5/2.5, First Half Goals) are consistently green.

## On-method vs off-method — don't over-read this one

The tool shows off-method (World Cup) +£1,241 and on-method (domestic) −£390.
**Do not conclude "trade internationals."** It's confounded three ways: it's a
tiny sample, it's dominated by the one heavily-*traded* France game, and it's a
single hot night. Your book's caution on internationals still stands — let a
bigger sample decide, not one screenshot.

## What I'd do with this

1. **Lean into your proven edge:** in-play trading / hedging. It's where 88% of
   your profit came from and it has never lost in this sample.
2. **Put a stop on every let-ride bet.** Before you back directionally, decide
   the price/'minute at which you red up. Ride winners, cut losers — you already
   do the first half brilliantly.
3. **Stop stacking correlated backs** on the same team/outcome. One position per
   thesis.
4. **Keep exporting.** Drop each new `ExchangeBets_Settled.csv` into `data/` and
   re-run `analyse`. At ~500 positions this stops being suggestive and becomes
   your actual, personal edge map — exactly the "find your patch" the book calls
   for.

*Sample: 35 positions, £5,887 turnover, +£851.63 net (+14.5% yield). Directional
and small — treat as a hypothesis generator, not proof.*
