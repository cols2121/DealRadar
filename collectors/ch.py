import os
import sys
import time
import json
from datetime import date, timedelta

import httpx

from store import Store

BASE = "https://api.company-information.service.gov.uk"
TECH_SIC = {"62012", "62020", "62090", "63110", "72190"}
EX_SCALEUP_KEYWORDS = [
    "monzo", "revolut", "wise", "spotify", "delivery hero",
    "transferwise", "babylon", "checkout", "starling", "freetrade",
    "deliveroo", "funding circle", "gousto", "bulb", "octopus",
]


def _get(path: str, params: dict | None = None) -> dict:
    api_key = os.environ.get("CH_API_KEY", "")
    for attempt in range(3):
        try:
            r = httpx.get(
                f"{BASE}{path}",
                params=params,
                auth=(api_key, ""),
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}


def _is_serial_founder(officer_id: str) -> bool:
    try:
        appts = _get(f"/officers/{officer_id}/appointments")
        return len(appts.get("items", [])) > 1
    except Exception:
        return False


def collect(days_back: int = 7) -> dict:
    store = Store()
    store.init_db()
    since = (date.today() - timedelta(days=days_back)).isoformat()
    start = time.time()
    fetched = 0
    written = 0
    errors = []

    start_index = 0
    while True:
        try:
            data = _get("/search/companies", {
                "q": "*",
                "incorporated_from": since,
                "start_index": start_index,
                "items_per_page": 100,
            })
        except Exception as e:
            errors.append(f"Search page {start_index}: {e}")
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            fetched += 1
            num = item.get("company_number")
            if not num:
                continue
            try:
                profile = _get(f"/company/{num}")
                sic_codes = set(profile.get("sic_codes", []))
                if not sic_codes & TECH_SIC:
                    continue

                officers_data = _get(f"/company/{num}/officers")
                officers = officers_data.get("items", [])
                serial_founder = False
                for officer in officers:
                    appt_path = (
                        officer.get("links", {})
                        .get("officer", {})
                        .get("appointments", "")
                    )
                    parts = [p for p in appt_path.split("/") if p]
                    if len(parts) >= 2:
                        officer_id = parts[-2]
                        if _is_serial_founder(officer_id):
                            serial_founder = True

                entity_key = f"ch:{num}"
                store.insert_signal("companies_house", entity_key, {
                    **profile,
                    "officers": officers,
                    "serial_founder": serial_founder,
                })
                written += 1
                time.sleep(0.5)

            except Exception as e:
                errors.append(f"Company {num}: {e}")
                continue

        total = data.get("total_results", 0)
        start_index += 100
        if start_index >= total:
            break

    duration = time.time() - start
    report = {
        "source": "companies_house",
        "records_fetched": fetched,
        "records_written": written,
        "duration_s": round(duration, 1),
        "errors": errors,
    }
    print(f"[ch] fetched={fetched} written={written} duration={duration:.1f}s errors={len(errors)}")
    return report


if __name__ == "__main__":
    if not os.environ.get("CH_API_KEY"):
        print("CH_API_KEY not set — skipping live run", file=sys.stderr)
        sys.exit(0)
    collect()
