# Project Context for Future Sessions

Last updated: 2026-09-04

Repository: `https://github.com/Js-Hwang1/ARC` (public)

This file is the durable handoff for a new Codex session. It is not a dump of
private chain-of-thought and cannot literally restore an earlier chat process.
It records the user's goals, verified facts, decisions, evidence, and next work.

## Start here

When resuming on another machine:

1. Read this file completely.
2. Read `docs/NOTEBOOK_DESIGN.md`.
3. Read `docs/HARNESS_ARCHITECTURE.md` and
   `docs/INFERENCE_BACKEND_DECISION.md`.
4. Check `git status`, the current branch, recent commits, and any new user
   changes before editing.
5. Preserve `HUMAN_DEV25/ls20/thoughts.txt` as raw human-authored evidence.
6. Continue from "Immediate next work" below unless the user changes priority.

## Objective

Win the ARC-AGI-3 Kaggle Milestone 2 on September 30, 2026 and remain eligible
for prize money. The user has access to more than 40 RTX PRO 6000 Blackwell
Server Edition GPUs and wants disciplined, fast experimental iteration.

The working hypothesis is that performance is primarily a harness, memory,
perception, and interaction-policy problem rather than a parameter-count-only
contest. The preferred initial model is `Qwen3-4B-Thinking-2507`, but model size
must remain an experimental variable rather than an article of faith.

## User's working preferences

- Make explicit architectural decisions; avoid unstructured "vibe coding."
- Use progressive reveal across the 25 development games.
- Optimize general mechanisms, not game-ID branches or memorized solutions.
- Use typed, safe implementation techniques. Rust is preferred for the domain
  core; Python is tolerated as a thin official-API/notebook adapter.
- Use the RTX cluster from the beginning; do not maintain a Mac inference path.
- Use daily Kaggle submissions as sparse out-of-distribution evidence, not as a
  hidden-test probing channel.
- Measure score and action efficiency as well as inference throughput.

## Current architecture decisions

1. Python notebook and thin Python adapter around the official ARC API.
2. Rust deterministic core through PyO3/maturin:
   - append-only raw events;
   - frame and animation analysis;
   - connected components/object tracks;
   - exact geometry, transforms, search, and counters;
   - evidence-linked beliefs and compact memory;
   - typed model/tool/action contracts and validation.
3. SGLang is the provisional primary inference backend.
4. vLLM remains a mandatory reference/fallback through the same
   OpenAI-compatible internal interface.
5. Select the production engine only after an ARC-shaped benchmark on one RTX
   PRO 6000. Do not select from batch-size-one performance alone.
6. Start Qwen3-4B-Thinking-2507 in BF16. Do not quantize without measured need.
7. One competition GPU should serve several asynchronous game sessions with
   continuous batching. Sweep inference concurrency 1, 4, 8, 16, and 32.
8. Do not enable speculative decoding until a non-speculative reference is
   stable and trace replay shows a score-per-GPU-second gain.
9. Model reasoning is not appended to future history. Persist only validated
   decisions, predictions, evidence, results, and compact memory.
10. The model selects probes, plans, and repairs. Rust executes verified macros
    and exact computations without another model call until predictions fail.
11. Prebuild all Linux x86-64 native wheels and inference dependencies. Kaggle
    performs offline installation only; no Rust compilation during scoring.
12. No custom CUDA kernel for 64-by-64 grid operations unless profiling later
    proves CPU contention. GPU work initially targets inference serving.
13. Docker is a cluster build/test tool, not the Kaggle deployable. Kaggle does
    not support Docker-in-Docker and cannot pull a registry image with internet
    disabled. Ship a pinned, checksum-verified offline wheelhouse/input overlay
    into Kaggle's managed container.

## Competition facts verified as of 2026-09-04

- Milestone 2 deadline: September 30, 2026 at 11:59 PM UTC, corresponding to
  7:59 PM EDT.
- Submission must be a Kaggle notebook.
- GPU notebook runtime limit: nine hours.
- Internet must be disabled.
- Freely and publicly available external data and pretrained models are allowed.
- Milestone eligibility requires making the notebook public under an open-source
  license by the deadline.
- Prize eligibility requires a complete reproducible/open-source solution.
- Kaggle uses Google Cloud `g4-standard-48`: one RTX PRO 6000, 48 vCPUs, about
  180 GiB host RAM, and 96 GB GPU memory.
- The current submission allowance has been treated as one scored submission per
  team per day. Reverify pinned Kaggle announcements before relying on it.
- A normal notebook Save & Run does not itself consume the scored submission;
  submitting its completed version does.

Authoritative overview:
https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

## Data splits and leakage boundary

Use the names:

- `dev25`: 25 released game environments; fully inspectable and replayable.
- `public_lb55`: 55 hidden games whose aggregate score drives the visible public
  leaderboard.
- `private_lb55`: 55 hidden games used for the private/final leaderboard.

The scored notebook may receive frames while acting, but those hidden frames,
game identities, action traces, or encodings must not be persisted or exfiltrated
through outputs/logs. Competition-mode diagnostics contain aggregates only.
Do not help infer or leak hidden/private cases.

See `docs/ARC_AGI_3_DATA_SPLITS.md`.

## Input and action format

The official environment returns a JSON/Pydantic-style frame object containing:

- `game_id`, `guid`;
- `frame`: `T x H x W` integers in `0..15`, with one or more animation frames
  and maximum grid size 64 by 64;
- `state`, `levels_completed`, `win_levels`;
- the previous `action_input`;
- `available_actions`;
- `full_reset`.

Coordinates use top-left `(0, 0)` and arrays are accessed `[y][x]`. The metadata
does not name objects, state goals, or explain action meanings. `ACTION6` carries
an `(x, y)` coordinate; legal clickable coordinates are not supplied. Every
animation frame must be retained and analyzed, not only the last frame.

Official data description:
https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data

## Scoring implications

For a completed level, relative human action efficiency is approximately:

```text
min(115, 100 * (human_actions / agent_actions)^2)
```

Later levels receive higher index weight, game scores are capped for leaderboard
purposes, and the leaderboard averages game scores. Completion usually dominates
tiny early-level action savings. The harness should avoid catastrophic wasted
actions, but should not refuse necessary information-gathering probes.

See `docs/ARC_AGI_3_SCORING_STRATEGY.md`.

## Evaluation protocol

Use `ls20` as the first vertical slice, but keep its oracle/manual reasoning
separate from the candidate general agent.

For progressive reveal:

1. Freeze the harness.
2. Reveal the next development game.
3. Record the blind first attempt.
4. Diagnose the missing general capability.
5. Patch the capability without a game-ID route.
6. Rerun every previously seen game.
7. Run community/out-of-distribution cases.
8. Reveal the next game only after regression gates pass.

Track at least:

- `seen_regression`;
- `next_game_first_attempt`;
- `community_ood`;
- actions, model calls, prompt/output tokens, time, peak memory;
- score per GPU-second.

The public 25 are demonstrative and hidden mechanics are intentionally broader,
so dev25 completion alone is weak evidence of hidden generalization. Continue
daily Kaggle submissions when a candidate passes local/OOD gates.

## Human reasoning evidence

The raw pilot is `HUMAN_DEV25/ls20/thoughts.txt`: 53 numbered observations over
seven levels. It contains useful patterns such as minimal control probes,
Manhattan targeting, hypothesis rejection, resource hierarchy, compositional
color/pattern/rotation reasoning, moving-object periodicity, and terminal-rule
revision.

Do not edit this raw file. It has missing exact frames/timestamps/action payloads
and one duplicated number; annotate it separately. Future traces should follow:

```text
observation -> belief -> unresolved question -> probe -> prediction -> action
-> result -> belief update -> plan
```

Synchronize screen/audio/environment JSONL and label retrospective reasoning as
`posthoc`. Pilot three games before freezing the trace protocol.

See `docs/HUMAN_REASONING_TRACE_PROTOCOL.md` and `HUMAN_DEV25/README.md`.

## External method evidence already reviewed

Common successful harness components across public projects:

- persistent memory and causal action-observation history;
- context compaction;
- raw plus symbolic visual representations;
- animation/difference access;
- legal-action and structured-output validation;
- scratch code/tools and plan recovery.

No consensus exists that explicit simulators, many handcrafted tools,
multi-agent orchestration, raw vision alone, or a 4B model are sufficient.
Public high-scoring systems usually use frontier models, and a disclosed Kaggle
milestone baseline uses a 27B model. Keep 4B, 8B, and 27B experiments possible.

Projects previously reviewed include Duck/TAAF, Reki/Forge, TAAF animation,
VISTA/AVO, Schema/Tycho/Retrodict, Prime/continual agents, and Astra results.
Do not conflate provider-harness results on other hardware/public25 with Kaggle's
single-GPU hidden evaluation.

## Public baseline in this repository

`baselines/foysal-qwen38-v6/` mirrors a public Apache-2.0 Kaggle notebook:

- reference: `foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b`;
- observed version: 6;
- model: Qwen3.8-27B FP8;
- public leaderboard score recorded: 2.23;
- observed public-evaluation runtime: about 2 hours 19 minutes;
- backend: vLLM through a bundled offline wheelhouse;
- public evaluation concurrency: 28.

This is a useful packaging/reference baseline, not the current leaderboard
leader and not the architecture to copy wholesale. See `SUBMISSION_RUNBOOK.md`.

## Repository map

- `PROJECT_CONTEXT.md`: this cross-session handoff.
- `AGENTS.md`: tells future coding agents to load this context.
- `docs/NOTEBOOK_DESIGN.md`: target Kaggle notebook and runtime lifecycle.
- `docs/HARNESS_ARCHITECTURE.md`: Rust/Python system boundaries.
- `docs/INFERENCE_BACKEND_DECISION.md`: SGLang/vLLM hypothesis and benchmark.
- `docs/OFFLINE_PACKAGING.md`: cluster Docker and Kaggle offline overlay flow.
- `docs/ARC_AGI_3_DATA_SPLITS.md`: released/hidden split terminology.
- `docs/ARC_AGI_3_SCORING_STRATEGY.md`: scoring priorities.
- `docs/HUMAN_REASONING_TRACE_PROTOCOL.md`: trace collection protocol.
- `docs/PUBLIC_100_VS_KAGGLE.md`: why public25 claims do not transfer directly.
- `HUMAN_DEV25/`: human reasoning artifacts and schema.
- `baselines/foysal-qwen38-v6/`: mirrored public notebook.
- `scripts/`: Kaggle baseline fetch and preflight utilities.
- `experiments/score_tracking.csv`: submission/evaluation ledger.

## Immediate next work

1. On one cluster RTX PRO 6000 node, record:
   - OS/kernel and container runtime;
   - exact GPU name, compute capability, driver, CUDA, and NVML;
   - CPU model/count, RAM, local storage;
   - Python, PyTorch, SGLang, vLLM, FlashInfer, and Triton compatibility.
2. Save a minimal Kaggle RTX notebook and record the exact Kaggle image digest
   and runtime fingerprint.
3. Build and offline-test the pinned wheelhouse overlay from that exact base
   image, following `docs/OFFLINE_PACKAGING.md`.
4. Create the backend-neutral ARC-shaped inference benchmark described in
   `docs/INFERENCE_BACKEND_DECISION.md`.
5. Run SGLang and vLLM in BF16 with identical Qwen3-4B-Thinking-2507 files,
   tokenizer, chat template, prompts, sampling, and seeds.
6. Freeze the first backend/version/wheelhouse only after the benchmark.
7. Scaffold the Rust `arc-core` types, perception slice, PyO3 bridge, and replay
   tests.
8. Create a minimal deployment notebook that preflights, verifies offline
   inputs, starts the chosen server, warms up, and shuts down safely.

## Open decisions

- Whether 4B has sufficient semantic/world-model ability once the harness is
  competent. Compare 4B/8B/larger under the same harness.
- Active prompt context and compaction threshold.
- Optimal environment actor count and inference admission concurrency.
- Whether constrained JSON affects Qwen reasoning quality; validate final-only
  constraint versus parse/validate/correct.
- Whether any speculative method has sufficient acceptance on actual ARC
  prompts.
- When semantic failures justify weight adaptation rather than harness changes.

## Guardrails

- No game-ID-specific routes in the candidate general agent.
- No private/hidden-case exfiltration, encoding, or log leakage.
- No secrets or Kaggle credentials in Git, notebooks, chat, or logs.
- Preserve user-authored raw data and unrelated worktree changes.
- Reverify time-sensitive Kaggle rules before submissions.
- The repository is public; never commit proprietary cluster credentials,
  internal hostnames, tokens, or sensitive operational details.
