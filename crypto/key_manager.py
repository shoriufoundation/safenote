"""
Key management for SafeNote.

Encryption keys are stored in the operating-system credential store via the
``keyring`` library (Windows Credential Locker, macOS Keychain, or
freedesktop Secret Service on Linux).  This keeps the key material protected
by the user's OS login session — SafeNote never writes raw keys to disk.

Key format: 256-bit (32 bytes), generated with :func:`secrets.token_bytes`.
When stored in keyring the key is base64-encoded for safe text transport.
"""

from __future__ import annotations

import base64
import logging
import secrets

import keyring

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

APP_NAME: str = "SafeNote"
"""Service / application name used as the keyring namespace."""

KEY_NAME: str = "audio-encryption-key"
"""Account / credential name under which the key is stored."""

KEY_SIZE_BYTES: int = 32
"""AES-256 requires a 256-bit (32-byte) key."""


# ── Public API ────────────────────────────────────────────────────────────────

def key_exists() -> bool:
    """Return ``True`` if an encryption key is already stored in the keyring."""
    try:
        stored = keyring.get_password(APP_NAME, KEY_NAME)
        return stored is not None
    except keyring.errors.KeyringError:
        logger.exception("Failed to query keyring")
        return False


def get_or_create_key() -> bytes:
    """Retrieve the existing encryption key, or generate and store a new one.

    Returns:
        The 32-byte raw encryption key.

    Raises:
        keyring.errors.KeyringError: If keyring access fails.
        ValueError: If the stored key is corrupt (wrong length after decode).
    """
    stored = keyring.get_password(APP_NAME, KEY_NAME)

    if stored is not None:
        key = base64.b64decode(stored)
        if len(key) != KEY_SIZE_BYTES:
            raise ValueError(
                f"Stored key has wrong length: expected {KEY_SIZE_BYTES}, "
                f"got {len(key)}.  The keyring entry may be corrupt."
            )
        logger.debug("Loaded existing encryption key from keyring")
        return key

    # Generate a fresh key
    key = secrets.token_bytes(KEY_SIZE_BYTES)
    encoded = base64.b64encode(key).decode("ascii")
    keyring.set_password(APP_NAME, KEY_NAME, encoded)
    logger.info("Generated and stored new encryption key in keyring")
    return key


def delete_key() -> None:
    """Delete the encryption key from the keyring.

    .. warning::
        This is **irreversible**.  Any files encrypted with this key will
        become permanently unrecoverable unless a backup was made with
        :func:`export_key_base64`.

    Raises:
        keyring.errors.KeyringError: If keyring access fails.
        keyring.errors.PasswordDeleteError: If the key does not exist.
    """
    keyring.delete_password(APP_NAME, KEY_NAME)
    logger.warning("Encryption key deleted from keyring")


def export_key_base64() -> str:
    """Export the current encryption key as a URL-safe base64 string.

    This is intended for user-initiated backups.  The string should be
    stored securely (e.g. in a password manager or printed on paper kept
    in a safe location).

    Returns:
        Base64-encoded key string.

    Raises:
        KeyError: If no key is stored in the keyring.
    """
    stored = keyring.get_password(APP_NAME, KEY_NAME)
    if stored is None:
        raise KeyError("No encryption key found in keyring — nothing to export")
    return stored


def import_key_base64(encoded: str) -> None:
    """Import a key from a base64-encoded string and store it in the keyring.

    If a key already exists it will be **overwritten**.

    Args:
        encoded: Base64-encoded 32-byte key (as produced by
                 :func:`export_key_base64`).

    Raises:
        ValueError: If *encoded* does not decode to exactly 32 bytes.
        keyring.errors.KeyringError: If keyring access fails.
    """
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError(f"Invalid base64 encoding: {exc}") from exc

    if len(raw) != KEY_SIZE_BYTES:
        raise ValueError(
            f"Decoded key has wrong length: expected {KEY_SIZE_BYTES} bytes, "
            f"got {len(raw)}"
        )

    keyring.set_password(APP_NAME, KEY_NAME, encoded)
    logger.info("Imported encryption key into keyring")
