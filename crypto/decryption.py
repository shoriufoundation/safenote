"""
AES-256-GCM decryption for SafeNote Audio (.sna) files.

This module reads ``.sna`` files produced by :mod:`crypto.encryption` and
returns the plaintext metadata dict and raw PCM audio bytes.

Custom exception hierarchy::

    SNAError
    ├── InvalidHeaderError    — magic / structural header problems
    ├── UnsupportedVersionError — version not understood by this build
    ├── CorruptedFileError    — truncation, bad tag, invalid JSON, etc.
    └── WrongKeyError         — GCM tag verification failed (wrong key)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .file_format import (
    HEADER_SIZE,
    MAX_METADATA_LENGTH,
    TAG_SIZE,
    SNAHeader,
    validate_header,
)

logger = logging.getLogger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────

class SNAError(Exception):
    """Base class for all SafeNote Audio file errors."""


class InvalidHeaderError(SNAError):
    """The file does not begin with a valid SNA header."""


class UnsupportedVersionError(SNAError):
    """The SNA file version is not supported by this build."""


class CorruptedFileError(SNAError):
    """The file appears truncated, has malformed metadata, or is otherwise
    structurally invalid."""


class WrongKeyError(SNAError):
    """GCM authentication failed — almost certainly the wrong key, or the
    ciphertext / tag has been tampered with."""


# ── Decryptor class ───────────────────────────────────────────────────────────

class AudioDecryptor:
    """Decrypt a ``.sna`` file and return metadata + raw audio.

    Usage::

        dec = AudioDecryptor(path="recording.sna", key=my_key)
        metadata, audio_bytes = dec.decrypt()

    Args:
        path: Path to the ``.sna`` file.
        key: 32-byte AES-256 key.
    """

    def __init__(self, path: Union[str, Path], key: bytes) -> None:
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        self._path: Path = Path(path)
        self._key: bytes = key

    # ── Public API ────────────────────────────────────────────────────────

    def decrypt(self) -> tuple[dict, bytes]:
        """Read, validate, and decrypt the SNA file.

        Returns:
            A ``(metadata, audio_bytes)`` tuple where *metadata* is a
            ``dict`` and *audio_bytes* is the raw PCM16 audio.

        Raises:
            InvalidHeaderError: If the magic bytes are wrong or the header
                                is too short.
            UnsupportedVersionError: If the file version cannot be read.
            CorruptedFileError: If the file is truncated, or the decrypted
                                metadata is not valid JSON.
            WrongKeyError: If GCM tag verification fails.
            FileNotFoundError: If the file does not exist.
        """
        raw = self._read_file()
        header = self._parse_header(raw)
        header_bytes = raw[:HEADER_SIZE]
        ciphertext, tag = self._extract_body(raw, header)
        plaintext = self._decrypt_blob(header.nonce, ciphertext, tag, associated_data=header_bytes)
        metadata, audio = self._split_plaintext(plaintext, header.metadata_length)
        return metadata, audio

    def validate(self) -> bool:
        """Quick header-only validation (does **not** decrypt).

        Returns:
            ``True`` if the header looks valid, ``False`` otherwise.
        """
        try:
            raw = self._read_file()
            header = self._parse_header(raw)
            # Also verify there's enough data for at least the tag
            body_len = len(raw) - HEADER_SIZE
            if body_len < TAG_SIZE:
                return False
            return True
        except SNAError:
            return False

    # ── Internals ─────────────────────────────────────────────────────────

    def _read_file(self) -> bytes:
        """Read the entire file into memory.

        Raises:
            FileNotFoundError: If the file does not exist.
            CorruptedFileError: If the file is too small for even a header.
        """
        if not self._path.exists():
            raise FileNotFoundError(f"SNA file not found: {self._path}")

        raw = self._path.read_bytes()
        if len(raw) < HEADER_SIZE + TAG_SIZE:
            raise CorruptedFileError(
                f"File too small ({len(raw)} bytes) — expected at least "
                f"{HEADER_SIZE + TAG_SIZE} bytes for header + tag"
            )
        return raw

    @staticmethod
    def _parse_header(raw: bytes) -> SNAHeader:
        """Parse and validate the SNA header.

        Raises:
            InvalidHeaderError: On bad magic.
            UnsupportedVersionError: On unsupported version.
        """
        try:
            header = SNAHeader.from_bytes(raw)
        except ValueError as exc:
            raise InvalidHeaderError(str(exc)) from exc

        if not header.is_valid_magic:
            raise InvalidHeaderError(
                f"Invalid SNA magic: {header.magic!r}"
            )
        if not header.is_supported_version:
            raise UnsupportedVersionError(
                f"Unsupported version {header.version_major}."
                f"{header.version_minor}"
            )
        if header.metadata_length > MAX_METADATA_LENGTH:
            raise CorruptedFileError(
                f"Metadata length {header.metadata_length} exceeds maximum "
                f"({MAX_METADATA_LENGTH})"
            )
        return header

    @staticmethod
    def _extract_body(raw: bytes, header: SNAHeader) -> tuple[bytes, bytes]:
        """Split the file into ciphertext and GCM tag.

        Returns:
            ``(ciphertext, tag)``

        Raises:
            CorruptedFileError: If the file is truncated.
        """
        body = raw[HEADER_SIZE:]
        if len(body) < TAG_SIZE:
            raise CorruptedFileError(
                f"File body too short ({len(body)} bytes); cannot extract "
                f"{TAG_SIZE}-byte GCM tag"
            )

        ciphertext = body[:-TAG_SIZE]
        tag = body[-TAG_SIZE:]
        return ciphertext, tag

    def _decrypt_blob(
        self, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes | None = None
    ) -> bytes:
        """Perform AES-256-GCM decryption.

        Raises:
            WrongKeyError: If the authentication tag is invalid.
        """
        aesgcm = AESGCM(self._key)
        # AESGCM.decrypt expects ciphertext ‖ tag
        ciphertext_with_tag = ciphertext + tag
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data)
        except InvalidTag as exc:
            raise WrongKeyError(
                "Decryption failed — the key is wrong or the file has been "
                "tampered with"
            ) from exc
        return plaintext

    @staticmethod
    def _split_plaintext(
        plaintext: bytes, metadata_length: int
    ) -> tuple[dict, bytes]:
        """Split decrypted plaintext into metadata dict and audio bytes.

        Raises:
            CorruptedFileError: If the plaintext is shorter than expected or
                                the metadata is not valid JSON.
        """
        if len(plaintext) < metadata_length:
            raise CorruptedFileError(
                f"Decrypted plaintext ({len(plaintext)} bytes) is shorter than "
                f"the declared metadata length ({metadata_length} bytes)"
            )

        metadata_bytes = plaintext[:metadata_length]
        audio_bytes = plaintext[metadata_length:]

        try:
            metadata = json.loads(metadata_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CorruptedFileError(
                f"Failed to parse metadata JSON: {exc}"
            ) from exc

        if not isinstance(metadata, dict):
            raise CorruptedFileError(
                f"Expected metadata to be a JSON object, got {type(metadata).__name__}"
            )

        return metadata, audio_bytes


# ── Convenience functions ─────────────────────────────────────────────────────

def decrypt_file(
    path: Union[str, Path], key: bytes
) -> tuple[dict, bytes]:
    """One-shot decryption of a ``.sna`` file.

    Args:
        path: Path to the ``.sna`` file.
        key: 32-byte AES-256 key.

    Returns:
        ``(metadata_dict, raw_audio_bytes)``

    Raises:
        InvalidHeaderError, UnsupportedVersionError, CorruptedFileError,
        WrongKeyError, FileNotFoundError — see :class:`AudioDecryptor`.
    """
    return AudioDecryptor(path=path, key=key).decrypt()


def validate_file(path: Union[str, Path]) -> bool:
    """Check whether *path* has a structurally valid SNA header.

    This does **not** require a key and does **not** attempt decryption.

    Returns:
        ``True`` if the header looks valid, ``False`` otherwise.
    """
    from .file_format import validate_file as _fmt_validate
    return _fmt_validate(path)
