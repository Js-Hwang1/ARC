# FOYSAL Qwen3.8 public baseline

This directory mirrors the latest public source of:

- Kaggle ref: `foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b`
- Observed version: 6
- Public leaderboard score: 2.23
- License shown by Kaggle: Apache 2.0

The notebook is a public baseline, not the source of the current overall
leaderboard leader. Preserve the original attribution and license.

Attached Kaggle inputs required by the notebook:

- Competition: `arc-prize-2026-arc-agi-3`
- Dataset: `driessmit1/arc3-vllm-h100-wheelhouse-v3`
- Dataset: `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`
- Model: `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1`
- Accelerator: `NvidiaRtxPro6000`
- Internet: disabled

Refresh the mirror with:

```bash
python3 scripts/fetch_public_kaggle_notebook.py
```

Before pushing a copy, create `kernel-metadata.json` with a new notebook ID
under your own Kaggle account and attach the exact inputs above. A Kaggle
competition rerun consumes the team's daily submission allowance; a normal
notebook Save & Run does not.

Run the static checks with:

```bash
python3 scripts/preflight_public_baseline.py
```

The pulled notebook's embedded Kaggle header says `isGpuEnabled: false`, while
the authoritative kernel metadata says `enableGpu: true` and selects
`NvidiaRtxPro6000`. Do not push the notebook without an explicit GPU-enabled
`kernel-metadata.json` and `--accelerator NvidiaRtxPro6000`.

The scoring rerun will return an aggregate public-leaderboard score only.
Do not attempt to persist, encode, or exfiltrate hidden frames or case
identifiers in notebook outputs.
