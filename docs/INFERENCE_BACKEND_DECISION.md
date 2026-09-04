# Inference Backend Decision: SGLang vs vLLM

Status: provisional decision, benchmark required

Date: 2026-09-04

## Decision

Use **SGLang as the first implementation backend**. Keep vLLM fully supported
through the same OpenAI-compatible client and treat it as both the reference and
fallback backend.

This is not a claim that SGLang is universally faster. The production backend
will be frozen only after both engines run the ARC-shaped benchmark on one RTX
PRO 6000 Blackwell Server Edition GPU using the exact model artifact and pinned
offline dependencies intended for Kaggle.

## Why SGLang first

Our workload is an agent program rather than independent chat completion:

- many game sessions alternate between deterministic actions and model calls;
- prompts share a stable system/tool prefix;
- each session repeatedly extends or compacts its own history;
- structured decisions and reasoning separation are required;
- request lengths and arrival times are irregular;
- total notebook completion time matters more than one-request tokens/second.

SGLang is explicitly designed around agentic programs, RadixAttention prefix
reuse, continuous batching, structured outputs, reasoning parsers, and several
speculative-decoding methods. That makes it the better first hypothesis for our
request graph.

vLLM now also has automatic prefix caching, continuous batching, Qwen3 reasoning
parsing, and structured outputs. Therefore no architectural component may import
SGLang-specific objects outside the backend adapter.

## Batch-size correction

Kaggle assigns one GPU, but the solver should not issue only one request at a
time. The competition gateway exposes many independent environments. While one
game is waiting for a model decision, other games can supply work to the same
server.

The target is:

```text
many environment actors -> bounded decision queue -> one inference server
                                            |
                                            +-> continuous dynamic batches
```

Concurrency 1 remains important for interactive latency and local debugging,
but selecting the engine from that result alone would optimize the wrong
objective. We care about full-run makespan, completed levels, and GPU-seconds.

## Initial model-serving policy

- Model: `Qwen/Qwen3-4B-Thinking-2507`.
- Precision: BF16 first; do not quantize before measuring a need.
- Tensor parallelism: 1.
- Active context: begin at 16K, then test 32K. External memory must prevent
  unbounded prompt growth.
- Reasoning parser: Qwen3.
- Maximum generated tokens: request-class dependent, never one global maximum.
- Prefix cache: enabled.
- Concurrent in-flight requests: tune across 1, 4, 8, 16, and 32.
- Speculative decoding: disabled for the reference run.
- Structured output: constrain only the final decision, not hidden reasoning.
- Sampling: pin Qwen-recommended thinking parameters for the first accuracy
  baseline, then tune only through controlled experiments.

The thinking-only model is not called for every movement. A model call should
produce a probe, a plan, or a plan repair. The deterministic executor may carry
out a validated multi-action macro until an observation violates its prediction.

## Backend-neutral interface

Both servers expose an OpenAI-compatible endpoint. The harness depends on this
internal contract:

```text
InferenceRequest
  request_id
  session_id
  messages
  max_output_tokens
  sampling_profile
  decision_schema
  deadline

InferenceResponse
  request_id
  reasoning_text       # optional diagnostic; not persisted into model history
  final_text
  prompt_tokens
  generated_tokens
  finish_reason
  latency
```

The adapter is responsible for translating schema and reasoning-parser options.
The Rust core validates `final_text` into a typed `Decision`. Invalid output is
repaired deterministically when unambiguous; otherwise one bounded correction
request is permitted.

## Representative benchmark

Run on one full RTX PRO 6000, not across multiple GPUs. Use the same container,
driver, CUDA, PyTorch, model files, tokenizer files, chat template, and sampling
configuration for both engines.

### Request shapes

| Class | Prompt | Output cap | Purpose |
| --- | ---: | ---: | --- |
| reflex | 2K | 128 | small correction or action selection |
| probe | 4K | 512 | choose an information-gaining action |
| plan | 8K | 1K | infer mechanics and form a plan |
| repair | 16K | 2K | reconcile contradictory evidence |

Replay three cache conditions:

1. cold, unrelated prompts;
2. common static system/tool prefix across sessions;
3. realistic growing and compacted per-game histories.

For each condition, sweep concurrency 1, 4, 8, 16, and 32. Run enough requests
to pass warmup and report distributions rather than one timing sample.

### Measurements

- successful request rate;
- time to first token, time per output token, and end-to-end latency;
- prompt, output, and total token throughput;
- p50, p95, and p99 latency per request class;
- prefix-cache hit rate and prefill work avoided;
- peak GPU and host memory;
- server startup time and offline install time;
- output equivalence under fixed seeds where determinism is available;
- hangs, malformed responses, OOMs, and recovery behavior;
- projected and measured end-to-end ARC evaluation time.

Use the SGLang benchmark client against both OpenAI-compatible backends, plus an
ARC trace-replay driver. Flush or restart caches between cold-cache runs.

## Selection rule

Select SGLang if it completes the ARC replay workload at least 10% faster than
vLLM without reducing valid-decision rate or reliability. Select vLLM if the
difference is below 10%, because the mirrored public Kaggle baseline already
demonstrates a working vLLM packaging path. A reliability failure, unsupported
model feature, or irreproducible offline wheelhouse disqualifies a backend even
if its microbenchmark is faster.

Do not select based solely on vendor throughput claims or concurrency-1 decode
speed.

## Speculative decoding gate

After the non-speculative backend is frozen, test speculation as a separate
experiment. Compare n-gram/prompt lookup, a small standalone draft, and EAGLE
only when compatible draft weights exist. Record accepted tokens per step and
full-run score per GPU-second. Disable speculation if batching, sampling, or low
acceptance makes end-to-end performance worse.

## Blackwell and offline packaging

Kaggle's `g4-standard-48` provides one RTX PRO 6000 GPU, 48 vCPUs, and about
180 GiB of host memory; the GPU has 96 GB GDDR7. Blackwell-compatible PyTorch,
CUDA, attention kernels, SGLang/vLLM, and their transitive wheels must be pinned
and attached as notebook inputs. The cluster build job produces the wheelhouse;
the notebook performs only offline installation and checksum validation.

## Sources

- [SGLang documentation](https://docs.sglang.io/)
- [SGLang serving benchmark](https://docs.sglang.ai/developer_guide/bench_serving)
- [SGLang speculative decoding](https://github.com/sgl-project/sglang/blob/main/docs_new/docs/advanced_features/speculative_decoding.mdx)
- [Qwen's SGLang deployment guide](https://github.com/QwenLM/Qwen3/blob/main/docs/source/deployment/sglang.md)
- [vLLM automatic prefix caching](https://docs.vllm.ai/en/latest/design/prefix_caching/)
- [vLLM structured outputs](https://docs.vllm.ai/en/stable/features/structured_outputs/)
- [vLLM benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/)
- [Google Cloud G4 machine series](https://cloud.google.com/compute/docs/accelerator-optimized-machines#g4_series)
- [NVIDIA RTX PRO 6000 Server Edition](https://docs.nvidia.com/enterprise-reference-architectures/rtx-pro-ai-factory/latest/components.html)
