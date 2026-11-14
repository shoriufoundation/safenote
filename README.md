# SafeNote 🛡️

**Your safety. Your privacy. Your choice.**

SafeNote is an offline-first, privacy-focused desktop audio recording application built with Python and PySide6. It is designed to record, store, and play back audio with robust AES-256-GCM authenticated encryption while ensuring complete user transparency and screen privacy.

---

## 🔒 Core Privacy & Security Principles

- **Offline-First & Zero Telemetry:** SafeNote does not send any telemetry, usage analytics, or error logs over the network. It requires no user account or cloud service.
- **Authenticated Encryption (AES-256-GCM):** Audio data and metadata are encrypted using AES-256 in Galois/Counter Mode with a unique 96-bit nonce per recording. Clear headers are bound to the ciphertext as Additional Authenticated Data (AAD) to prevent tampering.
- **OS-Protected Key Storage:** Encryption keys are stored in the operating system's credential store (Windows Credential Manager via Keyring). Keys can be safely backed up and restored via Base64 export/import.
- **In-Memory Audio Playback:** Decrypted audio streams exist exclusively in RAM during playback and are never written to disk as plaintext files.
- **Atomic Writes:** Encrypted files are streamed to temporary files and atomically renamed upon successful completion and verification, preventing corrupted or incomplete files from being mistaken for valid recordings.
- **Emergency Hide:** A dedicated screen privacy control (`Ctrl+Shift+H`) immediately replaces sensitive application content with a neutral locked screen and safely finalizes any active recording without hiding operating-system microphone indicators.
- **Honest Security Boundaries:** SafeNote protects data at rest against unauthorized access and offline extraction. It does not claim protection against kernel-level malware or physical compromise with full administrative access to an unlocked session.

---

## ✨ Features

- **Audio Recording:**
  - Microphone device selection with live device detection.
  - Configurable sampling rates (16 kHz, 22.05 kHz, 44.1 kHz, 48 kHz) and channels (Mono / Stereo).
  - Real-time VU level meter and duration counter.
  - Transparent recording status indicator banners and system tray badges.
- **Audio Playback:**
  - Decrypts directly into memory with zero disk footprint.
  - Interactive timeline seek slider with scrub preview.
  - Play, pause, resume, stop, and quick jump controls (±5s).
  - Volume slider and mute toggle.
- **Recording Library:**
  - SQLite metadata database with WAL mode for concurrency.
  - Search by recording title and notes.
  - Rename recordings and delete with confirmation dialogs.
  - Explicit WAV export with unencrypted file warning.
- **Localization:**
  - Complete, native translations for **Turkish (Türkçe)**, **English**, and **Azerbaijani (Azərbaycanca)**.
  - Dynamic runtime language switching without restarting.
- **Themes & UI/UX:**
  - Modern, responsive Dark and Light themes.
  - Sidebar navigation with clean page stacking.
  - First-run configuration wizard for onboarding.
  - System tray icon with active recording alerts.

---

## 🚀 Installation & Development Setup

### Requirements
- Python 3.10+ (tested on Python 3.14 on Windows 10/11)
- Windows 10 / Windows 11 (Linux and macOS support planned)

### Running from Source
```powershell
# Navigate to project directory
cd SafeNote

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run SafeNote
python main.py
```

### Running Automated Tests
```powershell
pytest -v
```

---

## 📦 Building Standalone Executable (Windows)

SafeNote includes PyInstaller build scripts for creating a standalone Windows executable:

```powershell
# Build single-folder distribution
python build.py
```

The resulting binary will be located in `dist/SafeNote/SafeNote.exe`.

---

## 📄 License & Organization

- **Organization:** Shoriu Foundation
- **Version:** 0.1.0-dev
- **License:** DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE (WTFPL 2)
