# DealRadar

A daily agent that scans public signals for newly-forming European startups, scores them against a pre-seed thesis, and delivers a 5-company digest to Slack/email with one-click feedback.

**Status:** Building in public — started 2026-06-11

## Pipeline

```
[Collectors] → [Dedupe + Entity Store] → [LLM Enrichment + Scoring] → [Ranker] → [Digest] → [Feedback Loop]
```

## Data sources

| Source | Access method | Week added |
| --- | --- | --- |
| Companies House | Free REST API (no rate limits) | Week 1 |
| GitHub | REST/GraphQL API | Week 2 |
| Product Hunt | Public GraphQL API | Week 2 |
| Hacker News | Firebase API + Algolia search | Week 3 |
| RSS | feedparser over curated feeds | Week 3 |

## Run it yourself

```bash
# 1. Clone the repo
git clone https://github.com/<you>/dealradar.git
cd dealradar

# 2. Copy the example env and fill in your keys
cp .env.example .env

# 3. Install dependencies
pip install -e .

# 4. Run the smoke test
pytest -q

# 5. Trigger the pipeline
python -m scripts.run_pipeline
```

## Deploy the feedback endpoint

The 👍/👎 buttons require a live HTTPS endpoint. Deploy to Render free tier in ~5 minutes:

1. Push this repo to GitHub (public or private)
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Render auto-detects `render.yaml` — click **Deploy**
4. Copy the service URL (e.g. `https://dealradar-feedback.onrender.com`)
5. In your Slack app settings → **Interactivity & Shortcuts** → set Request URL to `<your-render-url>/slack/actions`
6. Add `FEEDBACK_ENDPOINT=<your-render-url>` to GitHub Actions secrets

The `/health` endpoint confirms the service is running.

## Out of scope (v1)

- LinkedIn scraping (ToS risk)
- Paid data providers (Dealroom / PitchBook)
- CRM integration
- Multi-tenant auth

## What I'd build next inside a fund

If I were in residence at Playfair, DealRadar is the wedge — here is where I'd take it next:

- **Inbound pitch triage.** Every founder pitch that hits the fund inbox gets an automated first-pass memo — thesis fit, team signal, market framing, and an explicit cite-or-omit evidence trail — so partners spend their attention on the shortlist rather than the slush pile.
- **Portfolio-support automations.** Standing agents that watch each portfolio company's public footprint (hiring, shipping cadence, press, churn signals) and surface intros, follow-on timing, and reporting prep automatically.
- **Fourth-fund data room tooling.** LP-grade reporting and diligence automation — pulling the fund's own track record, portfolio metrics, and pipeline analytics into a continuously-updated data room ready for the next raise.
