"""
Updates enrich/prompts/score_fewshot.txt with user-validated examples
from the feedback table. Run after each digest cycle.
"""
from pathlib import Path

from store import Store

FEWSHOT_PATH = Path("enrich/prompts/score_fewshot.txt")
THRESHOLD = 3  # min votes to promote to few-shot


def update_fewshots() -> int:
    """
    Reads feedback table, finds entities with >= THRESHOLD votes in one direction,
    and appends new few-shot examples to score_fewshot.txt.
    Returns number of new examples added.
    """
    store = Store()
    rows = store.conn.execute(
        """
        SELECT entity_key, signal, COUNT(*) as n
        FROM feedback
        GROUP BY entity_key, signal
        HAVING n >= ?
        ORDER BY n DESC
        """,
        (THRESHOLD,),
    ).fetchall()

    if not rows:
        return 0

    existing = FEWSHOT_PATH.read_text(encoding="utf-8")
    additions = []

    for row in rows:
        entity_key = row["entity_key"]
        signal = row["signal"]
        vote_count = row["n"]

        # Idempotent — skip if already in fewshot file
        marker = f"<!-- fewshot:{entity_key}:{signal} -->"
        if marker in existing:
            continue

        # Look up the most recent score for this entity
        score_row = store.conn.execute(
            """
            SELECT score, one_line, memo, confidence, evidence_urls, scored_at
            FROM scores
            WHERE entity_key = ?
            ORDER BY scored_at DESC
            LIMIT 1
            """,
            (entity_key,),
        ).fetchone()

        if not score_row:
            continue

        label = "POSITIVE EXAMPLE (user-validated)" if signal == "up" else "NEGATIVE EXAMPLE (user-rejected)"
        additions.append(
            f"\n\n---\n\n"
            f"## {label}\n"
            f"{marker}\n"
            f"Entity: {entity_key}\n"
            f"User signal: {signal} ({vote_count} votes)\n"
            f"Score given: {score_row['score']}\n"
            f"One-line: {score_row['one_line']}\n"
            f"Confidence: {score_row['confidence']}\n"
            f"Memo: {score_row['memo']}\n"
            f"Evidence: {score_row['evidence_urls']}\n"
            f"\nExpected output:\n"
            f'{{"score": {score_row["score"]}, "confidence": "{score_row["confidence"]}"}}'
        )

    if additions:
        FEWSHOT_PATH.write_text(
            existing + "".join(additions), encoding="utf-8"
        )
        print(f"[fewshot] Added {len(additions)} new examples to score_fewshot.txt")

    return len(additions)
