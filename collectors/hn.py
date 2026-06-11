import os
import sys
import time
from datetime import datetime, timezone, timedelta

import httpx

from store import Store
from collectors.eu_locations import is_eu_location

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"

EU_TLDS = {".co.uk", ".de", ".fr", ".nl", ".se", ".fi", ".ie", ".no", ".dk",
           ".es", ".it", ".pl", ".pt", ".be", ".at", ".ch", ".cz", ".ro",
           ".hu", ".gr", ".hr", ".sk", ".si", ".ee", ".lv", ".lt", ".lu"}


def _has_eu_tld(url: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    return any(url_lower.endswith(tld) or f"{tld}/" in url_lower for tld in EU_TLDS)


def _is_eu_posting_time(ts: int) -> bool:
    """Heuristic: posted between 07:00-12:00 UTC suggests EU morning."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return 7 <= dt.hour < 12


def _fetch_page(params: dict) -> dict:
    for attempt in range(3):
        try:
            r = httpx.get(ALGOLIA_URL, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}


def collect(days_back: int = 7) -> dict:
    store = Store()
    store.init_db()
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())
    start = time.time()
    fetched = 0
    written = 0
    errors = []

    params = {
        "query": "Show HN",
        "tags": "story",
        "numericFilters": f"created_at_i>{since_ts}",
        "hitsPerPage": 100,
        "page": 0,
    }

    while True:
        try:
            data = _fetch_page(params)
        except Exception as e:
            errors.append(f"HN page {params['page']}: {e}")
            break

        hits = data.get("hits", [])
        if not hits:
            break

        for hit in hits:
            fetched += 1
            title = hit.get("title", "")
            url = hit.get("url", "")
            ts = hit.get("created_at_i", 0)

            if not title.startswith("Show HN:"):
                continue

            # EU heuristics — any one is enough
            eu_signals = [
                _has_eu_tld(url),
                _is_eu_posting_time(ts),
                is_eu_location(hit.get("author", "")),
            ]
            if not any(eu_signals):
                continue

            entity_key = f"news.ycombinator.com/item?id={hit.get('objectID')}"
            store.insert_signal("hacker_news", entity_key, {
                **hit,
                "eu_tld": _has_eu_tld(url),
                "eu_posting_time": _is_eu_posting_time(ts),
            })
            written += 1

        nb_pages = data.get("nbPages", 1)
        params["page"] += 1
        if params["page"] >= nb_pages:
            break
        time.sleep(0.3)

    duration = time.time() - start
    report = {
        "source": "hacker_news",
        "records_fetched": fetched,
        "records_written": written,
        "duration_s": round(duration, 1),
        "errors": errors,
    }
    print(f"[hn] fetched={fetched} written={written} duration={duration:.1f}s errors={len(errors)}")
    return report


if __name__ == "__main__":
    collect()
