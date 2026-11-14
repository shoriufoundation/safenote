"""
SafeNote – Encrypted audio player.

Decrypts ``.sna`` files entirely in memory (no plaintext ever hits the
disk) and plays back the resulting PCM data through ``QAudioSink``.
"""

from __future__ import annotations

import enum
from typing import Optional

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QTimer, Signal
from PySide6.QtMultimedia import QAudioFormat, QAudioSink

from audio.formats import estimate_duration


class PlayerState(enum.Enum):
    """Possible states of the :class:`AudioPlayer`."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer(QObject):
    """Player for decrypted SafeNote ``.sna`` audio files.

    The encrypted file is decrypted into a ``QByteArray`` in memory; raw
    PCM-16 data is streamed to the default audio output via
    ``QAudioSink``.

    Signals
    -------
    playback_started()
        Emitted when playback begins (from stopped state).
    playback_paused()
        Emitted when playback is paused.
    playback_resumed()
        Emitted when playback resumes after a pause.
    playback_stopped()
        Emitted when playback is explicitly stopped.
    playback_finished()
        Emitted when the audio reaches the end of the buffer.
    position_changed(float)
        Fires periodically with the current position in seconds.
    duration_available(float)
        Emitted once after a file is loaded, with the total duration.
    error_occurred(str)
        Emitted on any error (decryption, playback, file I/O, …).
    """

    # ── Qt Signals ───────────────────────────────────────────────────
    playback_started = Signal()
    playback_paused = Signal()
    playback_resumed = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()
    position_changed = Signal(float)   # current position in seconds
    duration_available = Signal(float)  # total duration in seconds
    error_occurred = Signal(str)       # human-readable error message

    # ── Construction ─────────────────────────────────────────────────
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._state: PlayerState = PlayerState.STOPPED
        self._audio_sink: QAudioSink | None = None
        self._buffer: QBuffer | None = None
        self._pcm_data: QByteArray | None = None
        self._sample_rate: int = 44100
        self._channels: int = 1
        self._duration: float = 0.0
        self._volume: float = 1.0

        # Position-tracking timer (~20 updates / second)
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(50)
        self._position_timer.timeout.connect(self._emit_position)

    # ── Properties ───────────────────────────────────────────────────
    def get_duration(self) -> float:
        """Total duration in seconds of the loaded audio."""
        return self._duration

    def get_position(self) -> float:
        """Current playback position in seconds."""
        if self._buffer is None or self._pcm_data is None:
            return 0.0
        bytes_per_sample = 2  # 16-bit
        bytes_per_second = self._sample_rate * self._channels * bytes_per_sample
        if bytes_per_second == 0:
            return 0.0
        return self._buffer.pos() / bytes_per_second

    def is_playing(self) -> bool:
        """``True`` when audio is actively being played."""
        return self._state == PlayerState.PLAYING

    # ── Loading ──────────────────────────────────────────────────────
    def load_file(self, path: str, key: bytes) -> None:
        """Decrypt *path* and prepare the PCM data for playback.

        Parameters
        ----------
        path:
            Filesystem path to an encrypted ``.sna`` recording.
        key:
            256-bit decryption key (the same key used for recording).

        Raises / emits ``error_occurred`` on:
            * ``FileNotFoundError`` – file does not exist.
            * ``crypto.decryption.WrongKeyError`` – incorrect key.
            * ``crypto.decryption.CorruptedFileError`` – file is damaged.
        """
        # Stop anything currently playing
        self.stop()

        from pathlib import Path as _Path

        file_path = _Path(path)
        if not file_path.exists():
            msg = f"File not found: {path}"
            self.error_occurred.emit(msg)
            return

        try:
            from crypto.decryption import AudioDecryptor  # noqa: WPS433

            decryptor = AudioDecryptor(path=file_path, key=key)
            metadata, pcm_bytes = decryptor.decrypt()
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return

        # Extract format info from metadata
        self._sample_rate = int(metadata.get("sample_rate", 44100))
        self._channels = int(metadata.get("channels", 1))

        # Duration from metadata or calculated from PCM size
        self._duration = float(
            metadata.get(
                "duration_seconds",
                estimate_duration(len(pcm_bytes), self._sample_rate, self._channels),
            )
        )

        # Store PCM data in a QByteArray so QBuffer can wrap it
        self._pcm_data = QByteArray(pcm_bytes)

        self.duration_available.emit(self._duration)

    # ── Playback controls ────────────────────────────────────────────
    def play(self) -> None:
        """Start playback from the beginning (or current position)."""
        if self._pcm_data is None or self._pcm_data.isEmpty():
            self.error_occurred.emit("No audio loaded")
            return

        if self._state == PlayerState.PAUSED:
            self.resume()
            return

        # (Re)initialise the audio pipeline
        self._teardown_sink()

        fmt = QAudioFormat()
        fmt.setSampleRate(self._sample_rate)
        fmt.setChannelCount(self._channels)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self._audio_sink = QAudioSink(fmt, self)
        self._audio_sink.setVolume(self._volume)
        self._audio_sink.stateChanged.connect(self._on_sink_state_changed)

        self._buffer = QBuffer(self._pcm_data, self)
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)

        self._audio_sink.start(self._buffer)
        self._state = PlayerState.PLAYING
        self._position_timer.start()
        self.playback_started.emit()

    def pause(self) -> None:
        """Pause playback (can be resumed)."""
        if self._state != PlayerState.PLAYING or self._audio_sink is None:
            return
        self._audio_sink.suspend()
        self._state = PlayerState.PAUSED
        self._position_timer.stop()
        self.playback_paused.emit()

    def resume(self) -> None:
        """Resume after a pause."""
        if self._state != PlayerState.PAUSED or self._audio_sink is None:
            return
        self._audio_sink.resume()
        self._state = PlayerState.PLAYING
        self._position_timer.start()
        self.playback_resumed.emit()

    def stop(self) -> None:
        """Stop playback and reset position to zero."""
        if self._state == PlayerState.STOPPED:
            return
        self._position_timer.stop()
        self._teardown_sink()
        self._state = PlayerState.STOPPED
        self.playback_stopped.emit()

    def seek(self, position_seconds: float) -> None:
        """Seek to *position_seconds* within the loaded audio.

        Has no effect when nothing is loaded.
        """
        if self._buffer is None or self._pcm_data is None:
            return

        bytes_per_sample = 2
        block_align = self._channels * bytes_per_sample
        bytes_per_second = self._sample_rate * block_align
        target_byte = int(position_seconds * bytes_per_second)

        # Align to block boundary
        target_byte = (target_byte // block_align) * block_align

        # Clamp to valid range
        target_byte = max(0, min(target_byte, self._pcm_data.size()))
        self._buffer.seek(target_byte)

        self._emit_position()

    def set_volume(self, level: float) -> None:
        """Set output volume.

        Parameters
        ----------
        level:
            Volume from 0.0 (mute) to 1.0 (full).
        """
        self._volume = max(0.0, min(1.0, level))
        if self._audio_sink is not None:
            self._audio_sink.setVolume(self._volume)

    # ── Private helpers ──────────────────────────────────────────────
    def _emit_position(self) -> None:
        """Push the current position through the signal."""
        pos = self.get_position()
        self.position_changed.emit(pos)

        # Detect end-of-buffer
        if (
            self._buffer is not None
            and self._pcm_data is not None
            and self._buffer.pos() >= self._pcm_data.size()
            and self._state == PlayerState.PLAYING
        ):
            self._finish()

    def _on_sink_state_changed(self, new_state) -> None:
        """React to ``QAudioSink`` state transitions."""
        from PySide6.QtMultimedia import QAudio

        if new_state == QAudio.State.IdleState and self._state == PlayerState.PLAYING:
            # QAudioSink has drained its buffer
            self._finish()
        elif new_state == QAudio.State.StoppedState:
            if self._audio_sink is not None:
                err = self._audio_sink.error()
                if err != QAudio.Error.NoError:
                    self.error_occurred.emit(f"Audio output error: {err}")

    def _finish(self) -> None:
        """Handle natural end of playback."""
        self._position_timer.stop()
        self._teardown_sink()
        self._state = PlayerState.STOPPED
        self.playback_finished.emit()

    def _teardown_sink(self) -> None:
        """Stop and delete the audio sink and buffer."""
        if self._audio_sink is not None:
            self._audio_sink.stop()
            self._audio_sink.deleteLater()
            self._audio_sink = None
        if self._buffer is not None:
            if self._buffer.isOpen():
                self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None
