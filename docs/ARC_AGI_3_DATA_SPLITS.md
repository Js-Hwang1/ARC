# ARC-AGI-3 data splits and observability

Last verified: 2026-09-03

Related reference: [ARC-AGI-3 scoring and engineering strategy](ARC_AGI_3_SCORING_STRATEGY.md)

See also: [Why public-set 100% is not a Kaggle 100% result](PUBLIC_100_VS_KAGGLE.md)

## Crystal-clear answer

ARC-AGI-3 has **25 released development environments** and **110 hidden
competition environments**. The hidden set is split into 55 environments for
the public leaderboard and 55 for the private leaderboard.

The phrase **public leaderboard** does not mean its 55 environments are public.
It means only that the aggregate score computed from that split is displayed
during the competition.

| Split | Count | Cases/frames available to us? | Observable result | Reusable recordings? |
|---|---:|---|---|---|
| Official Public Demo / development set | 25 | Yes: files, local engine, and public API | Per-game and aggregate scores | Yes |
| Hidden public-leaderboard / Semi-Private split | 55 | No | One aggregate public-LB score after a scored submission | No |
| Hidden private-leaderboard / Fully Private split | 55 | No | Not shown during the live competition; retained for private/final ranking | No |

Therefore:

- **Official 25: fully probeable.** We can inspect state, log every transition,
  run unlimited local instances, search, generate trajectories, and measure
  per-game results.
- **Public-LB 55: not case-probeable.** A submitted agent interacts with them
  inside Kaggle's isolated scoring run, but we cannot retrieve their frames,
  identities, recordings, logs, or per-game scores. Only the aggregate score is
  returned. That single score can support coarse A/B comparison, subject to the
  current one-scored-submission-per-team-per-day limit; it is not access to the
  cases.
- **Private-LB 55: not probeable.** Their cases and live score are withheld.
  They provide no feedback loop during the competition.

Official basis: the [Kaggle data page](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data)
states that evaluation uses a separate private set of 110 unseen games, with
half used for the public leaderboard and half for the private leaderboard.

## What happens during a hidden scoring run

The agent must receive hidden frames in memory to choose actions. That does not
make those frames available to the competitor after the run. Kaggle restricts
hidden-run outputs and provides deliberately coarse errors to prevent test-set
probing. A failed scored run also consumes the daily submission allowance.

### The two executions must not be confused

| Execution | Games seen by that execution | Are its files, stdout, and notebook outputs downloadable? |
|---|---|---|
| Notebook Save & Run / validation | Released or validation inputs | Yes |
| Competition scoring rerun | The 110 hidden competition games | No; Kaggle privately extracts the required submission artifact and returns status plus the aggregate public-LB score |

The visible Output and Logs tabs belong to the first execution. Submitting its
completed version causes Kaggle to start a separate, isolated second execution.
The second execution does not replace the visible notebook outputs with its
hidden-run files.

Code can technically write one JSON file per hidden game inside the scoring
container. Those files are ephemeral and unavailable after the run. They may be
used as internal state by the agent during that same execution, but cannot be
downloaded afterward. Trying to smuggle their content through the required
submission artifact or another observable channel would be hidden-test
exfiltration/probing.

The returned aggregate score also cannot uniquely be backmapped into 55
problems or 55 per-game results: it is one scalar produced from many unknown
terms. Designing repeated submissions specifically to reconstruct those terms
would itself be leaderboard probing.

Legitimate behavior:

- Use current and prior frames internally to solve the game during that run.
- Maintain transient structured memory, hypotheses, and counters for the agent.
- Receive the normal aggregate leaderboard score after the run.

Not a legitimate debugging strategy:

- Persist or print hidden frames expecting to download them afterward.
- Encode game identifiers, frame content, or fingerprints into the submission
  artifact, errors, timing, action patterns, or another side channel.
- Coordinate submissions to reconstruct individual hidden cases.

See [Kaggle's code-competition debugging guidance](https://www.kaggle.com/code-competition-debugging).

## Is there a community collection of the hidden public-LB 55?

**No credible, rules-compliant case-level collection was found as of the date
above.** Public notebook code and aggregate leaderboard scores are collectable;
the underlying 55 games, per-game scores, frames, and trajectories are not.

Treat any dataset claiming to contain the actual hidden 55 or their recovered
traces as untrusted until the competition organizers confirm its provenance in
writing. It may be fabricated, leaked, or produced by prohibited probing, and
using it could invalidate the submission.

## Legitimate community data we can use

These expand development coverage but do **not** contain the hidden 55:

1. The official [ARC-AGI-3 human dataset](https://arcprize.org/blog/arc-agi-3-human-dataset):
   342 step-by-step human replays covering the same 25 released environments.
2. The community [ARC-AGI-3 world-model traces](https://huggingface.co/datasets/fredericowieser/arc-agi-3-wm-traces):
   transition data from released/community sources; provenance and licensing
   must be filtered before training.
3. The [ARC3 community game catalog](https://github.com/sonpham-org/arc-3):
   roughly 300 official and community games, of which only 25 are official.
4. The [200+ community-game testbed](https://www.kaggle.com/code/poonszesen/arc-agi-3-interactive-testbed-200-games).

The official 25 can be run locally with no rate limit and many simultaneous
instances; the ARC documentation reports roughly 2,000 FPS. Online public play
supports scorecards/replays but is rate-limited. See
[Local vs Online](https://docs.arcprize.org/local-vs-online) and
[Available Games](https://docs.arcprize.org/available-games).

## Recommended terminology in this repository

Use these exact labels to avoid future confusion:

- `dev25`: the 25 released official development games.
- `public_lb55`: the hidden 55-game split producing the visible leaderboard
  score. Never call these "public cases."
- `private_lb55`: the other hidden 55-game split.
- `community_ood`: public community-created games held out by game family.
- `human_dev25`: human replays for `dev25` only.

## What we can estimate

We can measure:

- Mean and variance over repeated runs on `dev25`.
- Generalization on creator- and mechanic-held-out `community_ood` games.
- The gap between our local metrics and the single aggregate `public_lb55`
  score returned by each permitted Kaggle submission.

We cannot measure during the live competition:

- Per-game performance on `public_lb55`.
- Any performance metric on `private_lb55`.
- Whether a particular hidden mechanic is present.
- A statistically clean public-to-private deviation from one aggregate
  submission score.
