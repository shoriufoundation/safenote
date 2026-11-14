"""
Streaming AES-256-GCM encryption for SafeNote Audio (.sna) files.

Design
------
The :class:`AudioEncryptor` accumulates plaintext (metadata JSON + raw audio)
and performs a **single** AES-256-GCM encrypt-then-write pass in
:meth:`finalize`.  GCM is a one-shot AEAD — the ``cryptography`` library does
not support incremental ``update()`` calls for GCM mode — so we buffer the
plaintext in a temporary file during recording and encrypt in one step at the
end.

File-safety contract:
* During recording, only a ``.sna.tmp`` file exists.
* On :meth:`finalize`, the encrypted output is written to a second temp file
  which is atomically renamed to the final ``.sna`` path.
* On :meth:`abort`, the temp file is deleted.
* A partial / orphaned ``.sna`` file can never be mistaken for a complete one
  because only :meth:`finalize` creates the final path.

Byte-level layout written to disk (see :mod:`crypto.file_format` for the
canonical spec)::

    HEADER (22 B)  |  ENCRYPTED_BLOB (variable)  |  GCM_TAG (16 B)

Where ENCRYPTED_BLOB = Enc(metadata_json ‖ audio_pcm).
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import tempfile
from pathlib import Path
from typing import Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .file_format import (
    HEADER_SIZE,
    NONCE_SIZE,
    TAG_SIZE,
    build_header,
)

logger = logging.getLogger(__name__)


class AudioEncryptor:
    """Stream audio data into an encrypted ``.sna`` file.

    Usage::

        enc = AudioEncryptor(key=my_key, output_path="recording.sna")
        enc.start()
        for chunk in audio_chunks:
            enc.write_chunk(chunk)
        enc.finalize(metadata)   # atomic write
        # — or —
        enc.abort()              # discard on error

    Args:
        key: 32-byte AES-256 key.
        output_path: Final destination path for the ``.sna`` file.
    """

    def __init__(self, key: bytes, output_path: Union[str, Path]) -> None:
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")

        self._key: bytes = key
        self._output_path: Path = Path(output_path)
        self._tmp_plaintext_path: Path | None = None
        self._tmp_fh = None  # file handle for plaintext buffer
        self._started: bool = False
        self._finalized: bool = False
        self._audio_bytes_written: int = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self, metadata: dict | None = None) -> None:
        """Open a temporary file to buffer raw audio plaintext.

        Args:
            metadata: Optional initial metadata dictionary.

        Raises:
            RuntimeError: If already started.
        """
        if self._started:
            raise RuntimeError("AudioEncryptor already started")

        # Create temp file in the same directory as the final output so that
        # os.replace() is guaranteed to be atomic (same filesystem).
        out_dir = self._output_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            suffix=".sna.tmp", dir=str(out_dir)
        )
        self._tmp_plaintext_path = Path(tmp_path)
        self._tmp_fh = os.fdopen(fd, "wb")
        self._started = True
        self._audio_bytes_written = 0
        logger.debug("AudioEncryptor started, temp buffer: %s", tmp_path)

    def write_chunk(self, data: bytes) -> None:
        """Append a chunk of raw PCM16 audio to the plaintext buffer.

        Args:
            data: Raw audio bytes (typically 16-bit PCM).

        Raises:
            RuntimeError: If the encryptor has not been started or has already
                          been finalized / aborted.
        """
        if not self._started or self._finalized:
            raise RuntimeError(
                "Cannot write_chunk: encryptor is not in an active state"
            )
        if self._tmp_fh is None:
            raise RuntimeError("Temp file handle is None — was abort() called?")

        self._tmp_fh.write(data)
        self._audio_bytes_written += len(data)

    def finalize(self, metadata: dict) -> Path:
        """Encrypt buffered data and atomically write the final ``.sna`` file.

        The plaintext is assembled as ``metadata_json_bytes ‖ audio_bytes``,
        encrypted in a single AES-256-GCM operation, and the result is
        written as::

            header (22 B) | ciphertext (variable) | tag (16 B)

        Args:
            metadata: JSON-serialisable dict with recording metadata
                      (sample_rate, channels, format, created_at,
                      duration_seconds, original_filename, …).

        Returns:
            The :class:`~pathlib.Path` of the written ``.sna`` file.

        Raises:
            RuntimeError: If the encryptor is not in an active state.
        """
        if not self._started or self._finalized:
            raise RuntimeError(
                "Cannot finalize: encryptor is not in an active state"
            )
        if self._tmp_fh is None:
            raise RuntimeError("Temp file handle is None — was abort() called?")

        # ── 1. Flush and re-read the buffered audio ──────────────────────
        self._tmp_fh.flush()
        self._tmp_fh.close()
        self._tmp_fh = None

        audio_plaintext = self._tmp_plaintext_path.read_bytes()

        # ── 2. Prepare metadata ──────────────────────────────────────────
        metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        metadata_length = len(metadata_bytes)

        # ── 3. Assemble plaintext: metadata ‖ audio ──────────────────────
        plaintext = metadata_bytes + audio_plaintext

        # ── 4. Generate unique nonce per recording & build header ─────────
        nonce = secrets.token_bytes(NONCE_SIZE)
        header = build_header(nonce, metadata_length)
        assert len(header) == HEADER_SIZE

        # ── 5. Encrypt (AES-256-GCM, single shot with header as AAD) ────
        # Authenticate header (magic, version, nonce, metadata_length) via AAD
        aesgcm = AESGCM(self._key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, header)

        ciphertext = ciphertext_with_tag[:-TAG_SIZE]
        tag = ciphertext_with_tag[-TAG_SIZE:]

        # ── 6. Atomic write to final path ────────────────────────────────
        # Write to a second temporary file, then rename.
        out_dir = self._output_path.parent
        fd2, tmp_enc_path = tempfile.mkstemp(
            suffix=".sna.enc.tmp", dir=str(out_dir)
        )
        try:
            with os.fdopen(fd2, "wb") as fh:
                fh.write(header)
                fh.write(ciphertext)
                fh.write(tag)

            os.replace(tmp_enc_path, str(self._output_path))
        except BaseException:
            # Clean up the encrypted temp file on failure
            try:
                os.unlink(tmp_enc_path)
            except OSError:
                pass
            raise
        finally:
            # Always clean up the plaintext temp file
            self._cleanup_tmp()

        self._finalized = True
        logger.info(
            "Finalized SNA file: %s (%d bytes audio, %d bytes metadata)",
            self._output_path,
            len(audio_plaintext),
            metadata_length,
        )
        return self._output_path

    def abort(self) -> None:
        """Discard the recording and clean up temporary files."""
        if self._tmp_fh is not None:
            try:
                self._tmp_fh.close()
            except OSError:
                pass
            self._tmp_fh = None

        self._cleanup_tmp()
        self._finalized = True  # prevent further writes
        logger.debug("AudioEncryptor aborted")

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def output_path(self) -> Path:
        """Final destination path for the ``.sna`` file."""
        return self._output_path

    @property
    def audio_bytes_written(self) -> int:
        """Number of raw audio bytes buffered so far."""
        return self._audio_bytes_written

    @property
    def is_active(self) -> bool:
        """``True`` if the encryptor is started and not yet finalized/aborted."""
        return self._started and not self._finalized

    # ── Internals ─────────────────────────────────────────────────────────

    def _cleanup_tmp(self) -> None:
        """Remove the plaintext temp file if it still exists."""
        if self._tmp_plaintext_path is not None:
            try:
                self._tmp_plaintext_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._tmp_plaintext_path = None


# ── Convenience function ──────────────────────────────────────────────────────

def encrypt_audio_data(
    key: bytes,
    audio_data: bytes,
    metadata: dict,
    output_path: Union[str, Path],
) -> Path:
    """One-shot helper: encrypt *audio_data* to an ``.sna`` file.

    This is a thin wrapper around :class:`AudioEncryptor` for callers that
    already have all audio data in memory.

    Args:
        key: 32-byte AES-256 key.
        audio_data: Raw PCM16 audio bytes.
        metadata: Recording metadata dict.
        output_path: Destination ``.sna`` path.

    Returns:
        Path to the written file.
    """
    enc = AudioEncryptor(key=key, output_path=output_path)
    enc.start()
    enc.write_chunk(audio_data)
    return enc.finalize(metadata)
