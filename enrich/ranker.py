from datetime import date
from store import Store


def get_top_n(n: int = 5, run_date: date | None = None) -> list[dict]:
    """
    Return top N scored candidates for a given date, sorted by score descending.
    Falls back to returning fewer than N if not enough candidates exist.
    """
    run_date = run_date or date.today()
    store = Store()

    rows = store.conn.execute(
        """
        SELECT
            s.entity_key,
            s.score,
            s.stage_guess,
            s.one_line,
            s.memo,
            s.confidence,
            s.evidence_urls,
            s.cost_gbp,
            s.scored_at,
            c.name,
            c.domain,
            c.sources,
            c.founder_names
        FROM scores s
        LEFT JOIN companies c ON s.entity_key = c.entity_key
        WHERE DATE(s.scored_at) = ?
        ORDER BY s.score DESC
        """,
        (run_date.isoformat(),),
    ).fetchall()

    candidates = [dict(r) for r in rows]

    # Prefer high/medium confidence if we have enough candidates
    if len(candidates) > n:
        high_conf = [c for c in candidates if c.get("confidence") != "low"]
        if len(high_conf) >= n:
            candidates = high_conf

    return candidates[:n]


def get_run_stats(run_date: date | None = None) -> dict:
    """Return aggregate stats for a run date (used in digest footer)."""
    run_date = run_date or date.today()
    store = Store()

    scored = store.conn.execute(
        "SELECT COUNT(*), SUM(cost_gbp) FROM scores WHERE DATE(scored_at) = ?",
        (run_date.isoformat(),),
    ).fetchone()

    collected = store.conn.execute(
        "SELECT COUNT(DISTINCT source), COUNT(*) FROM raw_signals WHERE DATE(collected_at) = ?",
        (run_date.isoformat(),),
    ).fetchone()

    feedback = store.conn.execute(
        """
        SELECT
            SUM(CASE WHEN signal='up' THEN 1 ELSE 0 END) as ups,
            COUNT(*) as total
        FROM feedback
        WHERE DATE(ts) >= DATE('now', '-7 days')
        """
    ).fetchone()

    precision = None
    if feedback and feedback["total"] and feedback["total"] > 0:
        precision = round(feedback["ups"] / feedback["total"], 2)

    return {
        "entities_scored": scored[0] or 0,
        "cost_gbp": round(scored[1] or 0.0, 4),
        "sources_active": collected[0] or 0,
        "signals_collected": collected[1] or 0,
        "precision_7d": precision,
        "run_date": run_date.isoformat(),
    }
