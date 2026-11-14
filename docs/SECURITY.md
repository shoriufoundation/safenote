# SafeNote Architecture & Security Specification

## 1. System Overview

SafeNote is built using a clean layered architecture with strict separation of concerns:

```
SafeNote/
├── audio/          # Hardware device enumeration, recording streams, and in-memory player
├── crypto/         # AES-256-GCM encryption, decryption, key management, and binary file format
├── storage/        # SQLite metadata database and filesystem recording repository
├── ui/             # PySide6 modern UI widgets, pages, emergency hide, and tray integration
├── core/           # Configuration (QSettings), localization (TR/EN/AZ), and app orchestration
└── tests/          # Comprehensive automated unit and integration tests
```

---

## 2. Binary File Format Specification (`.sna` v1.0)

SafeNote Audio (`.sna`) files use an authenticated container format designed for privacy and tampering resistance:

```
+---------------+---------------+--------------------+------------------------+
|  MAGIC (4 B)  | VERSION (2 B) |    NONCE (12 B)    |  METADATA_LEN (4 B)    |
|   b"SNA\x01"  |    (1, 0)     |  AES-256-GCM Nonce |  Big-Endian uint32     |
+---------------+---------------+--------------------+------------------------+
|                      CIPHERTEXT (Variable length)                           |
|       Encrypted: JSON Metadata (METADATA_LEN bytes) || PCM16 Audio         |
+-----------------------------------------------------------------------------+
|                          GCM_TAG (16 Bytes)                                 |
|               AES-256-GCM Authentication Tag (Header + Ciphertext)          |
+-----------------------------------------------------------------------------+
```

### Authentication Guarantee:
- The entire 22-byte header (`MAGIC`, `VERSION`, `NONCE`, `METADATA_LEN`) is passed to `AESGCM.encrypt` as **Additional Authenticated Data (AAD)**.
- Any modification to header parameters, metadata, or ciphertext will result in authentication tag failure and immediate rejection (`WrongKeyError`).

---

## 3. Threat Model & Security Boundaries

### In Scope:
1. **Physical Loss of Storage Media:** Recordings on stolen drives or copied without the OS user's keyring access remain unreadable.
2. **File Tampering & Truncation:** Corrupted, truncated, or modified files are detected immediately and rejected prior to playback.
3. **Screen Privacy (Emergency Hide):** Instantly blinds the application with `Ctrl+Shift+H`, safe-stopping active recordings.

### Out of Scope / Honest Disclosures:
1. **Compromised Operating System:** An attacker with root, kernel, or active process inspection capabilities can dump memory or hook audio drivers.
2. **Lost Encryption Keys:** If the master encryption key is deleted from the OS Keyring and has not been backed up, recorded files are cryptographically unrecoverable.
