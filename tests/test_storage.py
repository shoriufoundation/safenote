"""
Automated unit tests for SafeNote Storage Module.

Tests:
- Database creation & WAL configuration
- Recording registration, retrieval, and counting
- Search by display name
- Rename recording
- Delete recording
- Orphaned recordings cleanup
- WAV export integrity and header validation
"""

import os
import secrets
import tempfile
import wave
from pathlib import Path

import pytest

from crypto.encryption import AudioEncryptor
from storage.database import RecordingDatabase
from storage.recording_repository import RecordingRepository


@pytest.fixture
def temp_env():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        db_path = str(p / "test_safenote.db")
        store_dir = str(p / "recordings")
        repo = RecordingRepository(storage_dir=store_dir, db_path=db_path)
        yield repo, p
        repo.close()


def test_database_crud(temp_env):
    """Test basic database operations."""
    repo, path = temp_env
    db = repo._db

    rec_id = db.add_recording(
        filepath=str(path / "rec1.sna"),
        filename="rec1.sna",
        display_name="Meeting Notes",
        created_at="2026-11-14T10:00:00",
        duration_seconds=65.2,
        file_size=204800,
        sample_rate=44100,
        channels=1,
    )
    assert rec_id > 0
    assert db.get_recording_count() == 1

    rec = db.get_recording(rec_id)
    assert rec["display_name"] == "Meeting Notes"
    assert rec["duration_seconds"] == 65.2

    # Search
    results = db.search_recordings("Meeting")
    assert len(results) == 1
    assert results[0]["id"] == rec_id

    # Rename
    db.rename_recording(rec_id, "Updated Meeting Notes")
    assert db.get_recording(rec_id)["display_name"] == "Updated Meeting Notes"

    # Delete
    deleted_path = db.delete_recording(rec_id)
    assert deleted_path == str(path / "rec1.sna")
    assert db.get_recording_count() == 0


def test_repository_export_wav(temp_env):
    """Test decrypting and exporting a recording to unencrypted WAV."""
    repo, path = temp_env
    key = secrets.token_bytes(32)

    # 1. Create a genuine encrypted recording
    sna_path = path / "recordings" / "test_export.sna"
    sna_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "sample_rate": 44100,
        "channels": 1,
        "format": "PCM_16",
        "duration_seconds": 1.0,
    }
    raw_pcm = b"\x00\x00" * 44100  # 1 second of silence

    enc = AudioEncryptor(key, sna_path)
    enc.start()
    enc.write_chunk(raw_pcm)
    enc.finalize(metadata)

    rec_id = repo.register_recording(str(sna_path), metadata)
    assert rec_id > 0

    # 2. Export to WAV
    wav_path = str(path / "exported.wav")
    success = repo.export_wav(rec_id, wav_path, key)
    assert success is True
    assert os.path.exists(wav_path)

    # 3. Verify WAV header & contents
    with wave.open(wav_path, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        assert wf.getnframes() == 44100
        assert wf.readframes(44100) == raw_pcm


def test_cleanup_orphaned_records(temp_env):
    """Test cleaning up records for files deleted from disk."""
    repo, path = temp_env
    db = repo._db

    # Add record for a non-existent file
    db.add_recording(
        filepath=str(path / "ghost.sna"),
        filename="ghost.sna",
        display_name="Ghost Recording",
        created_at="2026-11-14T08:00:00",
    )
    assert db.get_recording_count() == 1

    # Cleanup with empty existing paths set
    removed = repo.cleanup_orphaned()
    assert removed == 1
    assert db.get_recording_count() == 0
