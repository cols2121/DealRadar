# Epic: Collectors

## Overview

Implements all five data collectors that feed raw signals into SQLite. Each collector is an independent module writing to the `raw_signals` table. Priority order matches the build doc: Companies House and GitHub in Week 1; Product Hunt, Hacker News, and RSS in Week 2. Includes the EU location normalisation lookup table shared across collectors.

## Architecture

```
┌──────────────────┐
│  eu_locations.py │  shared lookup (countries + major cities)
└────────┬─────────┘
         │
    ┌────┴─────────────────────────────────────────────────┐
    ▼            ▼            ▼            ▼               ▼
┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│  ch.py │ │  gh.py  │ │  ph.py  │ │  hn.py   │ │  rss.py  │
│Cos Hse │ │ GitHub  │ │ProdHunt │ │Hckr News │ │   RSS    │
└────┬───┘ └────┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘
     └──────────┴───────────┴───────────┴─────────────┘
                                    │
                              store.insert_signal()
```

## Components

### 1. EU location normaliser (`collectors/eu_locations.py`)
- Country name list + major city list for regex normalisation
- `is_eu_location(text: str) -> bool` — accepts ~80% coverage, logs misses

### 2. Companies House collector (`collectors/ch.py`)
- Incorporations from last 7 days filtered by tech SIC codes
- Director history check for serial founders
- Output: `entity_key = CH company number`

### 3. GitHub collector (`collectors/gh.py`)
- Repos created <90 days ago with >N stars/week velocity, EU owner location
- New orgs with ex-scaleup engineer bios (Monzo, Revolut, Wise, Spotify, Delivery Hero, etc.)
- Output: `entity_key = github.com/<org>`

### 4. Product Hunt collector (`collectors/ph.py`)
- GraphQL: launches from last 7 days with EU maker locations
- Output: `entity_key = producthunt.com/posts/<slug>`

### 5. Hacker News collector (`collectors/hn.py`)
- Algolia API: Show HN posts + "we're building" comments, EU heuristics
- Output: `entity_key = news.ycombinator.com/item?id=<id>`

### 6. RSS collector (`collectors/rss.py`)
- Sifted, Tech.eu, EU-Startups, TechCrunch Europe feeds
- LLM extraction pass: "does this article mention a pre-seed/newly formed company?"
- Output: `entity_key = article URL`

## Success Criteria

- [ ] `python -m collectors.ch` writes ≥1 raw_signal row to SQLite without error
- [ ] `python -m collectors.gh` writes ≥1 raw_signal row to SQLite without error
- [ ] All 5 collectors run via `python -m dealradar.run --collect-only` without crashing
- [ ] EU location normaliser correctly classifies "London", "UK", "🇬🇧", "Berlin", "Paris" as EU
- [ ] Each collector has retry-with-backoff on HTTP errors (httpx + tenacity or manual)
- [ ] Run report logs: source name, records fetched, records written, duration

## Task Dependencies

```
Wave 0 (parallel, no deps):
    01-eu-locations
    02-ch-collector
    03-gh-collector

Wave 1 (after eu-locations):
    04-ph-collector     (needs eu-locations)
    05-hn-collector     (needs eu-locations)
    06-rss-collector    (needs eu-locations + llm_client)

Wave 2:
    07-collector-hardening   (retries, run reports, failure alerts)
```

## Dispatch Strategy

**Wave 0:** eu-locations and the two highest-priority collectors built in parallel
**Wave 1:** remaining collectors, all use eu-locations
**Wave 2:** hardening across all collectors (retries, logging)

**Critical Path:** 01 → 06 → 07 (~5h)

## Estimated Effort

| Wave | Tasks | Parallel Agents | Duration |
|------|-------|-----------------|----------|
| 0 | 3 | 3 | ~3h |
| 1 | 3 | 3 | ~3h |
| 2 | 1 | 1 | ~2h |
| **Total** | **7** | **Max 3** | **~10h** |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub location free-text normalisation misses | High | Medium | Log all misses; accept ~20%; improve lookup post-v0.1 |
| Companies House API rate limit | Low | Low | Free tier is generous; add 0.5s delay between pages |
| Product Hunt GraphQL auth changes | Medium | Medium | Wrap in try/except; collector failure is non-fatal |
| RSS feeds going down | Low | Low | Each feed in try/except; run report shows which succeeded |

## Prerequisites

- [ ] foundation epic complete (store.py, schema.sql, eu credentials loaded)
- [ ] Companies House API key in .env
- [ ] GitHub token in .env
