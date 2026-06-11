# Epic: Feedback Loop

## Overview

Closes the learning loop: user 👍/👎 signals from the feedback table feed back into the LLM scoring prompt as few-shot examples, recurring downvote patterns trigger additions to the thesis exclude list (with human-confirm), and a precision metric is computed weekly and shown in each digest footer.

## Architecture

```
feedback table
       │
       ├──────────────────────►┌─────────────────────┐
       │                       │  fewshot_updater.py │
       │                       │  thumbs-down → neg  │
       │                       │  few-shot examples  │
       │                       └─────────────────────┘
       │
       └──────────────────────►┌─────────────────────┐
                               │  exclude_updater.py │
                               │  pattern detection  │
                               │  + human-confirm    │
                               └─────────────────────┘
                                         │
                                         ▼
                               config/thesis.yaml (updated)

feedback table ─────────────►┌──────────────────────┐
                              │  precision_tracker.py│
                              │  weekly metric       │
                              └──────────────────────┘
```

## Success Criteria

- [ ] After 3 thumbs-down on similar entities, a new negative few-shot example appears in `score_fewshot.txt`
- [ ] After 5 thumbs-down with a common keyword pattern, a human-confirm prompt is triggered before adding to thesis `exclude`
- [ ] Precision metric (thumbs-up / total rated) computed weekly and stored in SQLite
- [ ] Precision trend appears in digest footer (e.g. "Precision (7d): 62% ↑ from 45% last week")

## Task Dependencies

```
Wave 0:
    01-fewshot-updater
    02-precision-tracker

Wave 1:
    03-exclude-updater   (builds on fewshot patterns)
```

## Estimated Effort

| Wave | Tasks | Duration |
|------|-------|----------|
| 0 | 2 | ~3h |
| 1 | 1 | ~2h |
| **Total** | **3** | **~6h** |
