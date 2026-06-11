import time
from dataclasses import dataclass, field

import httpx


@dataclass
class RunReport:
    source: str
    records_fetched: int = 0
    records_written: int = 0
    duration_s: float = 0.0
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "OK" if not self.errors else f"ERRORS({len(self.errors)})"
        return (
            f"[{self.source}] {status} "
            f"fetched={self.records_fetched} written={self.records_written} "
            f"duration={self.duration_s:.1f}s"
        )


class BaseCollector:
    source: str = "base"

    def retry_get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        auth: tuple | None = None,
        max_attempts: int = 3,
    ) -> httpx.Response:
        for attempt in range(max_attempts):
            try:
                r = httpx.get(
                    url,
                    params=params,
                    headers=headers,
                    auth=auth,
                    timeout=15,
                )
                r.raise_for_status()
                return r
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("retry_get exhausted")
