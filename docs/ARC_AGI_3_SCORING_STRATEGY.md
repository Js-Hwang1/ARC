# ARC-AGI-3 scoring and engineering strategy

Last verified: 2026-09-03

Primary references:

- [Official RHAE methodology](https://docs.arcprize.org/methodology)
- [Official reference scoring implementation](https://github.com/arcprize/ARC-AGI/blob/main/arc_agi/scorecard.py)
- [Official scoring update and human baselines](https://arcprize.org/blog/arc-agi-3-human-dataset)

Deployment context: [Why public-set 100% is not a Kaggle 100% result](PUBLIC_100_VS_KAGGLE.md)

## Exact score

ARC-AGI-3 uses Relative Human Action Efficiency (RHAE). For level `l`:

- `H_l` is the organizer's upper-median human action baseline.
- `A_l` is the number of environment actions taken from the start of that level
  until it is completed.
- The level weight is its one-indexed level number: `w_l = l`.

For a completed level:

```text
level_score_l = min(115, 100 * (H_l / A_l)^2)
```

An uncompleted level has score zero.

For a game with `L` levels:

```text
raw_game_score = sum(l * level_score_l for l=1..L) / sum(l for l=1..L)

completion_cap = 100 * sum(l for completed levels) / sum(l for l=1..L)

game_score = min(raw_game_score, completion_cap)
```

Levels are sequential in practice, so completed levels normally form a prefix.
The completion cap prevents 115% scores on early levels from making an
unfinished game look completed.

The leaderboard score is the unweighted mean of the game scores:

```text
leaderboard_score = sum(game_score_g for g=1..N) / N
```

For the Kaggle public leaderboard, `N = 55`. Each game is equally important,
regardless of how many levels it contains.

## Quadratic action penalty

| AI actions relative to human baseline | Completed-level score |
|---:|---:|
| `<= 0.9325 H` | 115%, capped |
| `1.00 H` | 100% |
| `1.25 H` | 64% |
| `1.50 H` | 44.44% |
| `2.00 H` | 25% |
| `3.00 H` | 11.11% |
| `5.00 H` | 4% |
| `10.00 H` | 1% |

Consequences:

- Doubling the action count does not halve the score; it quarters it.
- Beating the baseline by more than about 6.75% earns no additional level
  score because 115% is the ceiling.
- Completing inefficiently is still better than scoring zero, especially when
  completion unlocks later, more valuable levels.

## Later levels dominate

For a five-level game, the completion ceiling after each solved prefix is:

| Levels completed | Weight completed | Maximum game score |
|---:|---:|---:|
| 1/5 | `1/15` | 6.67% |
| 2/5 | `3/15` | 20.00% |
| 3/5 | `6/15` | 40.00% |
| 4/5 | `10/15` | 66.67% |
| 5/5 | `15/15` | 100.00% |

Level 5 alone carries one third of that game's weight. Therefore reaching and
solving later levels is generally more valuable than polishing an already
reliable early-level route.

Efficient early levels can still help: their scores of up to 115% can offset a
slower completed level in the weighted raw score. They cannot lift a partially
completed game above its completion cap or a completed game above 100%.

## What counts as an action

The official methodology excludes internal reasoning, model calls, ordinary
tool calls, and computation that does not interact with the environment.
Submitted numbered actions do count.

The current reference implementation also has these important details:

- A valid numbered action is counted even if it produces no useful state
  change. Treat no-ops as expensive.
- The initial reset starts the play. Subsequent resets are tracked as both a
  reset and an action.
- A reset does not erase the actions already spent on the current level. If the
  level is later completed, earlier failed attempts remain in that level's
  action total.
- `ACTION7` is undo, but it is itself a numbered action. The mistaken action and
  the undo both cost actions.
- Actions spent on a level that is never completed leave that level at zero.
  They do not reduce previously banked level scores, but they consume wall time
  that could have been spent on another game.

## Conversion to leaderboard points

Because the public leaderboard averages 55 games:

```text
one game scoring 100 = 100 / 55 = 1.818 leaderboard points
one game scoring 10  =  10 / 55 = 0.182 leaderboard points
```

The 7.51 leaderboard leader observed on 2026-09-03 represents a sum of roughly
413 game-score points across the 55 games, or 4.13 perfect-game equivalents.
The published 2.23 Qwen3.8 baseline represents about 1.23 perfect-game
equivalents. This equivalence does not tell us whether points came from full
games or partial progress, but it gives the correct scale of the gap.

## Harness strategy implied by the metric

### 1. Optimize completion before microscopic efficiency

At current low leaderboard scores, reliably completing more levels and reaching
later levels is usually worth more than shaving a few actions from an already
solved route. Once completion is reliable, compress the route aggressively.

### 2. Invest exploration where its future value is largest

Exploration on level 1 damages the least-weighted level, while learned mechanics
can benefit every later level. Persist verified rules, object roles, controls,
goals, and failed hypotheses across level transitions.

This does not justify blind exploration. The quadratic penalty makes repeated
random actions, duplicate tests, and no-op loops costly when the level is
eventually solved.

### 3. Separate discovery from execution

Use two controller modes:

- **Discovery:** deliberate information-gain actions, hypothesis tracking, and
  deeper internal reasoning.
- **Execution:** once a route or mechanic is verified, run the shortest robust
  action sequence with minimal model deliberation.

Interrupt an execution macro on any unexpected state change instead of spending
many invalid follow-up actions.

### 4. Spend reasoning to save actions, within the wall-clock budget

Internal computation is action-free but not time-free. Use deeper reasoning
before high-impact coordinate clicks, irreversible transitions, resets, and
late-level actions. Use cheap direct control for verified repetitive motion.

### 5. Use reset and undo only when they preserve more value than they cost

Neither mechanism refunds prior actions. Prefer undo when it preserves valuable
level state and avoids a longer recovery, not as a routine probing primitive.
Prevent game-over and reset cycles with explicit guards.

### 6. Allocate time by expected score gain, not evenly

Each game has equal final weight, but their probability of yielding points per
second differs. A useful scheduling approximation for the current level is:

```text
priority ~= probability_of_completion
          * expected_completed_level_score
          * current_level_weight_fraction
          / expected_remaining_seconds
          + value_of_unlocking_future_levels
```

Start with a broad pass so easy opportunities are not missed. Continue deeply
on games demonstrating progress or a coherent mechanic. Stop loops whose
expected marginal score is below the best alternative use of remaining time.

### 7. Preserve breadth

Since games are averaged equally, a system that obtains meaningful partial
scores across many novel mechanics can beat one that perfects a small number of
games. Training and evaluation should be balanced by game and mechanic family,
not by raw transition count.

## Required experiment telemetry

For every public/community run, record at least:

- Game and level index, total levels, completion, and RHAE.
- Actions per level and known human baseline for released games.
- No-op, invalid, undo, reset, repeated-state, and game-over counts.
- Discovery actions versus execution actions.
- Model input/output tokens, inference latency, environment latency, and total
  wall time.
- Verified rules learned and whether they transferred to later levels.
- Score lost to action inefficiency versus score lost to non-completion.

Primary optimization reports should include:

1. Mean game score, with games weighted equally.
2. Completion-cap utilization: `game_score / completion_cap`.
3. Levels reached and completed, emphasizing later-level weight.
4. Expected score gained per GPU-minute.
5. Paired per-game deltas and confidence intervals across repeated seeds.

Do not select changes using the aggregate `dev25` mean alone. Require neutral or
positive performance on mechanic-family-held-out `community_ood` games before
spending a daily Kaggle submission.
