import json
import os
import urllib.parse

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from store import Store

app = FastAPI(title="DealRadar Feedback API")


@app.post("/slack/actions")
async def slack_actions(request: Request):
    """Receive Slack interactive component payloads (button clicks)."""
    body = await request.body()
    try:
        decoded = body.decode("utf-8")
        if decoded.startswith("payload="):
            decoded = urllib.parse.unquote(decoded[len("payload="):])
        payload = json.loads(decoded)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Invalid payload: {e}"}, status_code=400)

    store = Store()
    for action in payload.get("actions", []):
        value = action.get("value", "")
        if "::" not in value:
            continue
        signal, entity_key = value.split("::", 1)
        if signal not in ("up", "down"):
            continue
        user_id = payload.get("user", {}).get("id", "unknown")
        try:
            store.insert_feedback(entity_key, user_id, signal)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    return JSONResponse({"ok": True})


@app.get("/health")
async def health():
    return {"status": "ok"}
