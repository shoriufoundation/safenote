"""
SafeNote Audio (.sna) file format definition.

Binary layout:
    ┌──────────────────────────────────────────────────────────┐
    │  MAGIC            4 bytes   b"SNA\\x01"                  │
    │  VERSION          2 bytes   (major, minor) — (1, 0)     │
    │  NONCE           12 bytes   AES-256-GCM nonce           │
    │  METADATA_LEN     4 bytes   big-endian uint32           │
    ├──────────────────────────────────────────────────────────┤
    │  ENCRYPTED_BLOB   variable  see below                   │
    │  GCM_TAG         16 bytes   authentication tag          │
    └──────────────────────────────────────────────────────────┘

The ENCRYPTED_BLOB is a single AES-256-GCM ciphertext covering:
    metadata_json_bytes ‖ raw_audio_bytes

METADATA_LEN stores the length of the *plaintext* metadata JSON so
the decryptor knows where to split after decryption.  It is written
in the clear header (authenticated implicitly because any tampering
will cause the GCM tag to fail).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Union

# ── Format constants ──────────────────────────────────────────────────────────

MAGIC: bytes = b"SNA\x01"
"""4-byte magic number identifying an SNA file."""

VERSION_MAJOR: int = 1
VERSION_MINOR: int = 0
VERSION: tuple[int, int] = (VERSION_MAJOR, VERSION_MINOR)
"""Current format version as (major, minor)."""

MAGIC_SIZE: int = len(MAGIC)               # 4
VERSION_SIZE: int = 2                       # 2 bytes (major, minor)
NONCE_SIZE: int = 12                        # AES-256-GCM recommended nonce
METADATA_LENGTH_SIZE: int = 4              # uint32 big-endian
TAG_SIZE: int = 16                          # GCM authentication tag

HEADER_SIZE: int = MAGIC_SIZE + VERSION_SIZE + NONCE_SIZE + METADATA_LENGTH_SIZE
"""Total clear-header size: 4 + 2 + 12 + 4 = 22 bytes."""

# Sanity-check at import time
assert HEADER_SIZE == 22, f"Expected HEADER_SIZE=22, got {HEADER_SIZE}"

# Maximum allowed metadata length (1 MiB) to guard against corrupt files.
MAX_METADATA_LENGTH: int = 1 * 1024 * 1024

# File extension
FILE_EXTENSION: str = ".sna"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SNAHeader:
    """Parsed representation of an SNA file header."""

    magic: bytes
    version_major: int
    version_minor: int
    nonce: bytes
    metadata_length: int

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def version(self) -> tuple[int, int]:
        """Return version as a ``(major, minor)`` tuple."""
        return (self.version_major, self.version_minor)

    @property
    def is_valid_magic(self) -> bool:
        """Return ``True`` if the magic bytes match the SNA format."""
        return self.magic == MAGIC

    @property
    def is_supported_version(self) -> bool:
        """Return ``True`` if the version is supported by this reader."""
        return self.version_major == VERSION_MAJOR

    # ── Factory ───────────────────────────────────────────────────────────

    @classmethod
    def from_bytes(cls, data: bytes) -> "SNAHeader":
        """Parse an :class:`SNAHeader` from the first *HEADER_SIZE* bytes.

        Args:
            data: At least *HEADER_SIZE* bytes of raw data.

        Raises:
            ValueError: If *data* is too short to contain a valid header.
        """
        if len(data) < HEADER_SIZE:
            raise ValueError(
                f"Data too short for SNA header: need {HEADER_SIZE} bytes, "
                f"got {len(data)}"
            )

        offset = 0
        magic = data[offset : offset + MAGIC_SIZE]
        offset += MAGIC_SIZE

        version_major = data[offset]
        version_minor = data[offset + 1]
        offset += VERSION_SIZE

        nonce = data[offset : offset + NONCE_SIZE]
        offset += NONCE_SIZE

        (metadata_length,) = struct.unpack_from(">I", data, offset)

        return cls(
            magic=magic,
            version_major=version_major,
            version_minor=version_minor,
            nonce=nonce,
            metadata_length=metadata_length,
        )

    @classmethod
    def from_file(cls, source: Union[str, Path, BinaryIO]) -> "SNAHeader":
        """Read and parse an :class:`SNAHeader` from a file path or open file.

        Args:
            source: A filesystem path or a readable binary stream positioned
                    at the start of the SNA data.

        Raises:
            ValueError: If the file is too short or the header is malformed.
            FileNotFoundError: If *source* is a path that does not exist.
        """
        if isinstance(source, (str, Path)):
            path = Path(source)
            with path.open("rb") as fh:
                data = fh.read(HEADER_SIZE)
        else:
            data = source.read(HEADER_SIZE)

        return cls.from_bytes(data)


# ── Helper functions ──────────────────────────────────────────────────────────

def build_header(nonce: bytes, metadata_length: int) -> bytes:
    """Build the 22-byte clear header for an SNA file.

    Args:
        nonce: 12-byte GCM nonce.
        metadata_length: Length of the *plaintext* metadata JSON in bytes.

    Returns:
        The fully assembled header as ``bytes``.

    Raises:
        ValueError: If *nonce* is the wrong size or *metadata_length* is
                    negative / too large.
    """
    if len(nonce) != NONCE_SIZE:
        raise ValueError(
            f"Nonce must be exactly {NONCE_SIZE} bytes, got {len(nonce)}"
        )
    if metadata_length < 0:
        raise ValueError("metadata_length must be non-negative")
    if metadata_length > MAX_METADATA_LENGTH:
        raise ValueError(
            f"metadata_length ({metadata_length}) exceeds maximum "
            f"({MAX_METADATA_LENGTH})"
        )

    header = bytearray()
    header.extend(MAGIC)
    header.append(VERSION_MAJOR)
    header.append(VERSION_MINOR)
    header.extend(nonce)
    header.extend(struct.pack(">I", metadata_length))
    assert len(header) == HEADER_SIZE
    return bytes(header)


def validate_header(header: SNAHeader) -> None:
    """Validate an :class:`SNAHeader`, raising on any problem.

    Raises:
        InvalidHeaderError: (imported from decryption) — but since this
            module should be dependency-free, we raise ``ValueError``
            with descriptive messages here.
    """
    if not header.is_valid_magic:
        raise ValueError(
            f"Invalid SNA magic: expected {MAGIC!r}, got {header.magic!r}"
        )
    if not header.is_supported_version:
        raise ValueError(
            f"Unsupported SNA version {header.version_major}.{header.version_minor}; "
            f"this build supports version {VERSION_MAJOR}.x"
        )
    if header.metadata_length > MAX_METADATA_LENGTH:
        raise ValueError(
            f"Metadata length {header.metadata_length} exceeds maximum "
            f"({MAX_METADATA_LENGTH})"
        )


def parse_header(data: bytes) -> SNAHeader:
    """Parse an :class:`SNAHeader` from raw header bytes."""
    return SNAHeader.from_bytes(data)


def validate_file(path: Union[str, Path]) -> bool:
    """Quick check: does *path* look like a valid SNA file?

    Returns:
        ``True`` if the header is present and valid, ``False`` otherwise.
    """
    try:
        header = SNAHeader.from_file(path)
        validate_header(header)
        return True
    except (ValueError, FileNotFoundError, OSError):
        return False
