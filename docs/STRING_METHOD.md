# S.T.R.I.N.G Theory — method reference

A distilled, encodable summary of the method in *The Six Figure Football
Trader* (Glen Kirkham, 2022). This is the specification the `stringtheory`
package implements. Page references are to the book in `docs/betting-book.pdf`.

> Income is directly proportional to how well you can read a football match.
> **80% match reading / 20% mentality.** Build the jigsaw — never bet on one
> piece of it.

## The six pieces

| Letter | Piece | What to look for | Source |
|---|---|---|---|
| **S** | Stats (in-play) | Dangerous attacks ≈ match minutes; lots of shots (≥15 projected full-time for goals); possession dominance ≥60%. "Either the in-play dictates the form, or the form dictates the in-play." | Bet365 |
| **T** | Time | Goal markets: 2nd half, **45–75'** sweet spot (can stretch to ~85' if watching). Unders: ~30' at 0-0 in conservative games. 0-0 at HT is the classic setup. | Bet365 |
| **R** | Recent form | Last 5 games: goals scored/conceded, form vs teams around the opponent's position, **% of games with a goal after the current minute**, **% over the line**. Want ≥70%. | Flashscore |
| **I** | Intent | Motivation: fixture congestion, league/points situation, competition importance, players resting for bigger games. Ask: *what's the motivation here?* | Judgement |
| **N** | Numbers | Only trade when the **offered price beats the price your strike rate needs**. | Betfair |
| **G** | Geography | Trade only leagues the book trusts, with the right bias. Men's **domestic** only. | — |

## N — the numbers (the core edge)

Break-even decimal price for a strike rate `p` is **`1 / p`** (before commission).
You are +EV whenever the offered price is *higher*.

| Strike rate | Min price | | Strike rate | Min price |
|---|---|---|---|---|
| 10% | 10.0 | | 60% | 1.66 |
| 20% | 5.0  | | 70% | 1.42 |
| 30% | 3.33 | | 80% | 1.25 |
| 40% | 2.5  | | 90% | 1.11 |
| 50% | 2.0  | | | |

Profit on a winning back bet = `stake × (price − 1)`, less ~2% Betfair
commission on winnings.

## G — geography

- **Core (trade freely):** England, Italy, Spain, France, Portugal, Germany, Netherlands.
- **Middle tier (goal-fests — much of the profit):** Austria, Croatia, Belgium,
  Finland, Turkey, Norway, Switzerland, Denmark, Greece, Sweden, Iceland,
  South Korea, Australia (first-half goals), Mexico, Peru.
- **Unders bias:** **Japan** — back unders when the form is full of 1s and 0s.
- **Strict (big games only, all criteria met):** Egypt, Israel, Morocco, Tunisia,
  Algeria, Libya, Malta, USA/MLS, Venezuela, Ecuador, Cuba.
- **Avoid:** Russia, Brazil, Argentina, Uruguay, Paraguay, China, Belarus,
  Estonia, Romania, South Africa, lower/U20 leagues.
- **Rule of thumb:** a country with ≥1 Champions League representative is a good
  nation to trade (except Russia).
- **Domestic only:** no cups, friendlies, replays or internationals.

## Staking — the Golden Equation (Chapter 14)

```
Bankroll  →  Frontline (10%, slide to 25%, never >30%)  →  Cycle (10 trades)  →  Unit (10% of frontline)
```

The **unit must stay constant** for a whole cycle. Firing three times on one
market = three units. Complete the cycle, then recompute. This is what makes
revenge-betting and emotional stake-hiking impossible.

## Hedging (Chapter 15)

"Back high, lay low." After the price moves (usually a goal), lay the market to:
- **green up** — lock equal profit either way: `lay = stake × back / lay`, or
- **free bet** — lay the same stake: scratch if nothing more happens, big win if
  it does (bring your soldiers back to the trenches).

## The process, step by step (Chapter 13)

1. **T + G** — scan Flashscore *Live* + Bet365 for games ~45–55', in a good
   league, 0-0 (favourite) or a strong favourite losing. Filter fast.
2. **S + I** — check the in-play stats and the motivation. Is what you expect
   actually showing on the pitch?
3. **R** — confirm the reading against recent form (goal-after-minute %, over %).
4. **N** — only now open Betfair. Take the price *only if* it beats what your
   strike rate needs.
5. **60–90'** — keep firing (e.g. O0.5) as the price drifts up; hedge when the
   goal comes.

## Discipline (Chapters 5, 16)

- **Log everything.** It's what takes you from OK to world-beater.
- After ~500 games, **find your patch** — the market/league/time where *you* are
  profitable — and get really good at one thing.
- **Relax.** Good decisions don't come from a stressed, chasing mind.
