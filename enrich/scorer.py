import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from config.thesis_model import load_thesis
from enrich.llm_client import LLMClient

SYSTEM_PROMPT = Path("enrich/prompts/score_system.txt").read_text()
FEWSHOT = Path("enrich/prompts/score_fewshot.txt").read_text()


class ScoringError(Exception):
    pass


@dataclass
class ScoreResult:
    score: int
    stage_guess: str
    one_line: str
    memo_3_lines: str
    confidence: str
    evidence_urls: list[str] = field(default_factory=list)


def _enforce_citations(memo: str, urls: list[str]) -> str:
    """Remove memo sentences that don't cite any evidence URL."""
    if not memo:
        return ""
    if not urls:
        return ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", memo) if s.strip()]
    cited = [s for s in sentences if any(url in s for url in urls)]
    return " ".join(cited) if cited else ""


def _parse_json(raw: str) -> dict:
    """Extract JSON from LLM response, tolerating minor formatting issues."""
    raw = raw.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def score_entity(
    entity_key: str,
    signals: list[dict],
    client: LLMClient | None = None,
) -> ScoreResult:
    if client is None:
        client = LLMClient()

    thesis = load_thesis()
    system = SYSTEM_PROMPT.replace("{thesis_json}", thesis.model_dump_json(indent=2))
    prompt = (
        f"{FEWSHOT}\n\n"
        f"---\n\n"
        f"## CANDIDATE TO SCORE\n\n"
        f"Entity key: {entity_key}\n\n"
        f"Signals:\n{json.dumps(signals, indent=2, default=str)}"
    )

    last_error = None
    for attempt in range(2):
        try:
            raw = client.complete(prompt, system=system, max_tokens=700)
            data = _parse_json(raw)

            result = ScoreResult(
                score=int(data["score"]),
                stage_guess=str(data.get("stage_guess", "unknown")),
                one_line=str(data.get("one_line", "")),
                memo_3_lines=str(data.get("memo_3_lines", "")),
                confidence=str(data.get("confidence", "low")),
                evidence_urls=list(data.get("evidence_urls", [])),
            )
            # Enforce cite-or-omit
            result.memo_3_lines = _enforce_citations(
                result.memo_3_lines, result.evidence_urls
            )
            return result

        except Exception as e:
            last_error = e
            if attempt == 0:
                # Retry once with stricter instruction prepended
                prompt = "Respond with valid JSON only, no other text.\n\n" + prompt

    raise ScoringError(
        f"Failed to score {entity_key} after 2 attempts: {last_error}"
    )


def score_and_store(entity_key: str, signals: list[dict]) -> ScoreResult:
    """Score an entity and persist the result to SQLite."""
    from store import Store

    client = LLMClient()
    result = score_entity(entity_key, signals, client=client)

    store = Store()
    store.insert_score(
        entity_key=entity_key,
        score_dict={
            "score": result.score,
            "stage_guess": result.stage_guess,
            "one_line": result.one_line,
            "memo_3_lines": result.memo_3_lines,
            "confidence": result.confidence,
            "evidence_urls": result.evidence_urls,
        },
        tokens_used=0,   # populated by LLMClient stdout log
        cost_gbp=0.0,
    )
    return result
