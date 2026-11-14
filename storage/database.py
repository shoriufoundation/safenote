"""Thread-safe SQLite database for SafeNote recording metadata.

Provides CRUD operations for recording entries stored in an SQLite
database with WAL journaling mode.  Every public method obtains a
per-thread connection so the class is safe to use from any thread.
"""

import sqlite3
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALLOWED_ORDER_COLUMNS = frozenset({
    "created_timestamp",
    "display_name",
    "duration_seconds",
    "file_size",
    "filename",
})


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert an ``sqlite3.Row`` to a plain dictionary."""
    return dict(row)


class RecordingDatabase:
    """Thread-safe SQLite database for recording metadata.

    Parameters
    ----------
    db_path : str, optional
        Absolute path to the database file.  Defaults to
        ``~/SafeNote/safenote.db``.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / "SafeNote" / "safenote.db")
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return a per-thread ``sqlite3.Connection``."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    # ------------------------------------------------------------------
    # Schema initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS recordings (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                filename          TEXT    NOT NULL,
                filepath          TEXT    NOT NULL UNIQUE,
                display_name      TEXT,
                created_at        TEXT    NOT NULL,
                duration_seconds  REAL,
                file_size         INTEGER,
                sample_rate       INTEGER DEFAULT 44100,
                channels          INTEGER DEFAULT 1,
                is_valid          INTEGER DEFAULT 1,
                notes             TEXT    DEFAULT '',
                tags              TEXT    DEFAULT '',
                created_timestamp REAL    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_recordings_created
                ON recordings(created_timestamp);
            CREATE INDEX IF NOT EXISTS idx_recordings_name
                ON recordings(display_name);
        """)
        conn.commit()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add_recording(
        self,
        filepath: str,
        filename: str,
        display_name: str,
        created_at: str,
        duration_seconds: Optional[float] = None,
        file_size: Optional[int] = None,
        sample_rate: int = 44100,
        channels: int = 1,
    ) -> int:
        """Insert a new recording and return its database ``id``.

        Parameters
        ----------
        filepath : str
            Absolute path to the encrypted ``.sna`` file.
        filename : str
            Basename of the file (e.g. ``recording_20260101_120000.sna``).
        display_name : str
            Human-friendly label shown in the UI.
        created_at : str
            ISO-8601 timestamp of when the recording was captured.
        duration_seconds : float, optional
            Length of the recording in seconds.
        file_size : int, optional
            Size of the encrypted file in bytes.
        sample_rate : int
            Audio sample rate (default ``44100``).
        channels : int
            Number of audio channels (default ``1``).

        Returns
        -------
        int
            The ``id`` of the newly inserted row.

        Raises
        ------
        sqlite3.IntegrityError
            If a recording with the same *filepath* already exists.
        """
        conn = self._get_conn()
        try:
            created_timestamp = datetime.fromisoformat(created_at).timestamp()
        except (ValueError, TypeError):
            created_timestamp = datetime.now().timestamp()

        cursor = conn.execute(
            """
            INSERT INTO recordings
                (filepath, filename, display_name, created_at,
                 duration_seconds, file_size, sample_rate, channels,
                 created_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filepath,
                filename,
                display_name,
                created_at,
                duration_seconds,
                file_size,
                sample_rate,
                channels,
                created_timestamp,
            ),
        )
        conn.commit()
        logger.debug("Added recording id=%d  path=%s", cursor.lastrowid, filepath)
        return cursor.lastrowid

    # ------------------------------------------------------------------
    # Read – single
    # ------------------------------------------------------------------

    def get_recording(self, recording_id: int) -> Optional[dict]:
        """Return a recording by *recording_id*, or ``None``."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM recordings WHERE id = ?", (recording_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None

    def get_recording_by_path(self, filepath: str) -> Optional[dict]:
        """Return a recording by its *filepath*, or ``None``."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM recordings WHERE filepath = ?", (filepath,)
        ).fetchone()
        return _row_to_dict(row) if row else None

    def recording_exists(self, filepath: str) -> bool:
        """Return ``True`` if a recording with *filepath* is registered."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM recordings WHERE filepath = ?", (filepath,)
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # Read – collection
    # ------------------------------------------------------------------

    def get_all_recordings(
        self,
        order_by: str = "created_timestamp",
        descending: bool = True,
    ) -> list[dict]:
        """Return every recording as a list of dicts.

        Parameters
        ----------
        order_by : str
            Column to sort by.  Must be one of the allowed columns.
        descending : bool
            Sort direction (newest first by default).
        """
        if order_by not in _ALLOWED_ORDER_COLUMNS:
            order_by = "created_timestamp"
        direction = "DESC" if descending else "ASC"
        conn = self._get_conn()
        rows = conn.execute(
            f"SELECT * FROM recordings ORDER BY {order_by} {direction}"
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def search_recordings(self, query: str) -> list[dict]:
        """Search recordings whose *display_name* or *notes* contain *query*.

        The search is case-insensitive.
        """
        conn = self._get_conn()
        pattern = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM recordings
            WHERE display_name LIKE ? OR notes LIKE ?
            ORDER BY created_timestamp DESC
            """,
            (pattern, pattern),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    _UPDATABLE_FIELDS = frozenset({
        "display_name",
        "duration_seconds",
        "file_size",
        "sample_rate",
        "channels",
        "is_valid",
        "notes",
        "tags",
    })

    def update_recording(self, recording_id: int, **kwargs) -> None:
        """Update one or more fields of a recording.

        Only fields listed in ``_UPDATABLE_FIELDS`` are accepted; unknown
        keys are silently ignored to prevent SQL injection.
        """
        fields = {k: v for k, v in kwargs.items() if k in self._UPDATABLE_FIELDS}
        if not fields:
            return
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [recording_id]
        conn = self._get_conn()
        conn.execute(
            f"UPDATE recordings SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        logger.debug("Updated recording id=%d  fields=%s", recording_id, list(fields))

    def rename_recording(self, recording_id: int, new_name: str) -> None:
        """Rename a recording's *display_name*."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE recordings SET display_name = ? WHERE id = ?",
            (new_name, recording_id),
        )
        conn.commit()
        logger.debug("Renamed recording id=%d  → %s", recording_id, new_name)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_recording(self, recording_id: int) -> Optional[str]:
        """Delete a recording entry and return its *filepath*.

        Returns
        -------
        str or None
            The *filepath* of the deleted recording so the caller can
            remove the physical file.  ``None`` if the id was not found.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT filepath FROM recordings WHERE id = ?", (recording_id,)
        ).fetchone()
        if row is None:
            return None
        filepath = row["filepath"]
        conn.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
        conn.commit()
        logger.info("Deleted recording id=%d  path=%s", recording_id, filepath)
        return filepath

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    def get_recording_count(self) -> int:
        """Return the total number of recordings."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) AS cnt FROM recordings").fetchone()
        return row["cnt"]

    def get_total_size(self) -> int:
        """Return the sum of all ``file_size`` values (bytes)."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COALESCE(SUM(file_size), 0) AS total FROM recordings"
        ).fetchone()
        return row["total"]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def cleanup_orphaned(self, existing_paths: set) -> int:
        """Remove entries whose file no longer exists on disk.

        Parameters
        ----------
        existing_paths : set of str
            Set of absolute file paths that are known to still exist.

        Returns
        -------
        int
            Number of orphaned entries removed.
        """
        conn = self._get_conn()
        rows = conn.execute("SELECT id, filepath FROM recordings").fetchall()
        orphaned_ids = [
            row["id"]
            for row in rows
            if row["filepath"] not in existing_paths
        ]
        if orphaned_ids:
            placeholders = ", ".join("?" for _ in orphaned_ids)
            conn.execute(
                f"DELETE FROM recordings WHERE id IN ({placeholders})",
                orphaned_ids,
            )
            conn.commit()
            logger.info("Cleaned up %d orphaned recording(s)", len(orphaned_ids))
        return len(orphaned_ids)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the current thread's database connection."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                logger.exception("Error closing database connection")
            finally:
                self._local.conn = None
