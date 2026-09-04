# Repository Instructions

Before making project changes, read `PROJECT_CONTEXT.md` completely, followed by
the design document relevant to the task. Treat it as the durable handoff from
earlier sessions and update it after material decisions or completed milestones.

The primary objective is ARC-AGI-3 Kaggle Milestone 2. Work deliberately from
reproducible experiments rather than adding broad untested features.

Preserve `HUMAN_DEV25/ls20/thoughts.txt` as raw user-authored evidence. Put
annotations and derived data in separate files.

Do not implement hidden-test exfiltration, encoded logging, game-ID branches, or
other leaderboard-probing mechanisms. Competition-mode logs must remain
aggregate-only.

The repository is public. Never commit credentials, cluster hostnames, tokens,
private keys, or other sensitive infrastructure information.
