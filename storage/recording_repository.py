"""High-level recording management combining database and filesystem.

``RecordingRepository`` sits on top of :class:`RecordingDatabase` and the
filesystem, providing a single entry-point for all recording operations such
as registering, deleting, searching, exporting and integrity checking.
"""

import io
import json
import struct
import logging
import wave
from pathlib import Path
from datetime import datetime
from typing import Optional

from storage.database import RecordingDatabase
from crypto.file_format import validate_file
from crypto.decryption import decrypt_file

logger = logging.getLogger(__name__)


def _validate_header(filepath: str) -> bool:
    """Return ``True`` if *filepath* is a valid SafeNote (.sna) file."""
    return validate_file(filepath)


class RecordingRepository:
    """High-level recording management combining database and filesystem.

    Parameters
    ----------
    storage_dir : str, optional
        Directory where ``.sna`` files are stored.
        Defaults to ``~/SafeNote/Recordings``.
    db_path : str, optional
        Path to the SQLite database file.
        Defaults to ``~/SafeNote/safenote.db``.
    """

    def __init__(self, storage_dir: str = None, db_path: str = None):
        if storage_dir is None:
            storage_dir = str(Path.home() / "SafeNote" / "Recordings")
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._db = RecordingDatabase(db_path)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def storage_dir(self) -> Path:
        """Return the directory where recordings are stored."""
        return self._storage_dir

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    def register_recording(self, filepath: str, metadata: dict) -> int:
        """Register a newly-saved recording in the database.

        Parameters
        ----------
        filepath : str
            Absolute path to the encrypted ``.sna`` file.
        metadata : dict
            Recording metadata.  Expected keys (all optional except where
            the database requires them):

            - ``display_name`` (str)
            - ``created_at`` (str, ISO-8601)
            - ``duration_seconds`` (float)
            - ``sample_rate`` (int)
            - ``channels`` (int)

        Returns
        -------
        int
            The database ``id`` of the registered recording.
        """
        p = Path(filepath)
        filename = p.name
        display_name = metadata.get("display_name", p.stem)
        created_at = metadata.get("created_at", datetime.now().isoformat())
        duration = metadata.get("duration_seconds")
        sample_rate = metadata.get("sample_rate", 44100)
        channels = metadata.get("channels", 1)

        try:
            file_size = p.stat().st_size
        except OSError:
            file_size = None

        return self._db.add_recording(
            filepath=str(p),
            filename=filename,
            display_name=display_name,
            created_at=created_at,
            duration_seconds=duration,
            file_size=file_size,
            sample_rate=sample_rate,
            channels=channels,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all_recordings(self) -> list[dict]:
        """Return all recordings, annotated with an ``exists`` flag.

        Each returned dict contains an extra boolean key ``"exists"``
        indicating whether the file is still present on disk.
        """
        recordings = self._db.get_all_recordings()
        for rec in recordings:
            rec["exists"] = Path(rec["filepath"]).is_file()
        return recordings

    def get_recording(self, recording_id: int) -> Optional[dict]:
        """Return a single recording by *recording_id*, or ``None``."""
        rec = self._db.get_recording(recording_id)
        if rec is not None:
            rec["exists"] = Path(rec["filepath"]).is_file()
        return rec

    def search(self, query: str) -> list[dict]:
        """Search recordings by display name or notes."""
        results = self._db.search_recordings(query)
        for rec in results:
            rec["exists"] = Path(rec["filepath"]).is_file()
        return results

    # ------------------------------------------------------------------
    # Rename
    # ------------------------------------------------------------------

    def rename(self, recording_id: int, new_name: str) -> None:
        """Rename a recording's display name."""
        self._db.rename_recording(recording_id, new_name)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, recording_id: int) -> bool:
        """Delete a recording from both the database and the filesystem.

        The caller is expected to have already confirmed the action with
        the user.

        Returns
        -------
        bool
            ``True`` if the recording was successfully deleted, ``False``
            if the *recording_id* was not found.
        """
        filepath = self._db.delete_recording(recording_id)
        if filepath is None:
            return False
        p = Path(filepath)
        if p.is_file():
            try:
                p.unlink()
                logger.info("Deleted file %s", p)
            except OSError:
                logger.exception("Failed to delete file %s", p)
        return True

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_wav(
        self,
        recording_id: int,
        destination: str,
        key: bytes,
    ) -> bool:
        """Decrypt a recording and export it as an unencrypted WAV file.

        Parameters
        ----------
        recording_id : int
            Database id of the recording to export.
        destination : str
            Path where the WAV file should be written.
        key : bytes
            32-byte AES-256 key used for decryption.

        Returns
        -------
        bool
            ``True`` on success, ``False`` on any failure.
        """
        rec = self._db.get_recording(recording_id)
        if rec is None:
            logger.error("export_wav: recording id=%d not found", recording_id)
            return False

        src = Path(rec["filepath"])
        if not src.is_file():
            logger.error("export_wav: file not found %s", src)
            return False

        try:
            metadata, raw_audio = decrypt_file(src, key)
        except Exception:
            logger.exception("export_wav: decryption failed for %s", src)
            return False

        sample_rate = int(metadata.get("sample_rate", rec.get("sample_rate", 44100)))
        channels = int(metadata.get("channels", rec.get("channels", 1)))

        try:
            dest = Path(destination)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(dest), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # PCM_16 = 2 bytes per sample
                wf.setframerate(sample_rate)
                wf.writeframes(raw_audio)
            logger.info("Exported WAV to %s", dest)
            return True
        except Exception:
            logger.exception("export_wav: writing WAV failed for %s", destination)
            return False

    @staticmethod
    def _decrypt_sna(path: Path, key: bytes) -> bytes:
        """Decrypt a ``.sna`` file and return the raw PCM audio bytes."""
        _metadata, raw_audio = decrypt_file(path, key)
        return raw_audio

    # ------------------------------------------------------------------
    # Validation & scanning
    # ------------------------------------------------------------------

    def validate_recording(self, filepath: str) -> bool:
        """Check whether an ``.sna`` file has a valid header."""
        return _validate_header(filepath)

    def scan_directory(self) -> list[str]:
        """Find ``.sna`` files on disk that are not yet in the database.

        Newly discovered files are automatically registered with sensible
        defaults.  Returns a list of filepaths that were registered.
        """
        registered: list[str] = []
        for sna_file in self._storage_dir.glob("*.sna"):
            abs_path = str(sna_file)
            if self._db.recording_exists(abs_path):
                continue
            if not _validate_header(abs_path):
                logger.warning("scan: skipping invalid file %s", abs_path)
                continue

            try:
                file_size = sna_file.stat().st_size
            except OSError:
                file_size = None

            try:
                mtime = sna_file.stat().st_mtime
                created_at = datetime.fromtimestamp(mtime).isoformat()
            except OSError:
                created_at = datetime.now().isoformat()

            self._db.add_recording(
                filepath=abs_path,
                filename=sna_file.name,
                display_name=sna_file.stem,
                created_at=created_at,
                file_size=file_size,
            )
            registered.append(abs_path)
            logger.info("scan: registered %s", abs_path)

        return registered

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def cleanup_orphaned(self) -> int:
        """Remove database entries whose files no longer exist on disk.

        Returns
        -------
        int
            Number of orphaned entries removed.
        """
        existing = {
            str(p) for p in self._storage_dir.glob("*.sna") if p.is_file()
        }
        return self._db.cleanup_orphaned(existing)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_storage_stats(self) -> dict:
        """Return summary statistics about the recording store.

        Returns
        -------
        dict
            Keys: ``total_recordings`` (int), ``total_size`` (int, bytes),
            ``storage_dir`` (str).
        """
        return {
            "total_recordings": self._db.get_recording_count(),
            "total_size": self._db.get_total_size(),
            "storage_dir": str(self._storage_dir),
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release database resources."""
        self._db.close()
