import os
import sys
import time
from datetime import date, timedelta

import httpx

from store import Store
from collectors.eu_locations import is_eu_location

PH_URL = "https://api.producthunt.com/v2/api/graphql"

POSTS_QUERY = """
query($after: String, $postedAfter: DateTime) {
  posts(order: NEWEST, after: $after, postedAfter: $postedAfter) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        slug
        name
        tagline
        url
        votesCount
        commentsCount
        createdAt
        makers {
          name
          profileUrl
          websiteUrl
          twitterUsername
          headline
        }
      }
    }
  }
}
"""


def _gql(query: str, variables: dict | None = None) -> dict:
    token = os.environ.get("PH_TOKEN", "")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            r = httpx.post(
                PH_URL,
                json={"query": query, "variables": variables or {}},
                headers=headers,
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                raise ValueError(str(data["errors"]))
            return data.get("data", {})
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}


def _maker_is_eu(maker: dict) -> bool:
    for field in ["websiteUrl", "profileUrl", "twitterUsername", "headline"]:
        val = maker.get(field) or ""
        if is_eu_location(val):
            return True
    return False


def collect(days_back: int = 7) -> dict:
    store = Store()
    store.init_db()
    since = (date.today() - timedelta(days=days_back)).isoformat() + "T00:00:00Z"
    start = time.time()
    fetched = 0
    written = 0
    errors = []
    cursor = None
    pages = 0
    max_pages = 5

    while pages < max_pages:
        try:
            data = _gql(POSTS_QUERY, {"after": cursor, "postedAfter": since})
            posts_data = data.get("posts", {})
            edges = posts_data.get("edges", [])
        except Exception as e:
            errors.append(f"PH page {pages}: {e}")
            break

        for edge in edges:
            node = edge.get("node", {})
            fetched += 1
            makers = node.get("makers", [])
            if not any(_maker_is_eu(m) for m in makers):
                continue

            entity_key = f"producthunt.com/posts/{node.get('slug', node.get('id'))}"
            store.insert_signal("product_hunt", entity_key, node)
            written += 1

        page_info = posts_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        pages += 1
        time.sleep(0.5)

    duration = time.time() - start
    report = {
        "source": "product_hunt",
        "records_fetched": fetched,
        "records_written": written,
        "duration_s": round(duration, 1),
        "errors": errors,
    }
    print(f"[ph] fetched={fetched} written={written} duration={duration:.1f}s errors={len(errors)}")
    return report


if __name__ == "__main__":
    collect()
