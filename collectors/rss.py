import os
import sys
import time
import json
from datetime import datetime, timezone, timedelta

import feedparser

from store import Store
from enrich.llm_client import LLMClient

FEEDS = [
    ("sifted", "https://sifted.eu/feed"),
    ("tech_eu", "https://tech.eu/feed"),
    ("eu_startups", "https://www.eu-startups.com/feed"),
    ("techcrunch_eu", "https://techcrunch.com/tag/europe/feed"),
]

EXTRACTION_PROMPT = """You are extracting startup signals from a news article about the European tech ecosystem.

Article title: {title}
Article summary: {summary}
Article URL: {url}

If this article mentions a company that appears to be pre-seed or newly formed (raising under £2m, recently incorporated, very early stage, or just launched), extract:
- name: the company name
- stage_evidence: one sentence quoting evidence from the article that suggests pre-seed stage
- url: the article URL

If no such pre-seed/newly-formed company is mentioned, return null.

Respond with valid JSON only. Examples:
{"name": "Acme AI", "stage_evidence": "The London-based startup just raised a £500k pre-seed round.", "url": "https://..."}
null"""


def _extract_company(title: str, summary: str, url: str, client: LLMClient) -> dict | None:
    prompt = EXTRACTION_PROMPT.format(
        title=title,
        summary=summary[:500] if summary else "",
        url=url,
    )
    try:
        raw = client.complete(prompt, max_tokens=200)
        raw = raw.strip()
        if raw.lower() == "null" or not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def collect(days_back: int = 7) -> dict:
    store = Store()
    store.init_db()
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    start = time.time()
    fetched = 0
    written = 0
    errors = []

    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    try:
        client = LLMClient(provider=provider)
    except ValueError as e:
        errors.append(f"LLM client init failed: {e}")
        client = LLMClient(provider="mock")

    for feed_name, feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Parse published date
                published = entry.get("published_parsed")
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if pub_dt < since:
                        continue

                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                url = entry.get("link", "")
                fetched += 1

                extracted = _extract_company(title, summary, url, client)
                if not extracted:
                    continue

                entity_key = url
                store.insert_signal("rss", entity_key, {
                    "feed": feed_name,
                    "title": title,
                    "url": url,
                    "extracted": extracted,
                    "published": entry.get("published", ""),
                })
                written += 1

        except Exception as e:
            errors.append(f"Feed {feed_name}: {e}")
            continue

    duration = time.time() - start
    report = {
        "source": "rss",
        "records_fetched": fetched,
        "records_written": written,
        "duration_s": round(duration, 1),
        "errors": errors,
    }
    print(f"[rss] fetched={fetched} written={written} duration={duration:.1f}s errors={len(errors)}")
    return report


if __name__ == "__main__":
    collect()
