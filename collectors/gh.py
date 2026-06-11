import os
import sys
import time
from datetime import date, timedelta

import httpx

from store import Store
from collectors.eu_locations import is_eu_location

GQL_URL = "https://api.github.com/graphql"
EX_SCALEUP = [
    "monzo", "revolut", "wise", "spotify", "deliveroo", "delivery hero",
    "transferwise", "babylon", "checkout.com", "starling", "freetrade",
    "funding circle", "gousto", "bulb", "octopus energy", "cazoo",
    "asos", "just eat", "skyscanner", "king", "arm",
]
MIN_VELOCITY = 2  # stars per week minimum

REPO_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: REPOSITORY, first: 50, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Repository {
        name
        nameWithOwner
        stargazerCount
        createdAt
        description
        homepageUrl
        owner {
          login
          ... on User { location bio }
          ... on Organization { location description }
        }
      }
    }
  }
}
"""


def _gql(query: str, variables: dict | None = None) -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        try:
            r = httpx.post(
                GQL_URL,
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


def _has_scaleup_bio(bio: str) -> bool:
    if not bio:
        return False
    bio_lower = bio.lower()
    return any(kw in bio_lower for kw in EX_SCALEUP)


def _star_velocity(stars: int, created_at: str) -> float:
    from datetime import datetime, timezone
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    weeks = max((now - created).days / 7, 1)
    return stars / weeks


def collect(days_back: int = 90) -> dict:
    store = Store()
    store.init_db()
    since = (date.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    start = time.time()
    fetched = 0
    written = 0
    errors = []

    if not os.environ.get("GITHUB_TOKEN"):
        print("[gh] GITHUB_TOKEN not set — skipping", file=sys.stderr)
        return {"source": "github", "records_fetched": 0, "records_written": 0,
                "duration_s": 0, "errors": ["GITHUB_TOKEN not set"]}

    # Search for recently created repos with EU owners
    search_query = f"created:>{since} stars:>5"
    cursor = None
    pages = 0
    max_pages = 10  # safety limit

    while pages < max_pages:
        try:
            data = _gql(REPO_QUERY, {"query": search_query, "cursor": cursor})
            search = data.get("search", {})
            nodes = search.get("nodes", [])
        except Exception as e:
            errors.append(f"GraphQL page {pages}: {e}")
            break

        for repo in nodes:
            fetched += 1
            owner = repo.get("owner", {})
            location = owner.get("location") or ""
            bio = owner.get("bio") or owner.get("description") or ""

            if not is_eu_location(location) and not _has_scaleup_bio(bio):
                continue

            velocity = _star_velocity(
                repo.get("stargazerCount", 0),
                repo.get("createdAt", "2000-01-01T00:00:00Z"),
            )
            if velocity < MIN_VELOCITY and not _has_scaleup_bio(bio):
                continue

            entity_key = f"github.com/{owner.get('login', 'unknown')}"
            store.insert_signal("github", entity_key, {
                **repo,
                "star_velocity": round(velocity, 2),
                "scaleup_bio": _has_scaleup_bio(bio),
            })
            written += 1

        page_info = search.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        pages += 1
        time.sleep(1)  # respect secondary rate limits

    duration = time.time() - start
    report = {
        "source": "github",
        "records_fetched": fetched,
        "records_written": written,
        "duration_s": round(duration, 1),
        "errors": errors,
    }
    print(f"[gh] fetched={fetched} written={written} duration={duration:.1f}s errors={len(errors)}")
    return report


if __name__ == "__main__":
    collect()
