import json
import os
from rapidfuzz import fuzz
from store import Store

THRESHOLD = int(os.getenv("DEDUPE_THRESHOLD", "75"))


def _name_key(signal: dict) -> str:
    """Extract best available name text for fuzzy matching."""
    raw = signal.get("raw_json") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    return (
        raw.get("company_name")
        or raw.get("name")
        or raw.get("nameWithOwner")
        or raw.get("title")
        or signal.get("entity_key", "")
    )


def dedupe(signals: list[dict]) -> list[dict]:
    """
    Group signals by entity similarity, upsert deduplicated companies into DB.
    Returns one merged dict per unique entity.
    """
    groups: list[list[dict]] = []

    for sig in signals:
        key = _name_key(sig)
        matched = None
        for group in groups:
            existing_key = _name_key(group[0])
            if existing_key and key and fuzz.token_sort_ratio(key, existing_key) >= THRESHOLD:
                matched = group
                break
        if matched is not None:
            print(f"[dedupe] Merged {key!r} into {_name_key(matched[0])!r}")
            matched.append(sig)
        else:
            groups.append([sig])

    store = Store()
    results = []
    for group in groups:
        merged = _merge_group(group)
        store.upsert_company(
            entity_key=merged["entity_key"],
            name=merged.get("name"),
            domain=merged.get("domain"),
            founder_names=json.dumps(merged.get("founder_names", [])),
            sources=json.dumps(merged.get("sources", [])),
        )
        results.append(merged)

    return results


def _merge_group(signals: list[dict]) -> dict:
    primary = signals[0]
    raw = primary.get("raw_json") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}

    sources = list({s.get("source", "unknown") for s in signals})
    entity_keys = [s.get("entity_key", "") for s in signals]
    entity_key = entity_keys[0]

    name = (
        raw.get("company_name")
        or raw.get("name")
        or raw.get("nameWithOwner")
        or raw.get("title")
    )
    domain = raw.get("homepageUrl") or raw.get("domain")

    founder_names = []
    for sig in signals:
        r = sig.get("raw_json") or {}
        if isinstance(r, str):
            try:
                r = json.loads(r)
            except Exception:
                r = {}
        officers = r.get("officers", [])
        for o in officers:
            fname = o.get("name")
            if fname and fname not in founder_names:
                founder_names.append(fname)
        makers = r.get("makers", [])
        for m in makers:
            mname = m.get("name")
            if mname and mname not in founder_names:
                founder_names.append(mname)

    return {
        "entity_key": entity_key,
        "name": name,
        "domain": domain,
        "founder_names": founder_names,
        "sources": sources,
        "signals": signals,
    }


def dedupe_from_db(since_date: str | None = None) -> list[dict]:
    """Load today's raw signals from DB, deduplicate, and return merged entities."""
    store = Store()
    if since_date:
        rows = store.conn.execute(
            "SELECT * FROM raw_signals WHERE DATE(collected_at) >= ?",
            (since_date,)
        ).fetchall()
    else:
        rows = store.conn.execute(
            "SELECT * FROM raw_signals WHERE DATE(collected_at) = DATE('now')"
        ).fetchall()

    signals = []
    for row in rows:
        d = dict(row)
        try:
            d["raw_json"] = json.loads(d["raw_json"])
        except Exception:
            pass
        signals.append(d)

    return dedupe(signals)
