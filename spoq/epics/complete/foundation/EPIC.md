# Epic: Foundation

## Overview

Bootstraps DealRadar from an empty directory to a runnable skeleton: public repo with README and DECISIONS.md, SQLite schema, typed thesis config, LLM client abstraction, GitHub Actions cron, and smoke-test scripts validating all external API credentials. Every downstream epic depends on the contracts defined here.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  config/        │────►│  store.py        │────►│  llm_client.py   │
│  thesis.yaml    │     │  (SQLite schema) │     │  (30-line wrap)  │
│  (Pydantic)     │     └──────────────────┘     └──────────────────┘
└─────────────────┘
        │
        ▼
┌─────────────────┐     ┌──────────────────┐
│  .github/       │     │  smoke_tests/    │
│  workflows/     │     │  (API verify)    │
│  cron.yml       │     └──────────────────┘
└─────────────────┘
```

## Components

### 1. Repo scaffold & public docs
- README with one-sentence pitch, ASCII architecture diagram, "Status: building in public" line
- DECISIONS.md with first 3 entries (SQLite rationale, cite-or-omit rationale, Companies House first)
- `.gitignore` excluding `data/`, `.env`, `__pycache__`
- `pyproject.toml` or `requirements.txt` with pinned deps

### 2. SQLite schema
- `schema.sql` committed; `data/dealradar.db` gitignored
- Tables: `raw_signals`, `companies`, `scores`, `feedback`
- `store.py`: thin wrapper with `insert_signal()`, `upsert_company()`, `insert_score()`, `insert_feedback()`

### 3. Thesis config
- `config/thesis.yaml` matching the spec
- `config/thesis_model.py`: Pydantic model validating and loading the YAML; single import used by all downstream components

### 4. LLM client abstraction
- `enrich/llm_client.py`: `LLMClient` class, ~30 lines, wraps Anthropic SDK
- `complete(prompt, system, max_tokens) -> str`
- Provider swappable via env var `LLM_PROVIDER` (default: anthropic)
- Logs token usage per call to stdout

### 5. GitHub Actions cron
- `.github/workflows/daily.yml`: runs at 07:30 UTC, calls `python -m dealradar.run`
- Secrets: `ANTHROPIC_API_KEY`, `CH_API_KEY`, `GITHUB_TOKEN`, `SLACK_WEBHOOK_URL`

### 6. Smoke tests
- `scripts/smoke_test.py`: verifies Companies House API, GitHub API, Anthropic API each return 200/valid in <5s
- Exits non-zero on any failure

## Success Criteria

- [ ] `python scripts/smoke_test.py` exits 0 with all three APIs green
- [ ] `python -c "from config.thesis_model import load_thesis; load_thesis()"` runs without error
- [ ] `python -c "from store import Store; s = Store(); s.init_db()"` creates `data/dealradar.db`
- [ ] `python -c "from enrich.llm_client import LLMClient; LLMClient().complete('ping', max_tokens=5)"` returns a string
- [ ] `.github/workflows/daily.yml` passes `act` dry-run or GitHub Actions lint
- [ ] Public repo exists with README and DECISIONS.md committed

## Task Dependencies

```
Wave 0 (parallel, no deps):
    01-repo-scaffold
    02-sqlite-schema
    03-thesis-config

Wave 1 (after Wave 0):
    04-llm-client       (needs 03-thesis-config for provider env var pattern)
    05-github-actions   (needs 01-repo-scaffold for repo structure)

Wave 2 (integration):
    06-smoke-tests      (needs 02, 03, 04 all wired)
```

## Dispatch Strategy

**Wave 0 (Parallel):** Tasks 01, 02, 03 — pure scaffolding, no cross-dependencies
**Wave 1 (Parallel):** Tasks 04, 05 — each depends on one Wave 0 task only
**Wave 2 (Sequential):** Task 06 — integration verification across all components

**Critical Path:** 01 → 05 → 06 (~3h)

## Estimated Effort

| Wave | Tasks | Parallel Agents | Duration |
|------|-------|-----------------|----------|
| 0 | 3 | 3 | ~1.5h |
| 1 | 2 | 2 | ~1.5h |
| 2 | 1 | 1 | ~1h |
| **Total** | **6** | **Max 3** | **~6h** |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Anthropic SDK version conflict | Low | Medium | Pin `anthropic>=0.25` in requirements |
| GitHub Actions secrets not set | Medium | Low | Smoke test catches this; doc in README |
| SQLite WAL mode needed for concurrent writes | Low | Low | Enable WAL in `Store.__init__` |

## Prerequisites

- [ ] Python 3.12 installed
- [ ] `pipx install spoq` done (already complete)
- [ ] Companies House API key obtained (free registration at developer.companieshouse.gov.uk)
- [ ] GitHub personal access token with `read:user`, `public_repo` scopes
- [ ] Anthropic API key

## Notes

Boring stack is intentional and should be stated as such in DECISIONS.md. The LLM client abstraction exists so the demo can say "provider-agnostic" without the code being complex. SQLite single-file = zero ops = the cron job is the only moving part visible in the public repo.
