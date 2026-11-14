"""
Automated unit tests for SafeNote Audio Module.

Tests:
- PCM16 to WAV conversion
- Duration estimation from byte lengths
- Audio player state transitions
- Audio player data loading and decryption
- Recorder configuration and lifecycle with mocked audio backend
"""

import os
import secrets
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from audio.formats import estimate_duration, get_wav_header, pcm16_to_wav
from audio.player import AudioPlayer, PlayerState
from audio.recorder import AudioRecorder
from crypto.encryption import AudioEncryptor


def test_pcm16_to_wav_conversion():
    """Test generating WAV byte buffers from raw PCM16."""
    sample_rate = 44100
    channels = 1
    pcm_data = b"\x12\x34" * 1000  # 2000 bytes = 1000 samples

    wav_bytes = pcm16_to_wav(pcm_data, sample_rate, channels)
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes
    assert b"fmt " in wav_bytes
    assert b"data" in wav_bytes
    assert len(wav_bytes) == len(pcm_data) + 44  # Standard 44-byte WAV header


def test_estimate_duration():
    """Test duration estimation from raw bytes."""
    sample_rate = 44100
    channels = 1
    # 44100 samples * 2 bytes/sample * 1 channel = 88200 bytes per second
    one_second_bytes = 44100 * 2 * 1
    assert estimate_duration(one_second_bytes, sample_rate, channels) == 1.0
    assert estimate_duration(one_second_bytes * 5, sample_rate, channels) == 5.0


def test_player_lifecycle(qapp):
    """Test AudioPlayer state machine and file loading."""
    player = AudioPlayer()
    assert not player.is_playing()

    key = secrets.token_bytes(32)
    with tempfile.TemporaryDirectory() as td:
        sna_path = Path(td) / "test_player.sna"
        metadata = {
            "sample_rate": 44100,
            "channels": 1,
            "format": "PCM_16",
            "duration_seconds": 0.5,
        }
        pcm_bytes = b"\x00\x00" * int(44100 * 0.5)

        enc = AudioEncryptor(key, sna_path)
        enc.start()
        enc.write_chunk(pcm_bytes)
        enc.finalize(metadata)

        # Load file into player
        player.load_file(str(sna_path), key)
        assert player.get_duration() == 0.5
        assert player._pcm_data is not None
        assert player._pcm_data.size() == len(pcm_bytes)

        # Volume control
        player.set_volume(0.8)
        assert player._volume == 0.8


def test_recorder_mock_lifecycle(qapp):
    """Test AudioRecorder lifecycle with sounddevice mocked."""
    recorder = AudioRecorder()
    assert not recorder.is_recording

    key = secrets.token_bytes(32)
    with tempfile.TemporaryDirectory() as td:
        with patch("sounddevice.RawInputStream") as mock_stream_cls:
            mock_stream = MagicMock()
            mock_stream_cls.return_value = mock_stream

            started = recorder.start(storage_dir=td, key=key)
            assert started is True
            assert recorder.is_recording is True
            assert mock_stream.start.called

            # Simulate stopping
            saved_path = recorder.stop()
            assert not recorder.is_recording
            assert saved_path is not None
            assert Path(saved_path).exists()
