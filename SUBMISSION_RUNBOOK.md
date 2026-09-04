# ARC-AGI-3 public-baseline submission runbook

Target notebook: `foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b`,
version 6, public score 2.23.

## Preferred exact-copy path

1. Open the public V6 notebook on Kaggle and choose **Copy & Edit**. This is
   safer than rebuilding its input graph because it preserves the attached
   input versions.
2. Confirm the copied notebook uses RTX PRO 6000, GPU enabled, internet
   disabled, and the ARC-AGI-3 competition data source.
3. Save & Run the copied notebook. This validation run does not spend the
   competition's scored-submission allowance.
4. Inspect the validation output for `submission.parquet`, dependency errors,
   model-load errors, and the expected roughly 2 hour 20 minute runtime.
5. Submit the completed notebook version to the competition once. This starts
   the hidden rerun and spends the team's daily allowance.
6. Record the returned public-leaderboard score in
   `experiments/score_tracking.csv`.

## CLI submission after the copied notebook completes

Do not paste a Kaggle token into chat or commit it to Git. Configure it locally,
then use the copied notebook's owner, slug, version, and output filename:

```bash
kaggle competitions submit arc-prize-2026-arc-agi-3 \
  -k YOUR_USERNAME/YOUR_COPIED_NOTEBOOK_SLUG \
  -v YOUR_COMPLETED_VERSION \
  -f submission.parquet \
  -m "Exact public Qwen3.8 V6 reproduction"
```

Poll the result with:

```bash
kaggle competitions submissions arc-prize-2026-arc-agi-3
```

The returned competition score is the aggregate score on the 55-game public
leaderboard split. It does not reveal per-game results or the score on the
other 55-game private split.

## Local mirror checks

```bash
python3 scripts/fetch_public_kaggle_notebook.py
python3 scripts/preflight_public_baseline.py
```

The source notebook carries a stale embedded `isGpuEnabled: false` field while
the live Kaggle kernel metadata correctly says GPU enabled and
`NvidiaRtxPro6000`. Do not rely on the embedded notebook field when uploading a
new kernel; explicitly request the accelerator.

