import json
from datetime import date


def render_slack_blocks(candidates: list[dict], run_stats: dict) -> list[dict]:
    """
    Render top candidates as Slack Block Kit blocks with feedback buttons.
    Each candidate dict must have: entity_key, score, one_line, memo, evidence_urls,
    name (optional), stage_guess (optional).
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"DealRadar — {date.today().strftime('%d %b %Y')} | Top {len(candidates)} pre-seed signals",
            },
        }
    ]

    for i, c in enumerate(candidates, 1):
        name = c.get("name") or c.get("entity_key", "Unknown")
        one_line = c.get("one_line") or ""
        memo = c.get("memo") or c.get("memo_3_lines") or ""
        evidence_urls = c.get("evidence_urls") or []
        if isinstance(evidence_urls, str):
            try:
                evidence_urls = json.loads(evidence_urls)
            except Exception:
                evidence_urls = []
        score = c.get("score", 0)
        stage = c.get("stage_guess") or c.get("stage", "unknown")
        entity_key = c.get("entity_key", f"entity_{i}")

        # Build evidence links text
        links_text = "  ".join(
            f"<{url}|Evidence {j}>" for j, url in enumerate(evidence_urls[:3], 1)
        )

        section_text = (
            f"*{i}. {name}* — _{one_line}_\n\n"
            f"{memo}\n\n"
        )
        if links_text:
            section_text += links_text

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": section_text},
            "accessory": {
                "type": "mrkdwn_element" if False else "plain_text_input",
            } if False else {
                "type": "button",
                "text": {"type": "plain_text", "text": f"#{i} · Score {score} · {stage}"},
                "action_id": f"view_{i}",
                "value": entity_key,
            },
        })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👍 Interesting"},
                    "style": "primary",
                    "action_id": "feedback_up",
                    "value": f"up::{entity_key}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👎 Not relevant"},
                    "style": "danger",
                    "action_id": "feedback_down",
                    "value": f"down::{entity_key}",
                },
            ],
        })

    # Run report footer
    precision = run_stats.get("precision_7d")
    precision_str = f" · Precision (7d): {precision:.0%}" if precision is not None else ""
    cost = run_stats.get("cost_gbp", 0)
    sources = run_stats.get("sources_active", 0)
    signals = run_stats.get("signals_collected", 0)

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": (
                    f"📊 {signals} signals · {sources} sources · "
                    f"Cost: £{cost:.4f}{precision_str} · "
                    f"<https://github.com|DealRadar>"
                ),
            }
        ],
    })

    return blocks


def render_email_html(candidates: list[dict], run_stats: dict) -> str:
    """Minimal HTML email fallback."""
    run_date = date.today().strftime("%d %b %Y")
    rows = ""
    for i, c in enumerate(candidates, 1):
        name = c.get("name") or c.get("entity_key", "Unknown")
        one_line = c.get("one_line") or ""
        memo = (c.get("memo") or c.get("memo_3_lines") or "").replace("\n", "<br>")
        score = c.get("score", 0)
        evidence_urls = c.get("evidence_urls") or []
        if isinstance(evidence_urls, str):
            try:
                evidence_urls = json.loads(evidence_urls)
            except Exception:
                evidence_urls = []
        links = " · ".join(f'<a href="{u}">Evidence {j}</a>' for j, u in enumerate(evidence_urls[:3], 1))
        rows += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #eee">
            <strong>{i}. {name}</strong> &mdash; <em>{one_line}</em><br>
            <small>Score: {score}</small><br><br>
            {memo}<br><br>
            {links}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;max-width:600px;margin:auto">
<h2>DealRadar — {run_date}</h2>
<table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
<p style="color:#999;font-size:12px">
  {run_stats.get('signals_collected',0)} signals · {run_stats.get('sources_active',0)} sources ·
  Cost: £{run_stats.get('cost_gbp',0):.4f}
</p>
</body></html>"""
