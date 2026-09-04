# ARC-AGI-3 Harness Architecture

Status: proposed baseline architecture, 2026-09-04

## Decisions

1. Keep the competition-facing adapter in Python. The official ARC-AGI-3
   package and public agent templates expose Python callbacks, and the Kaggle
   submission is a Python notebook.
2. Put the deterministic domain core in Rust. Rust owns lossless state,
   perception, exact geometry, temporal analysis, search, validation, and the
   typed model/tool contracts.
3. Do not use Cython initially. It is useful for accelerating Python loops but
   does not provide the ownership, exhaustive enums, or memory-safety benefits
   motivating a compiled core.
4. Treat model serving as a replaceable backend:
   - local Apple Silicon: MLX-LM;
   - Kaggle RTX PRO 6000: vLLM or the fastest verified CUDA backend;
   - experiments: the same harness can target 4B, 8B, or larger checkpoints.
5. Prebuild the Kaggle Rust wheel for Linux x86-64. Do not depend on a Rust
   compiler or the internet being present during the scored notebook run.
6. Optimize score per GPU-second, not harness microbenchmarks. A 64-by-64 frame
   has only 4,096 cells, so model inference, context construction, and failed
   actions are expected to dominate until profiling proves otherwise.

## Runtime boundary

```text
ARC-AGI-3 Python API
        |
        v
thin Python adapter  <---->  inference backend (MLX locally / vLLM on Kaggle)
        |
        | one batched call per environment step
        v
Rust core
  - immutable raw event log
  - frame and animation analysis
  - connected components and object tracks
  - exact coordinates, transforms, and path search
  - verified facts, hypotheses, and evidence
  - prompt packet construction
  - action and invariant validation
```

Python should not contain game-solving rules. Its responsibilities are process
lifecycle, official API calls, concurrency, model I/O, and conversion between
NumPy buffers and Rust types. The Python/Rust boundary must operate on complete
frame batches rather than making per-pixel calls.

## Core event types

The canonical state is an append-only sequence of raw events. Derived state is
recomputable and versioned so perception changes never destroy evidence.

```text
RawStep
  episode_id
  step_index
  action_sent: Option<Action>
  frames: T x H x W u8
  available_actions: set<ActionKind>
  game_state
  levels_completed

Observation
  current_frame_hash
  changed_cells
  animation_summary
  connected_components
  object_tracks
  spatial_relations

Belief
  proposition
  status: hypothesis | verified | contradicted
  supporting_step_ids
  confidence

Decision
  intent
  action
  expected_observation
  fallback
```

`Action` is an exhaustive enum. `ACTION6` carries a validated `(x, y)` point;
the other actions carry no coordinate payload. The executor rejects unavailable
actions, malformed coordinates, known no-ops, and decisions that violate a
verified invariant unless the decision explicitly requests a controlled probe.

## Model contract

The model receives a compact observation packet rather than an ever-growing
transcript:

- current progress and legal actions;
- current frame plus lossless access to raw frames;
- changed pixels, object table, and animation timeline;
- verified mechanics and live hypotheses with evidence;
- recent action/observation pairs;
- the current plan and unresolved question;
- on-demand exact tools such as crop, diff, path, transform, and count.

The model returns one typed `Decision`. Its hidden thinking is not copied into
the next turn. Only the final decision, prediction, result, and updated compact
memory persist. This follows Qwen's multi-turn recommendation and prevents
reasoning transcripts from consuming the context budget.

## Local 16 GB Apple Silicon target

Use the 4-bit MLX conversion of `Qwen3-4B-Thinking-2507`. Its weights are about
2.26 GB, leaving enough unified memory for MLX, macOS, the harness, and a useful
KV cache. Do not configure the native 262K context on a 16 GB machine.

For this model's 36 layers, 8 KV heads, and 128-dimensional heads, a 16-bit KV
cache is approximately 144 KiB per token:

| Active context | Approximate KV cache |
| ---: | ---: |
| 8K | 1.1 GiB |
| 16K | 2.3 GiB |
| 32K | 4.5 GiB |
| 64K | 9.0 GiB |

Start with an 8K or 16K active context and rely on the external event store and
compact memory. The local machine is suitable for functional iteration and
single-game experiments, but it is not a throughput proxy for the Kaggle GPU.

## Kaggle packaging

The checked public baseline currently reports Python 3.12.13. Build a pinned
PyO3/maturin wheel for the exact Kaggle Linux x86-64 environment and install it
offline from an attached Kaggle Dataset or notebook input:

```python
wheel_dir = Path("/kaggle/input/arc-harness-wheel")
wheels = list(wheel_dir.glob("arc_harness-*.whl"))
if len(wheels) != 1:
    raise RuntimeError(f"Expected one harness wheel, found: {wheels}")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--no-index",
    str(wheels[0]),
])
```

Production code must also verify the wheel's SHA-256 digest before installation.
Publish the Rust source, lockfile, build recipe, wheel, and license by the
applicable prize deadline.

Do not compile Rust during a scored run. The current Kaggle image documents a C
build toolchain but does not document a Rust toolchain, internet is disabled,
and compilation consumes the nine-hour wall-clock allowance.

## Performance policy

Do not write custom CUDA kernels for 64-by-64 grid manipulation. Keep those
operations on CPU unless profiles show material contention at full environment
concurrency. Spend GPU engineering effort first on model serving: batching,
prefix reuse, KV-cache policy, bounded output lengths, and only then speculative
decoding if it improves completed-game score per GPU-second.

Every optimization must report:

- first-attempt score on an unrevealed game;
- regression score on all previously seen games;
- community out-of-distribution score;
- actions, model calls, prompt tokens, generated tokens, wall time, and peak
  memory per game;
- score per GPU-second.

## First implementation slice

Implement only the following before adding semantic planners:

1. Rust types for `RawStep`, `Action`, `Observation`, and `Decision`.
2. Lossless ingestion of `T x H x W` frames and deterministic frame hashing.
3. Exact changed-cell sets, per-color connected components, bounding boxes, and
   animation summaries.
4. A typed Python bridge and JSONL replay CLI.
5. Synthetic tests plus a replay test from a real public-game recording.
6. A backend-neutral model client exercised against local MLX-LM.

This slice is deliberately game-agnostic. `ls20` can then be used to drive the
first missing capabilities without adding a game-ID branch.

## Sources

- [ARC-AGI-3 Kaggle overview](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)
- [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks)
- [Kaggle Python image](https://github.com/Kaggle/docker-python)
- [Qwen3-4B-Thinking-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)
- [MLX 4-bit conversion](https://huggingface.co/mlx-community/Qwen3-4B-Thinking-2507-4bit)
