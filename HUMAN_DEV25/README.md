# `dev25` human traces

Use this directory for structured human reasoning traces over the 25 released
ARC-AGI-3 games.

Read [`../docs/HUMAN_REASONING_TRACE_PROTOCOL.md`](../docs/HUMAN_REASONING_TRACE_PROTOCOL.md)
before consuming a first-contact game. Validate normalized JSONL records
against [`trace.schema.json`](trace.schema.json). [`session_notes.md`](session_notes.md)
is a lightweight live/post-session worksheet; it is not a substitute for the
environment recording.

Recommended layout:

```text
HUMAN_DEV25/
  raw/                    # screen/audio/environment captures; git-ignored
  aligned_media/          # timestamp-aligned derivatives; git-ignored
  <game_id>/
    recording.jsonl       # ARC environment recording
    reasoning.jsonl       # records conforming to trace.schema.json
    notes.md               # retrospective notes, explicitly labelled posthoc
```

Do not put hidden leaderboard data here. These traces are only for released or
properly licensed community games.
