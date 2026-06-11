# Epic: Digest Delivery

## Overview

Renders the daily top-5 digest as a Slack Block Kit message with 👍/👎 buttons and an email fallback, deploys the feedback endpoint to Render, and wires GitHub Actions to run it at 07:30 UTC. Failure alerts go to a personal Slack DM. A run report footer (entities scanned, cost, sources live) is appended to every digest.

## Architecture

```
ranker.get_top_n()
        │
        ▼
┌───────────────┐     ┌──────────────────────┐
│  renderer.py  │────►│  slack_sender.py     │
│  Block Kit    │     │  webhook + buttons   │
└───────────────┘     └──────────────────────┘
        │
        ├────────────────►┌──────────────────────┐
        │                 │  email_sender.py      │
        │                 │  Resend/SMTP fallback │
        │                 └──────────────────────┘
        │
        └────────────────►┌──────────────────────┐
                          │  feedback_api.py      │
                          │  FastAPI on Render    │
                          │  POST /feedback       │
                          └──────────────────────┘
```

## Success Criteria

- [ ] Slack message delivered with Block Kit formatting and 👍/👎 buttons at 07:30 UTC
- [ ] Button click writes to feedback table (verified via `sqlite3 data/dealradar.db "SELECT * FROM feedback"`)
- [ ] Email fallback sends if RESEND_API_KEY is set
- [ ] Run report footer shows: entities scanned, cost today (£), sources succeeded
- [ ] Failure alert POSTed to Slack DM within 60s of cron failure
- [ ] Feedback endpoint live on Render HTTPS URL

## Task Dependencies

```
Wave 0:
    01-renderer         (pure rendering, no external deps)
    02-feedback-api     (FastAPI endpoint, can be built independently)

Wave 1 (after renderer):
    03-slack-sender     (needs renderer output)
    04-email-sender     (needs renderer output)

Wave 2:
    05-render-deploy    (needs feedback-api built)
    06-run-report       (needs slack-sender wired)
```

## Estimated Effort

| Wave | Tasks | Duration |
|------|-------|----------|
| 0 | 2 | ~2h |
| 1 | 2 | ~3h |
| 2 | 2 | ~2h |
| **Total** | **6** | **~8h** |
