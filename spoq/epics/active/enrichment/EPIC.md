# Epic: Enrichment

## Overview

Takes raw signals from SQLite, deduplicates entities across sources, scores them with the LLM against the thesis, and produces a ranked candidate list ready for the digest. This is the anti-hallucination core: every claim in a scoring memo must map to a cited evidence URL.

## Architecture

```
raw_signals table
       │
       ▼
┌──────────────┐     ┌──────────────────────────────────────────┐
│  dedupe.py   │────►│  scorer.py                               │
│  rapidfuzz   │     │  thesis injected + cite-or-omit rule     │
│  ~90% thresh │     │  strict JSON output + evidence_urls[]    │
└──────────────┘     └───────────────────┬──────────────────────┘
                                         │
                                         ▼
                                  scores table → ranker.py → top N
```

## Components

### 1. Deduplicator (`enrich/dedupe.py`)
- Fuzzy-match entities across sources on name + domain + founder name
- rapidfuzz, threshold ~90
- Writes/updates `companies` table

### 2. Scorer (`enrich/scorer.py`)
- Builds scoring prompt: thesis YAML + candidate signals + 2 few-shot examples
- Calls LLMClient.complete() with strict JSON schema
- Validates: every claim in memo must have a URL in evidence_urls; if not, strips the claim
- Logs token cost per entity

### 3. Ranker (`enrich/ranker.py`)
- Reads today's scores from SQLite
- Returns top N sorted by score desc, filtered by min confidence threshold

## Success Criteria

- [ ] `python -m enrich.dedupe` merges 2 test entities with 90%+ name similarity into one company record
- [ ] `python -m enrich.scorer` produces valid JSON with score 0-100 and evidence_urls for a test entity
- [ ] Zero uncited claims in 3 consecutive scoring runs (memo stripped of any claim lacking evidence_url)
- [ ] Token cost logged per entity; total run cost printed at end
- [ ] ranker.py returns top 5 for a given date

## Task Dependencies

```
Wave 0:
    01-dedupe

Wave 1 (after dedupe):
    02-scoring-prompt
    03-scorer

Wave 2:
    04-ranker
```

## Estimated Effort

| Wave | Tasks | Duration |
|------|-------|----------|
| 0 | 1 | ~2h |
| 1 | 2 | ~4h |
| 2 | 1 | ~1h |
| **Total** | **4** | **~8h** |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM returns malformed JSON | Medium | Medium | json.loads with try/except; retry once with stricter prompt |
| Dedupe false positives (two different companies merged) | Medium | Low | Log all merges; set threshold conservatively at 92 initially |
| High token cost per entity | Low | Low | Haiku is cheap; log cost/entity; cap memo at 150 tokens |
