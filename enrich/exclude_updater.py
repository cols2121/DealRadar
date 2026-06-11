"""
Analyses thumbs-down feedback to surface recurring keywords in LLM memos,
then proposes additions to config/thesis.yaml's exclude list.
Requires explicit human confirmation before writing changes.
"""
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from store import Store

_STOPWORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would could should may might shall "
    "this that these those it its we our us they their them he she him her "
    "company startup uk us eu based founded team product platform".split()
)

_MIN_KEYWORD_LENGTH = 4
_TOP_N = 10
_MIN_OCCURRENCES = 2


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z]{%d,}" % _MIN_KEYWORD_LENGTH, text.lower())
    return [w for w in words if w not in _STOPWORDS]


def detect_exclude_patterns(min_votes: int = 3) -> list[dict]:
    """
    Find entities with >= min_votes thumbs-down and extract common keywords
    from their LLM memos. Returns proposed exclusion patterns with counts.
    """
    store = Store()

    # Entities with enough thumbs-down votes
    rows = store.conn.execute(
        """
        SELECT f.entity_key, COUNT(*) as downs
        FROM feedback f
        WHERE f.signal = 'down'
        GROUP BY f.entity_key
        HAVING downs >= ?
        """,
        (min_votes,),
    ).fetchall()

    if not rows:
        return []

    entity_keys = [r["entity_key"] for r in rows]

    # Fetch their LLM memos from scores table
    placeholders = ",".join("?" * len(entity_keys))
    memos = store.conn.execute(
        f"SELECT memo FROM scores WHERE entity_key IN ({placeholders})",
        entity_keys,
    ).fetchall()

    all_keywords: list[str] = []
    for memo_row in memos:
        if memo_row["memo"]:
            all_keywords.extend(_extract_keywords(memo_row["memo"]))

    counts = Counter(all_keywords)
    proposals = [
        {"keyword": kw, "occurrences": cnt}
        for kw, cnt in counts.most_common(_TOP_N)
        if cnt >= _MIN_OCCURRENCES
    ]
    return proposals


def propose_and_confirm(proposals: list[dict], thesis_path: str = "config/thesis.yaml") -> bool:
    """
    Print proposed exclusions and prompt user to confirm before writing.
    Returns True if thesis.yaml was updated.
    """
    if not proposals:
        print("No exclusion patterns detected from thumbs-down feedback.")
        return False

    print("\n=== Proposed thesis.yaml exclude additions ===")
    for p in proposals:
        print(f"  {p['keyword']!r:30s} ({p['occurrences']} thumbs-down mentions)")

    answer = input("\nAdd these to thesis.yaml exclude list? [y/N] ").strip().lower()
    if answer != "y":
        print("Skipped.")
        return False

    path = Path(thesis_path)
    config = yaml.safe_load(path.read_text())
    existing = set(config.get("exclude", []))
    new_terms = [p["keyword"] for p in proposals if p["keyword"] not in existing]

    if not new_terms:
        print("All proposed terms already in exclude list.")
        return False

    config.setdefault("exclude", []).extend(new_terms)
    path.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True))
    print(f"Added {len(new_terms)} term(s) to {thesis_path}: {new_terms}")
    return True


if __name__ == "__main__":
    proposals = detect_exclude_patterns()
    updated = propose_and_confirm(proposals)
    sys.exit(0 if updated or not proposals else 1)
