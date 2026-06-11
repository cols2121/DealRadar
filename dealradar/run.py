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


def run() -> None:
    start = time.time()
    reports = []
    errors = []

    # --- Collect ---
    print("[run] Starting collectors...")
    collectors = []
    try:
        from collectors.ch import collect as ch_collect
        collectors.append(("companies_house", ch_collect))
    except Exception as e:
        errors.append(f"ch import: {e}")

    try:
        from collectors.gh import collect as gh_collect
        collectors.append(("github", gh_collect))
    except Exception as e:
        errors.append(f"gh import: {e}")

    try:
        from collectors.ph import collect as ph_collect
        collectors.append(("product_hunt", ph_collect))
    except Exception as e:
        errors.append(f"ph import: {e}")

    try:
        from collectors.hn import collect as hn_collect
        collectors.append(("hacker_news", hn_collect))
    except Exception as e:
        errors.append(f"hn import: {e}")

    try:
        from collectors.rss import collect as rss_collect
        collectors.append(("rss", rss_collect))
    except Exception as e:
        errors.append(f"rss import: {e}")

    total_written = 0
    for name, collect_fn in collectors:
        try:
            report = collect_fn()
            reports.append(report)
            total_written += report.get("records_written", 0)
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"[run] ERROR in {name}: {e}", file=sys.stderr)

    print(f"[run] Collection complete: {total_written} entities written across {len(reports)} sources")

    if not total_written:
        print("[run] No entities collected — skipping enrichment and digest")
        return

    # --- Enrichment placeholder (implemented in enrichment epic) ---
    print("[run] Enrichment: skipped (pending enrichment epic)")

    # --- Summary ---
    duration = time.time() - start
    sources_ok = len(reports)
    sources_fail = len(errors)
    print(f"[run] Done in {duration:.1f}s | sources ok={sources_ok} fail={sources_fail}")

    if errors:
        alert = f"⚠️ DealRadar run completed with {len(errors)} error(s): {'; '.join(errors[:3])}"
        _send_alert(alert)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        _send_alert(f"🚨 DealRadar run CRASHED: {e}")
        raise
