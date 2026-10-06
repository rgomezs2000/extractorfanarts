"""Persistencia local (SQLite): historial de descargas y deduplicación."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class DownloadStore:
    """Almacén pequeño para registrar hashes de lo ya descargado."""

    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS descargas ("
                "md5 TEXT PRIMARY KEY, url TEXT, path TEXT, ts REAL)"
            )
            self._conn.commit()

    def load_hashes(self) -> set[str]:
        with self._lock:
            rows = self._conn.execute("SELECT md5 FROM descargas").fetchall()
        return {row[0] for row in rows}

    def add(self, md5: str, url: str, path: str) -> None:
        import time
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO descargas (md5, url, path, ts) VALUES (?, ?, ?, ?)",
                (md5, url, path, time.time()),
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
