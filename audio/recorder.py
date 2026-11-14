"""
SafeNote – Thread-safe audio recorder with real-time encryption.

Records audio from a microphone via ``sounddevice`` and streams the
captured PCM-16 data through ``crypto.encryption.AudioEncryptor`` so
that no plaintext audio ever touches the disk.
"""

from __future__ import annotations

import queue
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal


class AudioRecorder(QObject):
    """Thread-safe audio recorder with real-time encryption.

    Signals
    -------
    recording_started()
        Emitted once the audio stream is open and capturing.
    recording_stopped(str)
        Emitted after a successful stop; carries the output file path.
    recording_error(str)
        Emitted when a non-fatal or fatal error occurs.
    duration_updated(float)
        Fires ~10 times / second with the elapsed recording time in
        seconds.
    level_updated(float)
        Fires per audio callback with a normalised VU level (0.0–1.0).
    device_disconnected()
        Emitted when the audio device reports a critical error suggesting
        disconnection.
    """

    # ── Qt Signals ───────────────────────────────────────────────────
    recording_started = Signal()
    recording_stopped = Signal(str)   # output file path
    recording_error = Signal(str)     # human-readable error message
    duration_updated = Signal(float)  # elapsed seconds
    level_updated = Signal(float)     # audio level 0.0 – 1.0
    device_disconnected = Signal()

    # ── Construction ─────────────────────────────────────────────────
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording: bool = False
        self._stream: sd.RawInputStream | None = None
        self._worker: threading.Thread | None = None
        self._audio_queue: queue.SimpleQueue[bytes | None] = queue.SimpleQueue()
        self._output_path: Path | None = None
        self._error: str | None = None
        self._start_time: float | None = None
        self._duration: float = 0.0
        self._sample_rate: int = 44100
        self._channels: int = 1
        self._device_id: int | None = None
        self._timer_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ── Public properties ────────────────────────────────────────────
    @property
    def is_recording(self) -> bool:
        """``True`` while audio is being captured."""
        return self._recording

    @property
    def duration(self) -> float:
        """Elapsed recording time in seconds."""
        return self._duration

    @property
    def error(self) -> str | None:
        """Last error message, or ``None``."""
        return self._error

    # ── Configuration ────────────────────────────────────────────────
    def configure(
        self,
        sample_rate: int = 44100,
        channels: int = 1,
        device_id: int | None = None,
    ) -> None:
        """Set recording parameters.

        Has no effect while a recording is in progress.

        Parameters
        ----------
        sample_rate:
            Samples per second (default 44 100).
        channels:
            Number of input channels (default 1 – mono).
        device_id:
            PortAudio device index, or ``None`` for the system default.
        """
        if self._recording:
            return
        self._sample_rate = sample_rate
        self._channels = channels
        self._device_id = device_id

    # ── Audio callback (runs on the PortAudio thread) ────────────────
    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio block.

        Pushes raw bytes into ``_audio_queue`` and emits a VU level.
        """
        if status:
            status_str = str(status).lower()
            if "input overflow" not in status_str:
                self._error = str(status)
                self.recording_error.emit(str(status))
                # Heuristic: assume device gone if we see certain errors
                if "device" in status_str or "unavailable" in status_str:
                    self.device_disconnected.emit()

        self._audio_queue.put(bytes(indata))

        # VU level – mean absolute value of signed-16-bit samples
        audio_data = np.frombuffer(bytes(indata), dtype=np.int16)
        if len(audio_data) > 0:
            level = float(np.abs(audio_data).mean()) / 32768.0
            self.level_updated.emit(min(level, 1.0))

    # ── Duration timer (background thread) ───────────────────────────
    def _duration_timer(self) -> None:
        """Periodically update ``_duration`` and emit ``duration_updated``."""
        while self._recording:
            time.sleep(0.1)
            if self._start_time is not None and self._recording:
                self._duration = time.time() - self._start_time
                self.duration_updated.emit(self._duration)

    # ── Encryption worker (background thread) ────────────────────────
    def _encryption_worker(self, path: Path, key: bytes) -> None:
        """Drain ``_audio_queue`` and write encrypted chunks via
        ``AudioEncryptor``.
        """
        from crypto.encryption import AudioEncryptor  # noqa: WPS433

        encryptor = AudioEncryptor(key, path)
        metadata: dict = {
            "sample_rate": self._sample_rate,
            "channels": self._channels,
            "format": "PCM_16",
            "created_at": datetime.now().isoformat(),
        }

        try:
            encryptor.start(metadata)

            while True:
                chunk = self._audio_queue.get()
                if chunk is None:
                    break
                encryptor.write_chunk(chunk)

            # Record final duration before sealing the file
            metadata["duration_seconds"] = self._duration
            encryptor.finalize(metadata)

        except Exception as exc:
            self._error = str(exc)
            encryptor.abort()
            self.recording_error.emit(str(exc))

    # ── Public interface ─────────────────────────────────────────────
    def start(
        self,
        storage_dir: str | Path | None = None,
        key: bytes | None = None,
    ) -> bool:
        """Begin recording.

        Parameters
        ----------
        storage_dir:
            Directory for the encrypted output file.  Created if absent.
            Defaults to ``~/SafeNote/Recordings``.
        key:
            256-bit encryption key.  When ``None`` the key is obtained
            automatically from ``crypto.key_manager``.

        Returns
        -------
        bool
            ``True`` if recording started successfully.
        """
        with self._lock:
            if self._recording:
                return False

        self._error = None
        self._audio_queue = queue.SimpleQueue()
        self._duration = 0.0

        # ---- output path ------------------------------------------------
        if storage_dir is None:
            storage_dir = Path.home() / "SafeNote" / "Recordings"
        storage_dir = Path(storage_dir)
        storage_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.sna"
        self._output_path = storage_dir / filename

        # ---- encryption key ----------------------------------------------
        if key is None:
            from crypto.key_manager import get_or_create_key  # noqa: WPS433
            key = get_or_create_key()

        # ---- encryption worker -------------------------------------------
        self._worker = threading.Thread(
            target=self._encryption_worker,
            args=(self._output_path, key),
            daemon=True,
        )
        self._worker.start()

        # ---- open audio stream -------------------------------------------
        try:
            kwargs: dict = {
                "samplerate": self._sample_rate,
                "channels": self._channels,
                "dtype": "int16",
                "callback": self._audio_callback,
            }
            if self._device_id is not None:
                kwargs["device"] = self._device_id

            self._stream = sd.RawInputStream(**kwargs)
            self._stream.start()

            self._recording = True
            self._start_time = time.time()

            # Duration timer
            self._timer_thread = threading.Thread(
                target=self._duration_timer, daemon=True,
            )
            self._timer_thread.start()

            self.recording_started.emit()
            return True

        except Exception as exc:
            self._error = str(exc)
            # Shut down the encryption worker cleanly
            self._audio_queue.put(None)
            self._worker.join(timeout=5)
            self._stream = None
            self.recording_error.emit(str(exc))
            return False

    def stop(self) -> str | None:
        """Stop recording and finalise the encrypted file.

        Returns
        -------
        str or None
            Path to the saved ``.sna`` file, or ``None`` if nothing was
            being recorded.

        Raises
        ------
        RuntimeError
            If an error occurred during recording or encryption.
        """
        with self._lock:
            if not self._recording:
                return None
            self._recording = False

        # ---- close audio stream ------------------------------------------
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass
        finally:
            self._stream = None
            # Sentinel so the encryption worker exits its loop
            self._audio_queue.put(None)

        # ---- wait for helper threads to finish ---------------------------
        if self._timer_thread is not None:
            self._timer_thread.join(timeout=2)
            self._timer_thread = None

        if self._worker is not None:
            self._worker.join(timeout=10)
            self._worker = None

        # ---- handle errors -----------------------------------------------
        if self._error:
            # Remove partial file on failure
            if self._output_path and self._output_path.exists():
                try:
                    self._output_path.unlink()
                except Exception:
                    pass
            raise RuntimeError(self._error)

        path = str(self._output_path) if self._output_path else None
        self.recording_stopped.emit(path or "")
        return path

    def cleanup(self) -> None:
        """Ensure all resources are released.

        Safe to call multiple times.  If a recording is in progress it
        is stopped first.
        """
        if self._recording:
            try:
                self.stop()
            except RuntimeError:
                pass
