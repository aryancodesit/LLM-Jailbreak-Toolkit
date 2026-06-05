import sqlite3
from attacks.base import AttackResult


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT,
    attack_name TEXT,
    target      TEXT,
    prompt      TEXT,
    response    TEXT,
    success     INTEGER,
    confidence  REAL,
    tokens      INTEGER,
    cost_usd    REAL,
    notes       TEXT
);
"""


class ResultStore:
    def __init__(self, db_path: str = "results.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(CREATE_TABLE)
        self.conn.commit()

    def save(self, result: AttackResult):
        self.conn.execute(
            """INSERT INTO results
               (timestamp, attack_name, target, prompt, response,
                success, confidence, tokens, cost_usd, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                result.timestamp,
                result.attack_name,
                result.target_behavior,
                result.prompt,
                result.response,
                int(result.success),
                result.confidence,
                result.tokens_used,
                result.cost_usd,
                result.notes,
            ),
        )
        self.conn.commit()

    def fetch_all(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM results ORDER BY timestamp DESC"
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def fetch_summary(self) -> dict:
        cur = self.conn.execute(
            "SELECT COUNT(*), SUM(success), SUM(cost_usd) FROM results"
        )
        total, successes, cost = cur.fetchone()
        return {
            "total": total or 0,
            "successes": successes or 0,
            "failures": (total or 0) - (successes or 0),
            "total_cost_usd": round(cost or 0.0, 5),
        }

    def close(self):
        self.conn.close()

    def fetch_heatmap(self) -> dict:
        """
        Returns {attack_name: {total, successes, rate}} for heatmap rendering.
        """
        cur = self.conn.execute(
            """
            SELECT attack_name,
                   COUNT(*)    AS total,
                   SUM(success) AS successes
            FROM results
            GROUP BY attack_name
            ORDER BY attack_name
            """
        )
        heatmap = {}
        for row in cur.fetchall():
            name, total, successes = row
            rate = (successes / total * 100) if total else 0
            heatmap[name] = {
                "total": total,
                "successes": int(successes or 0),
                "failures": int(total - (successes or 0)),
                "rate": round(rate, 1),
            }
        return heatmap

    def fetch_by_attack(self, attack_name: str) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM results WHERE attack_name = ? ORDER BY timestamp DESC",
            (attack_name,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def fetch_models(self) -> list[str]:
        """Extract unique model names from notes field."""
        cur = self.conn.execute("SELECT DISTINCT notes FROM results")
        models = set()
        for (notes,) in cur.fetchall():
            if notes:
                for part in notes.split("|"):
                    part = part.strip()
                    if part.startswith("Model:"):
                        models.add(part.replace("Model:", "").strip())
        return sorted(models) or ["unknown"]
