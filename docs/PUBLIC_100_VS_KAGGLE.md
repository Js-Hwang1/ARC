# ARC-AGI-3 public-set 100% versus Kaggle

Last verified: 2026-09-03

Related references:

- [Data splits and observability](ARC_AGI_3_DATA_SPLITS.md)
- [Scoring and engineering strategy](ARC_AGI_3_SCORING_STRATEGY.md)
- [Submission runbook](../SUBMISSION_RUNBOOK.md)

## Bottom line

The 96--100% AVO, Tycho, and `arc-code` results do **not** establish 96--100%
on the Kaggle competition. They were evaluated on `dev25`, the 25 released
games that researchers could inspect and use while developing their systems.
NVIDIA explicitly says that its AVO result is not on either the semi-private or
private competition sets.

There is now an important additional result. On September 3, ARC Prize reported
that GPT-6 Astra reached 99.95% on the hidden 55-game Semi-Private set with its
Provider Adapter harness. This demonstrates strong transfer to unseen games,
but the run used hosted inference costing about $18,817 and was not a Kaggle
one-GPU submission. No result on the 55-game Fully Private set is public.

The Kaggle task is therefore not merely:

> copy a 100% harness and make it fit on one RTX PRO 6000

It is:

> reproduce the useful test-time learning behavior of a hosted frontier model
> and its harness with an offline, locally deployable model; make it generalize
> to 110 unseen games; and execute the whole system on one GPU within nine
> hours.

That is a model-capability compression problem, a harness problem, a
generalization problem, and a systems problem simultaneously.

## Why the current Kaggle leader's notebook may not be visible

The premise that every scored notebook must be public immediately is
incorrect. Submissions are made from Kaggle notebooks, but a notebook may be
private while the competition is running.

For the September 30 milestone, a team must make its notebook public under an
open-source license **by that milestone deadline** to qualify for the prize.
Prize winners also have an open-source obligation. Consequently, a score can
appear before the exact scored notebook becomes public. A team can also keep a
submission private and forgo prize eligibility.

The public Code tab is not a complete mapping from leaderboard rows to the
exact notebook version that produced each score. At the deadline, verify the
team, notebook version, score, timestamp, license, model assets, and any linked
datasets rather than assuming the newest public notebook is the scored one.

Official basis: [Kaggle competition overview and prize/code
requirements](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview).

## What the headline claims actually measured

| Result | Games | Model and execution | Protocol | Kaggle hidden result? |
|---|---|---|---|---|
| Claude Opus 5, about 40.68% public and 30.16% Semi-Private | Released `dev25` and hidden Semi-Private 55 | Hosted Claude Opus 5, official Standard harness | One run per set at High effort | Semi-Private only |
| `arc-code`, 96.2%; 99.3% pass@2 | Released `dev25` | Stock Claude Code with hosted Opus 5, shell, files, and an action tool | 24/25 in one pass; one failed game retried for pass@2; about $540 | No |
| Tycho, 100% | Released `dev25` | Hosted Opus 5 or GPT-5.6 Sol plus actor/builder, executable models, verifier, and planner | 25/25 and 183/183 in one matched public-set run | No |
| NVIDIA AVO, 100% | Released `dev25` | Hosted Opus 5 plus persistent memory, supervision, and a text-grid interaction loop | 25/25 and 183/183 in 6,624 scored environment actions | No |
| GPT-6 Astra Provider Adapter, about 100% public and 96.72--99.95% Semi-Private | Released `dev25` and hidden Semi-Private 55 | Hosted GPT-6 Astra with retained opaque reasoning and compaction | Six reasoning settings; approximately $17K--$23K per Semi-Private run | Semi-Private only |
| Kaggle notebook score | Hidden `public_lb55` | Offline local weights on the competition machine | One isolated nine-hour rerun; aggregate score only | **Yes** |

Sources:

- [Official Opus 5 public per-game results and 30.16% Semi-Private
  result](https://arcprize.org/results/anthropic-claude-opus-5)
- [`arc-code`: 96.2%, approximately $540, and the pass@2
  distinction](https://github.com/jerber/arc-code)
- [Tycho paper and its 100% public-set protocol](https://arxiv.org/abs/2607.28287)
- [Open-source Tycho implementation](https://github.com/NIMI-research/Tycho)
- [NVIDIA AVO result and explicit public-set
  qualification](https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/)
- [ARC Prize explanation of model/harness results versus Kaggle
  Systems](https://arcprize.org/leaderboard)
- [GPT-6 Astra public and Semi-Private results](https://arcprize.org/results/openai-gpt-6-astra)

Correction: 30.16% is Opus 5's hidden Semi-Private score, not its `dev25`
aggregate. The 25 public per-game values displayed by ARC Prize average to
approximately 40.68% using their rounded values. A statement that “raw Opus 5
is around 50%” may be loosely referring to that public-set performance, a
different run, or a different aggregation, but it is not the published
Semi-Private score.

## What `dev25` currently predicts about unseen games

There is real but limited paired evidence. These pairs use the same broad
system on both released Public Demo and hidden Semi-Private environments:

| System/configuration | Public Demo 25 | Semi-Private 55 | Hidden/public retention |
|---|---:|---:|---:|
| GPT-5.6 Sol, Standard, max | 13.33 | 7.78 | 58% |
| GPT-5.6 Sol, Standard, xhigh | about 7.23 | 6.99 | 97% |
| GPT-5.6 Sol, Standard, high | about 5.19 | 2.15 | 41% |
| GPT-5.6 Sol, Standard, medium | about 1.52 | 1.07 | 70% |
| GPT-5.6 Sol, Standard, low | about 0.88 | 0.33 | 38% |
| Claude Opus 5, Standard, high | about 40.68 | 30.16 | 74% |
| GPT-6 Astra, Standard, max | about 68.34 | 62.71 | 92% |
| GPT-6 Astra, Provider Adapter, high | about 99.67 | 99.95 | 100% |
| Duck/Qwen 3.6 27B | 1.6002 mean over public repetitions | 1.21 Kaggle milestone | 76%, but not a matched single-run protocol |

Values marked “about” are means calculated from the rounded public per-game
scores on the official result pages. Retention is descriptive, not a calibrated
conversion formula. The GPT-5.6 settings are correlated, not independent
systems, and the Duck public number averages 20 tries per game while Kaggle is
a single competition execution.

The evidence supports three conclusions:

1. A better `dev25` system usually has better unseen performance within the
   same model/harness family.
2. There is no stable public-to-hidden multiplier. Observed retention spans
   roughly 38% to 100% even before considering heavily public-set-tuned systems.
3. Strong generic models with correct context retention can transfer almost
   perfectly. Small local models remain limited by capability and runtime, not
   merely by public/hidden distribution shift.

No one outside the organizers yet knows performance on the Fully Private 55.
Therefore no one knows a system's score over the complete hidden 110 during
the live competition.

## Were the 100% runs performed on the companies' own hardware?

They are not one-GPU Kaggle runs.

- `arc-code` uses a model key and cloud sandbox infrastructure. Its reported
  Opus pass cost about $540 for 25 games.
- Tycho plays against a locally cached environment, then validates and replays
  traces through the official ARC API. Its model inference uses Anthropic or
  OpenAI transports. Its selected-policy configuration allows 3,500 language
  model calls per game, 24,000 answer tokens per call, and a $1,500 inference
  ceiling per game, although the ceiling was not reached. The paper estimates
  the full Opus 5 run at about $2,990.
- NVIDIA reports the model as Claude Opus 5 but does not specify the model
  provider's serving hardware for the ARC evaluation. Claude's weights are not
  available for local Kaggle deployment. The DGX B200 mentioned in the AVO post
  belongs to a separate seven-day GPU-kernel optimization experiment, not the
  ARC-AGI-3 inference run.

Thus, “their own hardware” is not the important distinction. The important
facts are that frontier inference was supplied by hosted services, execution
was not constrained to the Kaggle machine, and the games were the released
development set.

## Why an existing 100% harness cannot simply be submitted

### 1. The backend model is unavailable offline

Tycho and `arc-code` are open source, but their headline performance depends on
Claude Opus 5 or GPT-5.6 Sol API calls. Internet is disabled in Kaggle. Opus 5
weights are closed and cannot be packed into the RTX PRO 6000.

Replacing Opus with a local 27B model is not a neutral backend swap. The
frontier model is the component that writes parsers, simulators, hypotheses,
and search code correctly. The harness amplifies capability; it does not create
all of that capability from nothing.

### 2. The inference allowance differs by orders of magnitude

Kaggle permits at most nine hours for the complete 110-game evaluation:

```text
9 hours / 110 games = 294.5 seconds per game on average
```

Games can be interleaved and model requests can be batched, so 294.5 seconds is
not a literal per-game deadline. It is nevertheless the correct total-compute
scale. A public harness configured for thousands of frontier calls per game
cannot be carried over unchanged.

### 3. Released-set performance may not generalize

All 25 `dev25` games and their implementations are public. Harnesses, prompts,
policies, and model releases have received repeated feedback from this fixed
set. A result can be honestly obtained and still be selected toward those
games. Kaggle's 110 games are unseen.

The Tycho paper is unusually clear about this: five public games were assigned
to harness development, policy selection used the whole released benchmark,
and the final result remains a public-set evaluation. This is valuable
research, but it is not a hidden-set estimate.

### 4. Some results use selection or retries

Pass@2, best-of-two, selective reruns, and model fleets answer a different
question from a single Kaggle execution. Always record the number of attempts,
whether the best trajectory was retained, model identity, reasoning effort,
and inference budget alongside an ARC score.

## What should be transferred into the Kaggle system

The repeated lesson across AVO, Tycho, Schema-like systems, and `arc-code` is
that the productive unit is an evidence-driven loop, not a long prompt:

1. Store every settled observation, action, outcome, and level boundary in an
   exact, queryable record.
2. Maintain compact persistent beliefs about controls, objects, dynamics,
   goals, hidden state, failed hypotheses, and uncertainty.
3. Turn promising hypotheses into executable transition models when useful.
4. Verify those models against all recorded transitions.
5. Use ordinary search or planning inside a verified model before spending
   scored environment actions.
6. Invalidate an action queue immediately when a predicted observation does
   not match reality.
7. Use a supervisor or deterministic stagnation detector to force a new probe,
   abstraction, or game switch when progress stops.
8. Separate discovery from execution and send guarded action macros for known
   behavior.

AVO's text-only 64 x 64 grid result is especially relevant: a high-scoring
system does not necessarily need a large vision-language model or image tokens.
Exact symbolic frames make change detection, replay, object tracking, and
world-model verification cheaper.

## Practical single-RTX-PRO-6000 architecture

The competition GPU has 96 GB of GDDR7 memory. A 27B-class FP8 model can fit,
but memory capacity alone does not prove that an agent will finish on time.
KV-cache size, context length, batch concurrency, decoding speed, Python tool
latency, and the number of model turns dominate the end-to-end budget.

A promising design is:

```text
110 game controllers
        |
        v
event-driven scheduler and compute allocator
        |
        +--> exact grid/diff/object extraction (CPU)
        +--> persistent structured memory (CPU RAM)
        +--> deterministic verifier/planner/search (CPU)
        +--> guarded action macro executor
        |
        v
one shared local model server on the RTX PRO 6000
  - actor prompt
  - world-model builder prompt
  - critic/supervisor prompt only when triggered
```

Do not load separate full-size actor, builder, and supervisor models. Share one
set of weights across roles and batch requests across games. Implement cheap
supervision with rules or a small model unless a difficult event justifies a
full 27B call.

Priority optimizations:

1. Use continuous batching across independent games.
2. Reuse stable prompt prefixes and keep context compact.
3. Store the full trace outside the model context; retrieve summaries and
   relevant transitions on demand.
4. Ask the model for executable abstractions or multi-action plans, not one
   fresh completion for every movement action.
5. Stop macros on mismatches, terminal frames, or unexpected action sets.
6. Allocate inference to games with the highest expected leaderboard gain per
   GPU-second.
7. Start with an optimized Blackwell-capable serving stack and profile the
   complete notebook before writing custom CUDA.

Custom kernels may eventually matter, especially for quantized attention,
prefill, decoding, or grid feature extraction. They are not the first-order
solution. Reducing a hundred model turns to ten useful turns is usually more
valuable than making the same hundred turns modestly faster. Write a kernel
only after traces show that an unsupported or inefficient operation is a
material portion of the nine-hour critical path.

## How the 40+ GPU cluster creates an advantage

The cluster does not relax the final one-GPU constraint; it accelerates the
outer development loop:

- Run public and community-game experiments over many seeds in parallel.
- Generate frontier-model teacher trajectories containing structured memory,
  hypotheses, executable world models, repairs, plans, and action decisions.
- Distill those behaviors into a locally deployable open model.
- Train on community games while holding out entire creators and mechanic
  families to measure genuine transfer.
- Sweep quantization, context policy, batch size, and scheduler settings.
- Reproduce the Kaggle nine-hour/one-GPU limit continuously, rather than only
  at submission time.

The defensible route is therefore **teacher-harness research on the cluster,
OOD validation, behavior distillation, and one-GPU deployment co-design**. A
literal port of a hosted Opus harness is useful as an oracle and trace
generator, not as the final Kaggle submission.
