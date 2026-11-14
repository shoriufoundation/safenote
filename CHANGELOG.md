# Changelog

All notable changes to SafeNote will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0-dev] - 2026-11-14

### Added
- Initial development release
- Audio recording with AES-256-GCM encryption
- Custom .sna encrypted audio format (version 1.0)
- Built-in audio player with seek, volume, and timeline
- Recording library with search, sort, and filter
- Emergency Hide privacy feature (Ctrl+Shift+H)
- Dark and light theme support
- Localization: Turkish, English, Azerbaijani
- First-run configuration wizard
- System tray integration
- WAV export with unencrypted file warning
- OS-protected key storage via keyring
- SQLite recording metadata database
- Microphone device selection
- Configurable keyboard shortcuts
- PyInstaller Windows packaging

### Security
- AES-256-GCM authenticated encryption
- Unique nonce per recording
- Atomic file writes (no partial .sna files)
- In-memory-only decrypted audio during playback
- No telemetry, no cloud, no hidden network access
