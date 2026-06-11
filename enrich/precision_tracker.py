"""
Computes precision metrics from user feedback and stores weekly snapshots.
Precision = thumbs-up / total rated, over a 7-day rolling window.
"""
from datetime import datetime, timezone
from store import Store


def get_precision_summary() -> dict | None:
    """
    Returns precision stats for this week vs last week.
    Returns None if fewer than 3 rated entities this week (insufficient data).
    """
    store = Store()

    def precision_for_window(days_offset: int = 0) -> tuple[float | None, int]:
        """Compute precision for a 7-day window ending days_offset days ago."""
        rows = store.conn.execute(
            """
            SELECT signal FROM feedback
            WHERE ts >= DATETIME('now', ? || ' days')
              AND ts <  DATETIME('now', ? || ' days')
            """,
            (str(-(7 + days_offset)), str(-days_offset)),
        ).fetchall()
        n = len(rows)
        if n < 3:
            return None, n
        ups = sum(1 for r in rows if r["signal"] == "up")
        return round(ups / n, 2), n

    this_precision, this_n = precision_for_window(0)
    last_precision, _ = precision_for_window(7)

    if this_precision is None:
        return None

    if last_precision is None:
        trend = "→"
    elif this_precision > last_precision:
        trend = "↑"
    elif this_precision < last_precision:
        trend = "↓"
    else:
        trend = "→"

    return {
        "this_week": this_precision,
        "last_week": last_precision,
        "rated_n": this_n,
        "trend": trend,
    }


def store_weekly_snapshot() -> None:
    """Persist current week's precision to the metrics table."""
    summary = get_precision_summary()
    if summary is None:
        return

    store = Store()
    now = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")
    store.conn.execute(
        "INSERT INTO metrics(week, precision, rated_n, ts) VALUES(?,?,?,?)",
        (week, summary["this_week"], summary["rated_n"], now.isoformat()),
    )
    store.conn.commit()
    print(f"[precision] Week {week}: {summary['this_week']:.0%} ({summary['rated_n']} rated) {summary['trend']}")


def format_for_digest(summary: dict | None) -> str:
    """Format precision summary as a short string for the digest footer."""
    if summary is None:
        return "Precision: insufficient data"
    p = f"{summary['this_week']:.0%}"
    trend = summary["trend"]
    last = f" (was {summary['last_week']:.0%})" if summary["last_week"] is not None else ""
    return f"Precision (7d): {p} {trend}{last}"
