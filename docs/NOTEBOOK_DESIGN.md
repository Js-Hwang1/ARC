# ARC-AGI-3 Submission Notebook Design

Status: initial design

Date: 2026-09-04

## Objective

Produce a public, reproducible Kaggle notebook that runs a general ARC-AGI-3
agent on one `g4-standard-48` machine within nine hours, with internet disabled.
The notebook is a deployment artifact; the solver is developed and tested as
normal source packages on the RTX PRO 6000 cluster.

The initial model is `Qwen3-4B-Thinking-2507`. SGLang is the provisional primary
backend and vLLM is the reference/fallback. The notebook must be able to switch
between them with configuration rather than solver changes.

## Design principles

1. Keep the notebook thin. Do not develop substantial logic in notebook cells.
2. Fail before model loading if an input, version, digest, GPU capability, or
   required environment variable is wrong.
3. Use the same solver path in public evaluation and competition reruns. Only
   environment discovery, output verbosity, and gateway configuration may vary.
4. Discover games from the official API. Never branch on hidden game IDs,
   ordering, or split membership.
5. Preserve raw frames internally but never export hidden frames, identifiers,
   action traces, encodings, or per-game diagnostics from a scored run.
6. Stop gracefully before Kaggle's hard timeout and preserve a valid automatic
   submission for all work completed so far.
7. Pin and checksum everything needed offline.

## Deployment artifact layout

The committed source tree should evolve toward:

```text
notebooks/
  arc_agi_3_submission.ipynb       thin Kaggle entrypoint
python/
  arc_agent/
    config.py                      immutable validated configuration
    competition.py                 official API adapter
    inference.py                   backend-neutral client
    scheduler.py                   environment actors and backpressure
    runtime.py                     lifecycle and deadline management
rust/
  Cargo.toml
  crates/
    arc-core/                      types, perception, memory, planning tools
    arc-py/                        PyO3 bindings
schemas/
  decision.schema.json
  observation.schema.json
packaging/
  kaggle-lock.json                 input paths, versions, and SHA-256 digests
  build-wheelhouse.sh              executed on compatible cluster node
tests/
  traces/                          public-game replay fixtures
```

The notebook attaches four categories of immutable Kaggle input:

- official competition data and ARC wheels;
- model weights/tokenizer/chat template;
- pinned SGLang or vLLM offline wheelhouse;
- our Python package, Rust wheel, schemas, manifests, and public replay assets.

The cluster may use a custom Docker image to build and test these artifacts, but
the notebook cannot pull or run that image. See `OFFLINE_PACKAGING.md`.

## Notebook cells

The committed notebook should contain approximately these cells and no hidden
state from an interactive session.

### 1. Manifest

Display the submission name, Git commit, model artifact/version, backend,
package versions, schema versions, and build timestamp. Define no solver logic.

### 2. Runtime preflight

Validate:

- `KAGGLE_IS_COMPETITION_RERUN` and gateway settings;
- Python and glibc compatibility;
- one visible RTX PRO 6000 GPU with the expected compute capability and memory;
- CUDA driver/runtime compatibility;
- 48 logical vCPUs and sufficient host memory as advisory checks;
- internet-offline environment;
- free disk space and writable `/kaggle/working`;
- the nine-hour deadline and safety margin.

Hardware checks may warn about benign host variation during local/public runs,
but a missing GPU or incompatible native wheel must fail immediately.

### 3. Input verification

Resolve every attached input through explicit candidates, require exactly one
match, and verify file sizes and SHA-256 digests against `kaggle-lock.json`.
Never recursively select the first vaguely matching model or wheel directory.

### 4. Offline installation

Install pinned wheels with `pip --no-index --find-links`. Do not invoke `apt`,
Git, Curl, Hugging Face Hub, or a source compiler. Set all model libraries to
offline mode before importing them. The wheelhouse is produced and smoke-tested
inside a cluster Docker image based on the recorded Kaggle image digest.

### 5. Package import and configuration

Import the packaged solver and construct one immutable `RunConfig`. Print a
redacted configuration. Secrets and gateway credentials must never be printed.

### 6. Inference-server launch

Launch SGLang or vLLM as a child process in its own process group. Capture logs
to a bounded local file, wait on a health endpoint, verify the served model ID,
then perform one short warmup request. A startup failure must include the last
bounded log lines and exit rather than hanging.

Reference SGLang shape, with the exact flags pinned after benchmarking:

```text
python -m sglang.launch_server
  --model-path <verified local model path>
  --host 127.0.0.1
  --port 30000
  --reasoning-parser qwen3
  --mem-fraction-static <benchmarked value>
  --max-running-requests <benchmarked value>
```

Speculative decoding is off in the reference notebook until an ARC replay
benchmark demonstrates a gain.

### 7. Competition adapter

Create the official Arcade client, discover available environments, and create
environment actors. Public evaluation may use released environment files; a
competition rerun uses the live gateway. Both paths instantiate the same agent,
prompt builder, tools, action validator, and scheduler.

### 8. Agent execution

Run the scheduler under the soft deadline. Emit periodic aggregate health only:

- elapsed and remaining wall time;
- number of active/finished/failed actors;
- aggregate completed levels and actions;
- inference queue depth and aggregate token counts;
- process/GPU memory and recoverable error counts.

Do not emit frames, per-game content, game IDs, prompts, model reasoning, or
action sequences in competition mode.

### 9. Graceful shutdown

Stop accepting new planning requests at the drain deadline, allow bounded
in-flight work to finish, close scorecards, terminate the model server, and
confirm that the competition-generated submission artifact exists. Cleanup is
idempotent and executes from `finally` and signal handlers.

### 10. Public diagnostics

Only non-competition runs may render replay timelines, prompt packets, model
reasoning, per-game metrics, and failure reports. This cell becomes a no-op in a
scored rerun.

## Runtime topology

```text
                        +----------------------+
official game API ----> | environment actors   |
                        | bounded concurrency  |
                        +----------+-----------+
                                   |
                         new frame or animation
                                   |
                        +----------v-----------+
                        | Rust state/perception|
                        | belief + plan checks |
                        +----+------------+----+
                             |            |
                    macro still valid     | model decision needed
                             |            v
                             |    +------------------+
                             |    | priority request |
                             |    | queue/backpressure|
                             |    +--------+---------+
                             |             |
                             |    +--------v---------+
                             |    | one SGLang/vLLM  |
                             |    | continuous batch |
                             |    +--------+---------+
                             |             |
                             +------<------+ typed Decision
                                   |
                        +----------v-----------+
                        | action validation    |
                        | execute or safe probe|
                        +----------------------+
```

## Environment actor states

Each actor follows an explicit state machine:

```text
NEW -> RESETTING -> OBSERVING -> DECIDING -> EXECUTING
                     ^             |            |
                     +-------------+------------+

terminal exits: WON | GAME_OVER | SOFT_DEADLINE | FAILED
```

An actor may execute a macro without entering `DECIDING` again while every
observed result remains compatible with the macro's prediction. Unexpected
change, a risk threshold, a level transition, or an invalid action forces a
fresh decision.

## Scheduler

The scheduler is asynchronous and bounded at three separate layers:

- number of active game actors;
- number of queued model decisions;
- number of inference requests admitted by the backend.

Initial values are configuration, not constants. Begin cluster tests around 24
active actors and sweep inference concurrency 1, 4, 8, 16, and 32. Backpressure
must pause actors before host memory or request queues grow without bound.

Priority should initially be fair round-robin with deadline awareness. Do not
introduce score-based abandonment or level-dependent prioritization until replay
evidence shows it improves the official aggregate metric.

## Model-call classes

Use separate output budgets and prompts:

- `REFLEX`: select among well-understood immediate actions;
- `PROBE`: choose a low-cost experiment and predict its observation;
- `PLAN`: infer mechanics and produce a multi-step conditional plan;
- `REPAIR`: resolve a contradiction or recover from a failed plan;
- `SUMMARIZE`: compact verified memory without selecting an action.

`Qwen3-4B-Thinking-2507` should mainly receive `PROBE`, `PLAN`, and `REPAIR`.
Routine execution belongs in Rust. No reasoning text is appended to future chat
history; only validated conclusions, predictions, actions, and results persist.

## Typed decision contract

The final model content must encode:

```json
{
  "mode": "probe | plan | execute | repair",
  "intent": "short falsifiable description",
  "action": {"kind": "ACTION1", "x": null, "y": null},
  "expected_observation": "what should change if the belief is correct",
  "plan": [],
  "memory_updates": [],
  "stop_macro_if": []
}
```

The production schema will use exhaustive enums and conditional requirements:
coordinates are forbidden except for `ACTION6`, and `ACTION6` requires in-range
coordinates. The Rust validator also checks the environment's available-action
set and verified invariants.

## Memory policy

Maintain four layers:

1. immutable raw step/animation log;
2. deterministic derived observations and object tracks;
3. evidence-linked verified facts and live hypotheses;
4. a compact model-facing working set with an explicit token budget.

Summaries never replace the raw log. Every verified claim points back to step
IDs. Contradicted claims remain recorded so the model does not repeat failed
hypotheses.

## Failure containment

- One game actor failure must not stop other games.
- Model timeouts have a bounded retry, then a safe deterministic fallback.
- Malformed output gets deterministic repair or one correction request.
- Repeated no-op actions trip a circuit breaker.
- Server death triggers at most one controlled restart if the time budget allows.
- OOM handling reduces admission concurrency; it never silently changes model
  precision, context policy, or sampling configuration.
- All retry and fallback behavior is included in public replay tests.

## Time budget

Treat nine hours as an absolute outer bound, not a target. Initial policy:

- startup/install/model load budget: 20 minutes;
- active solver deadline: 8 hours 20 minutes after notebook start;
- drain and scorecard-close budget: 10 minutes;
- emergency buffer: 10 minutes.

These values must be replaced by measured startup and teardown distributions.
The runtime uses monotonic time and carries deadlines into every queue operation
and inference request.

## Reproducibility and publication

The public notebook must identify:

- Git commit and dirty-state check;
- model owner, exact version/revision, filenames, and digests;
- Python, Rust wheel, engine, CUDA, and PyTorch versions;
- chat template digest and sampling configuration;
- all attached Kaggle input versions;
- build commands and lockfiles;
- seeds and nondeterministic CUDA settings;
- expected hardware and tested peak resource use.

The milestone notebook and every required input must be publicly accessible
under compatible open-source terms by the deadline.

## Acceptance gates before the first custom submission

1. Clean cluster node can reproduce the offline install from the pinned inputs.
2. Synthetic Rust/Python interface tests pass.
3. Public recordings replay deterministically through perception and memory.
4. Agent completes a full dev25 run without a process leak, deadlock, unbounded
   queue, malformed action, or hard timeout.
5. SGLang/vLLM benchmark decision is recorded.
6. A Kaggle Save & Run succeeds with internet disabled on the competition GPU.
7. Scored-run logs are audited for hidden-case data leakage.
8. A soft-deadline drill produces a valid graceful shutdown.

## Immediate implementation order

1. Capture the cluster software/hardware fingerprint and build the reproducible
   CUDA environment.
2. Save a minimal Kaggle RTX notebook to capture its exact base image and
   runtime fingerprint, then build the offline overlay in that base image.
3. Implement the backend-neutral benchmark and run SGLang versus vLLM.
4. Scaffold the Rust core and Python bridge described in
   `HARNESS_ARCHITECTURE.md`.
5. Create a minimal notebook that only preflights, installs, launches the
   selected server, makes a warmup request, and shuts down.
6. Add official environment discovery and a random/legal-action smoke agent.
7. Add the observation store and perception packet.
8. Integrate the first typed Qwen decision loop on `ls20`.

## Sources

- [ARC-AGI-3 Kaggle overview and code requirements](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)
- [ARC-AGI-3 Kaggle data/API description](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/data)
- [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks)
- [Offline packaging strategy](OFFLINE_PACKAGING.md)
- [SGLang documentation](https://docs.sglang.io/)
- [vLLM documentation](https://docs.vllm.ai/)
- [Qwen3-4B-Thinking-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)
