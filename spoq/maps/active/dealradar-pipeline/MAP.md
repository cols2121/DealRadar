# Map: DealRadar Pipeline

## Vision

DealRadar is a daily AI sourcing agent for pre-seed European startups, built as a portfolio project for the Playfair AI Engineer in Residence application (Summer 2026). The system scans public signals across Companies House, GitHub, Product Hunt, Hacker News, and RSS news feeds; scores candidates against a thesis with an LLM; and delivers a ranked 5-company digest to Slack and email with one-click feedback. Completing this map produces a live product running for 14+ consecutive days, used by 3–5 external users, with a demo video and public repo ready for application submission by Day 25.

## Program Structure

```
┌──────────────┐
│  foundation  │  DB schema, thesis config, LLM client, repo scaffold
│  (Wave 0)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  collectors  │  Companies House, GitHub, Product Hunt, HN, RSS
│  (Wave 1)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  enrichment  │  Dedupe, LLM scoring, evidence validation
│  (Wave 2)    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐     ┌──────────────────┐
│  digest-delivery │     │  feedback-loop   │
│  (Wave 3)        │────►│  (Wave 4)        │
└──────────────────┘     └──────────────────┘
```

## Epics

### foundation
- **Status:** pending
- **Estimated Hours:** ~6h
- **Dependencies:** none
- **Summary:** Bootstraps the entire project: public repo with README/DECISIONS.md, SQLite schema, Pydantic thesis config model, 30-line LLM client abstraction (Haiku default, Sonnet upgrade path), GitHub Actions cron skeleton, and smoke-test scripts for all external APIs. Nothing else can start until this is done.

### collectors
- **Status:** pending
- **Estimated Hours:** ~10h
- **Dependencies:** [foundation]
- **Summary:** Implements all five data collectors in priority order: Companies House (incorporations + director history), GitHub (repo velocity + org signals), Product Hunt (EU maker launches), Hacker News (Show HN + EU heuristics), and RSS (Sifted, Tech.eu, EU-Startups, TechCrunch EU). Each collector writes raw records to SQLite with a standardised schema. Includes the EU location normalisation lookup table.

### enrichment
- **Status:** pending
- **Estimated Hours:** ~8h
- **Dependencies:** [collectors]
- **Summary:** Cross-source entity deduplication (rapidfuzz, ~90% threshold), LLM scoring pipeline (thesis YAML injected, strict JSON output, cite-or-omit rule, 2 few-shot examples), token cost logging, and the ranker that produces a scored candidate list. This is the anti-hallucination core — every claim maps to an evidence URL.

### digest-delivery
- **Status:** pending
- **Estimated Hours:** ~8h
- **Dependencies:** [enrichment]
- **Summary:** Daily digest rendered as Slack Block Kit (top 5, 👍/👎 buttons, evidence links, run report footer) and email fallback via Resend/SMTP. GitHub Actions cron at 07:30 UTC. Tiny FastAPI feedback endpoint deployed to Render free tier to receive button payloads. Failure alerts to personal Slack DM. Run report (entities collected/scored/cost) appended to each digest.

### feedback-loop
- **Status:** pending
- **Estimated Hours:** ~6h
- **Dependencies:** [digest-delivery]
- **Summary:** Feedback written to SQLite `feedback` table; thumbs-down patterns become negative few-shot examples in the scoring prompt; recurring exclusion patterns trigger a human-confirm step before appending to thesis YAML. Precision metric computed weekly and shown as a footer line in each digest.

## Epic Dependencies

```
Wave 0:
    foundation ──────────────────────────────────────────────► collectors

Wave 1:
    collectors ──────────────────────────────────────────────► enrichment

Wave 2:
    enrichment ──────────────────────────────────────────────► digest-delivery

Wave 3:
    digest-delivery ─────────────────────────────────────────► feedback-loop

Wave 4:
    feedback-loop  (terminal)
```

## Dispatch Strategy

**Wave 0:** foundation — zero dependencies, start immediately
**Wave 1:** collectors — start after foundation; collectors 3–5 can be parallelised once collector 1 validates the DB schema
**Wave 2:** enrichment — start after all collectors are wired; dedupe must precede scoring
**Wave 3:** digest-delivery — start after enrichment produces scored candidates; Slack + email can be built in parallel
**Wave 4:** feedback-loop — start after digest buttons are live and receiving payloads

## Success Criteria

- [ ] Pipeline runs end-to-end and `v0.1` commit is tagged (Day 5)
- [ ] All 5 collectors writing to SQLite with no silent failures
- [ ] LLM memo cites evidence URL for every claim; zero uncited claims in 3 consecutive runs
- [ ] Slack digest delivered at 07:30 UTC for 14 consecutive days
- [ ] 👍/👎 button payloads received and written to feedback table
- [ ] Precision metric visible in digest footer and trending upward by Day 21
- [ ] `v1.0` tagged with metrics locked (Days live, entities scanned, cost/day, users)

## Estimated Effort

| Epic | Estimated Hours | Wave | Dependencies |
|------|----------------|------|-------------|
| foundation | ~6h | 0 | none |
| collectors | ~10h | 1 | foundation |
| enrichment | ~8h | 2 | collectors |
| digest-delivery | ~8h | 3 | enrichment |
| feedback-loop | ~6h | 4 | digest-delivery |
| **Total** | **~38h** | **5 waves** | |

**Critical Path:** foundation → collectors → enrichment → digest-delivery → feedback-loop (~38h sequential)
**With parallelism:** collectors 3–5 run concurrently (~6h savings); Slack + email within digest-delivery parallel (~2h savings). Realistic elapsed: ~30h across 4 weeks at 2.5–4h/day.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| EU location normalisation misses | High | Medium | Write lookup table on Day 3; accept ~20% miss rate; log misses for manual review |
| LLM scores poor quality early | High | Low | Precision trend is the story, not the absolute number; baseline logged Day 7 |
| Feedback endpoint downtime | Medium | High | Render health checks + failure alert to personal Slack DM |
| Rate limits on data sources | Medium | Medium | All sources are official free APIs/RSS; add backoff + retry Day 12 |
| Scope creep into Week 1 | High | High | Exit criteria are the spec; anything else goes to README roadmap |
