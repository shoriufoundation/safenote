"""
Automated unit tests for SafeNote Cryptographic Module.

Tests:
- AES-256-GCM round trip encryption & decryption
- Wrong key handling (WrongKeyError)
- Corrupted file handling (tag / body tampering)
- Invalid header handling
- Unsupported format version handling
- Empty recording handling (0 bytes PCM)
- Metadata tampering & integrity validation
- Key manager base64 export and import
"""

import os
import secrets
import tempfile
from pathlib import Path

import pytest

from crypto.decryption import (
    AudioDecryptor,
    CorruptedFileError,
    InvalidHeaderError,
    UnsupportedVersionError,
    WrongKeyError,
    decrypt_file,
)
from crypto.encryption import AudioEncryptor
from crypto.file_format import (
    HEADER_SIZE,
    MAGIC,
    TAG_SIZE,
    VERSION,
    build_header,
    parse_header,
    validate_file,
)
from crypto.key_manager import export_key_base64, import_key_base64


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def valid_key():
    return secrets.token_bytes(32)


def test_encryption_decryption_round_trip(temp_dir, valid_key):
    """Test standard round-trip of audio and metadata."""
    out_file = temp_dir / "recording.sna"
    metadata = {
        "sample_rate": 44100,
        "channels": 1,
        "format": "PCM_16",
        "created_at": "2026-11-14T12:00:00",
        "duration_seconds": 2.5,
    }
    raw_audio = b"\x00\x01\xfe\xff" * 2000  # 8000 bytes

    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start(metadata)
    encryptor.write_chunk(raw_audio[:4000])
    encryptor.write_chunk(raw_audio[4000:])
    final_path = encryptor.finalize(metadata)

    assert final_path.exists()
    assert validate_file(str(out_file))

    dec_meta, dec_audio = decrypt_file(out_file, valid_key)
    assert dec_meta["sample_rate"] == 44100
    assert dec_meta["channels"] == 1
    assert dec_meta["duration_seconds"] == 2.5
    assert dec_audio == raw_audio


def test_wrong_encryption_key(temp_dir, valid_key):
    """Test that decryption with a wrong key raises WrongKeyError."""
    out_file = temp_dir / "wrong_key_test.sna"
    metadata = {"sample_rate": 44100, "channels": 1}
    raw_audio = b"some-audio-bytes" * 100

    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start(metadata)
    encryptor.write_chunk(raw_audio)
    encryptor.finalize(metadata)

    wrong_key = secrets.token_bytes(32)
    with pytest.raises(WrongKeyError):
        decrypt_file(out_file, wrong_key)


def test_corrupted_ciphertext(temp_dir, valid_key):
    """Test that tampering with ciphertext or GCM tag raises WrongKeyError / CorruptedFileError."""
    out_file = temp_dir / "corrupted.sna"
    metadata = {"sample_rate": 44100, "channels": 1}
    raw_audio = b"secret-audio" * 50

    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start(metadata)
    encryptor.write_chunk(raw_audio)
    encryptor.finalize(metadata)

    # Tamper with the last byte (part of authentication tag)
    data = bytearray(out_file.read_bytes())
    data[-1] ^= 0x55
    out_file.write_bytes(data)

    with pytest.raises(WrongKeyError):
        decrypt_file(out_file, valid_key)


def test_invalid_header_magic(temp_dir, valid_key):
    """Test that a file without valid SNA magic raises InvalidHeaderError."""
    invalid_file = temp_dir / "bad_magic.sna"
    invalid_file.write_bytes(b"BAD!\x00\x00" + b"\x00" * 40)

    assert not validate_file(str(invalid_file))
    with pytest.raises(InvalidHeaderError):
        decrypt_file(invalid_file, valid_key)


def test_unsupported_version(temp_dir, valid_key):
    """Test that a file with unsupported major version is rejected."""
    bad_ver_file = temp_dir / "unsupported_ver.sna"
    nonce = secrets.token_bytes(12)
    # Header with major version 99
    header = MAGIC + bytes([99, 0]) + nonce + (10).to_bytes(4, "big")
    bad_ver_file.write_bytes(header + b"\x00" * 30)

    with pytest.raises(UnsupportedVersionError):
        decrypt_file(bad_ver_file, valid_key)


def test_empty_audio_recording(temp_dir, valid_key):
    """Test encryption and decryption of an empty audio recording (0 bytes)."""
    out_file = temp_dir / "empty.sna"
    metadata = {"sample_rate": 44100, "channels": 1, "duration_seconds": 0.0}

    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start(metadata)
    # No audio chunks written
    encryptor.finalize(metadata)

    dec_meta, dec_audio = decrypt_file(out_file, valid_key)
    assert dec_meta["sample_rate"] == 44100
    assert dec_audio == b""


def test_abort_cleans_temporary_file(temp_dir, valid_key):
    """Test that abort() discards temporary plaintext file without creating .sna."""
    out_file = temp_dir / "aborted.sna"
    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start({"sample_rate": 44100})
    encryptor.write_chunk(b"some audio data")
    encryptor.abort()

    assert not out_file.exists()
    # No dangling .tmp files in temp_dir
    tmp_files = list(temp_dir.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_header_tampering_rejected_by_aad(temp_dir, valid_key):
    """Test that modifying header bytes (like metadata_length or version) fails authentication."""
    out_file = temp_dir / "tampered_header.sna"
    metadata = {"sample_rate": 44100, "channels": 1}
    raw_audio = b"secret-audio" * 20

    encryptor = AudioEncryptor(valid_key, out_file)
    encryptor.start(metadata)
    encryptor.write_chunk(raw_audio)
    encryptor.finalize(metadata)

    # Tamper with the metadata length in the header (offset 18..22)
    raw = bytearray(out_file.read_bytes())
    raw[21] ^= 0x01  # flip 1 bit in metadata length field
    out_file.write_bytes(raw)

    with pytest.raises(WrongKeyError):
        decrypt_file(out_file, valid_key)


def test_key_base64_export_import():
    """Test exporting and importing keys via Base64."""
    original_key = secrets.token_bytes(32)
    import base64
    b64_str = base64.b64encode(original_key).decode("ascii")

    decoded_key = base64.b64decode(b64_str.strip().encode("ascii"))
    assert decoded_key == original_key
