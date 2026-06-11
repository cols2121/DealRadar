import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("data/dealradar.db")


class Store:
    def __init__(self, path=DB_PATH):
        Path(path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row

    def init_db(self):
        schema = Path("schema.sql").read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    def insert_signal(self, source: str, entity_key: str, raw_json: dict):
        self.conn.execute(
            "INSERT INTO raw_signals(source,entity_key,raw_json,collected_at) VALUES(?,?,?,?)",
            (source, entity_key, json.dumps(raw_json), datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def upsert_company(self, entity_key: str, **fields):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO companies(entity_key,name,domain,founder_names,sources,first_seen,updated_at)
               VALUES(:entity_key,:name,:domain,:founder_names,:sources,:now,:now)
               ON CONFLICT(entity_key) DO UPDATE SET
                 name=excluded.name, domain=excluded.domain,
                 founder_names=excluded.founder_names, sources=excluded.sources,
                 updated_at=excluded.updated_at""",
            {"entity_key": entity_key, "now": now,
             "name": fields.get("name"),
             "domain": fields.get("domain"),
             "founder_names": fields.get("founder_names"),
             "sources": fields.get("sources")}
        )
        self.conn.commit()

    def insert_score(self, entity_key: str, score_dict: dict, tokens_used: int, cost_gbp: float):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO scores(entity_key,score,stage_guess,one_line,memo,confidence,
                                  evidence_urls,tokens_used,cost_gbp,scored_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (entity_key, score_dict["score"], score_dict.get("stage_guess"),
             score_dict.get("one_line"), score_dict.get("memo_3_lines"),
             score_dict.get("confidence"),
             json.dumps(score_dict.get("evidence_urls", [])),
             tokens_used, cost_gbp, now)
        )
        self.conn.commit()

    def insert_feedback(self, entity_key: str, user_id: str, signal: str):
        self.conn.execute(
            "INSERT INTO feedback(entity_key,user_id,signal,ts) VALUES(?,?,?,?)",
            (entity_key, user_id, signal, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()
