# Human reasoning trace protocol for `dev25`

Last updated: 2026-09-04

## Decision

Recording a careful human solve of all 25 released games is a high-value
experiment. The useful artifact is not a polished explanation of each
solution. It is a synchronized record of how beliefs changed while the game
was still unknown:

```text
frame -> observation -> uncertainty -> proposed experiment -> prediction
      -> action -> observed result -> belief update -> plan
```

This can expose reusable cognitive operations for the harness and provide
targets for a small policy/reasoning model. It must not become a collection of
game-specific scripts.

The official human dataset already contains 342 step-by-step replays over the
released games. Our new contribution is the missing semantic layer: what the
human thought an action would distinguish, which hypothesis it supported, and
why the plan changed. See the [official human dataset announcement](https://arcprize.org/blog/arc-agi-3-human-dataset)
and [recording format](https://docs.arcprize.org/recordings).

## What to capture

Use three synchronized layers and never mix them silently.

1. **First-contact trace:** brief think-aloud statements made before and after
   decisions. This is the main causal evidence.
2. **Environment record:** exact frames, actions, timestamps, score, and state
   in ARC JSONL format. This is the ground truth.
3. **Retrospective annotation:** richer explanation written after the session.
   It is useful, but it is explicitly labelled `posthoc` because hindsight
   removes uncertainty and tends to rationalize mistakes.

Capture decisions, not prose volume. A decision boundary occurs when the
solver chooses an informative probe, changes a hypothesis or plan, takes an
irreversible/risky action, begins a repeated action macro, stops a macro, or
crosses a level boundary. Repeated moves under an unchanged plan need one
macro record rather than one essay per action.

## First-contact rules

For a primary trace, the participant must not have previously:

- played or watched a replay of the game;
- inspected the implementation, game description, or solution;
- received a hint about the mechanics or goal;
- retried the game before starting the recording.

Record exposure honestly as `first_contact`, `seen_unsolved`, or
`experienced`. Never discard an exposed run; store it in a separate analysis
stratum. One person can produce at most one true first-contact trace per game.

Use a pseudonymous participant ID. Keep screen/audio capture under
`HUMAN_DEV25/raw/`; that directory is git-ignored. Derived JSONL may be checked
in after removing usernames, paths, tokens, and other incidental data.

## Pilot, then freeze

Do not immediately consume all 25 first-contact opportunities.

1. Have another person choose three game IDs without describing them. The
   three should span different input modes if that can be arranged without
   revealing mechanics.
2. Record the three sessions with the protocol below.
3. Align speech to actions, identify fields that were confusing or missing,
   and revise the schema once.
4. Freeze the protocol version before recording the other 22 games.

Changing the questions halfway through all 25 would make comparisons weaker.

## Live protocol

Run screen/audio capture and the ARC environment recorder. At the beginning,
say the session ID and make one visible synchronization action or marker.

At each meaningful decision boundary, speak these short tags:

```text
OBS:      What changed or appears causally important?
BELIEF:   What are the leading goal/mechanic hypotheses and confidence?
QUESTION: What uncertainty most blocks progress?
PROBE:    Which action or macro will distinguish hypotheses?
PREDICT:  What result is expected? What result would disconfirm the belief?
STOP:     When should the macro stop or the plan be abandoned?
```

Immediately after observing the result:

```text
RESULT:   What actually changed?
UPDATE:   Which belief or plan changed, and why?
SURPRISE: How unexpected was it from 0 to 1?
```

At a level boundary:

```text
TRANSFER: What controls, roles, rules, invariants, hazards, and plan fragments
          should persist into the next level?
```

Do not force constant narration. When attention is saturated, play normally
and mark the timestamp for immediate retrospective annotation. A recording of
natural behavior is more useful than behavior distorted by an onerous form.

## What the annotator should derive

Align each decision to the frame before the action and to the observed outcome.
Store records using `HUMAN_DEV25/trace.schema.json`. Preserve the verbatim
statement, then add normalized labels from this initial operator vocabulary:

- `segment_objects`
- `track_object_identity`
- `detect_frame_delta`
- `infer_control_mapping`
- `infer_object_role`
- `infer_goal`
- `track_hidden_state`
- `choose_information_gain_probe`
- `predict_transition`
- `verify_or_reject_hypothesis`
- `construct_local_world_model`
- `plan_route`
- `execute_guarded_macro`
- `detect_stagnation`
- `recover_or_reset`
- `compress_cross_level_memory`

Add a new operator only when an existing one cannot describe the decision.
Keep the original text so the taxonomy can be revised later.

## Turning traces into a harness

The trace should inform a division of labor:

| Component | Responsibility |
|---|---|
| Deterministic perception/state | frame differencing, object tracks, coordinates, collision/no-op detection, history |
| Belief manager | explicit hypotheses, confidence, evidence, contradictions, unknowns |
| Experiment selector | choose the cheapest action that best separates live hypotheses |
| World model/search | predict candidate transitions and plan once mechanics are sufficiently stable |
| Policy model | resolve ambiguous object roles, goal semantics, experiment choice, and plan repair |
| Macro executor | issue verified action sequences with guards; interrupt on unexpected deltas |
| Memory | carry only verified mechanics and compact unresolved questions across levels |

The model should emit compact typed decisions rather than a long chain of
thought. Suitable training targets are `belief_update`, `probe`,
`predicted_outcome`, `action_macro`, `guard`, `plan`, and `memory_write`.
Private free-form reasoning can still occur internally, but verbose output is
not itself the product and consumes inference time.

One expert's 25 traces are enough to discover a good representation and expose
harness requirements, but not enough by themselves to train a robust model.
After freezing the representation:

1. label a sample of the official 342 human replays with the same operators;
2. generate counterfactual and failed trajectories locally on `dev25`;
3. collect the same fields on procedurally varied and creator-held-out
   `community_ood` games;
4. recruit additional first-contact solvers to detect personal heuristics that
   do not generalize.

## Small-model and speculative-decoding experiment

Treat Qwen3-4B/8B as candidates, not assumptions. Compare them with at least
one stronger model behind the same harness and under both of these budgets:

- equal wall-clock time in the exact one-GPU submission environment;
- equal GPU-seconds during development.

Measure:

- RHAE and levels completed, paired by game and seed;
- useful score gained per GPU-minute;
- model calls, input/output tokens, and tokens per decision;
- time-to-first-token, inter-token latency, total batch throughput, and GPU
  utilization;
- speculative acceptance rate and mean accepted draft length;
- invalid/no-op actions, resets, contradictions detected, and macro aborts.

Benchmark at the concurrency expected in the submission. Speculative decoding
primarily attacks serial inter-token latency; draft verification has overhead
and can lose when acceptance is low or continuous batching already saturates
the GPU. Compare at least:

1. normal continuous batching;
2. prompt lookup / n-gram speculation for structured repetitive outputs;
3. a much smaller draft model, if memory and acceptance justify it;
4. a checkpoint with native MTP only when the chosen model actually supports
   it.

The governing metric is not raw tokens/second. It is leaderboard score per
wall-clock second under the Kaggle constraints. Often the first throughput win
will be emitting a 50-token typed decision instead of a 1,000-token narrative.

Current vLLM guidance likewise describes speculative decoding as workload-
dependent and reports different gains by algorithm and request rate; benchmark
the deployed configuration rather than assuming a speedup. See the
[vLLM speculative decoding documentation](https://docs.vllm.ai/en/latest/features/spec_decode/).

## Falsifiable gates

Do not promote a design because a transcript looks intelligent. Require these
gates:

1. **Representation gate:** two annotators can independently encode the same
   pilot decisions with acceptable agreement.
2. **Prediction gate:** the stored beliefs predict action outcomes better than
   a frame/action-only baseline.
3. **Ablation gate:** removing the belief/probe/memory component reduces held-
   out performance.
4. **Generalization gate:** gains survive mechanic-family-held-out
   `community_ood`, not just replay of `dev25`.
5. **Deployment gate:** gains survive the one-GPU, nine-hour submission twin
   with the exact model quantization, batching, and context policy.

This is how the human study becomes engineering evidence instead of another
source of compelling but untestable ideas.
