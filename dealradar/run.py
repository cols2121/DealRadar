"""Main pipeline entry point: collect → dedupe → score → rank → send."""
import os
import sys
import time
from datetime import date


def _send_alert(message: str) -> None:
    webhook = os.environ.get("SLACK_ALERT_WEBHOOK_URL")
    if not webhook:
        return
    try:
        import httpx
        httpx.post(webhook, json={"text": message}, timeout=5)
    except Exception:
        pass


def _run_collectors() -> tuple[int, list[dict]]:
    """Run all collectors. Returns (total_written, reports)."""
    from collectors.ch import collect as ch_collect
    from collectors.gh import collect as gh_collect
    from collectors.ph import collect as ph_collect
    from collectors.hn import collect as hn_collect
    from collectors.rss import collect as rss_collect

    collectors = [
        ("companies_house", ch_collect),
        ("github", gh_collect),
        ("product_hunt", ph_collect),
        ("hacker_news", hn_collect),
        ("rss", rss_collect),
    ]

    reports = []
    total_written = 0
    for name, fn in collectors:
        try:
            report = fn()
            reports.append(report)
            total_written += report.get("records_written", 0)
            print(f"[run] {name}: {report.get('records_written', 0)} written")
        except Exception as e:
            print(f"[run] ERROR {name}: {e}", file=sys.stderr)
            reports.append({"source": name, "records_written": 0, "errors": [str(e)]})

    return total_written, reports


def _run_enrichment() -> list[dict]:
    """Deduplicate today's signals and score each entity."""
    from enrich.dedupe import dedupe_from_db
    from enrich.scorer import score_and_store, ScoringError

    entities = dedupe_from_db()
    print(f"[run] {len(entities)} unique entities after dedupe")

    scored = 0
    for entity in entities:
        entity_key = entity.get("entity_key", "")
        signals = entity.get("signals", [])
        try:
            score_and_store(entity_key, signals)
            scored += 1
        except ScoringError as e:
            print(f"[run] Scoring failed for {entity_key}: {e}", file=sys.stderr)

    print(f"[run] Scored {scored}/{len(entities)} entities")
    return entities


def _run_digest(run_stats: dict) -> None:
    """Rank top candidates and send digest."""
    from enrich.ranker import get_top_n
    from digest.slack_sender import send_digest, send_alert as slack_alert

    candidates = get_top_n(n=5)
    if not candidates:
        print("[run] No candidates to send — skipping digest")
        return

    print(f"[run] Sending digest with {len(candidates)} candidates")
    try:
        send_digest(candidates, run_stats)
        print("[run] Slack digest sent")
    except Exception as e:
        msg = f"⚠️ DealRadar digest send failed: {e}"
        print(msg, file=sys.stderr)
        slack_alert(msg)


def run() -> None:
    wall_start = time.time()
    print(f"[run] Starting DealRadar pipeline — {date.today().isoformat()}")

    try:
        # 1. Collect
        total_written, collector_reports = _run_collectors()

        if not total_written:
            print("[run] No new signals collected — exiting early")
            return

        # 2. Enrich + score
        _run_enrichment()

        # 3. Build run stats
        from enrich.ranker import get_run_stats
        run_stats = get_run_stats()

        # 4. Send digest
        _run_digest(run_stats)

        duration = time.time() - wall_start
        sources_ok = sum(1 for r in collector_reports if not r.get("errors"))
        sources_fail = len(collector_reports) - sources_ok
        print(
            f"[run] Complete in {duration:.1f}s | "
            f"sources ok={sources_ok} fail={sources_fail} | "
            f"cost=£{run_stats.get('cost_gbp', 0):.4f}"
        )

    except Exception as e:
        _send_alert(f"🚨 DealRadar run CRASHED: {e}")
        print(f"[run] FATAL: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    run()
