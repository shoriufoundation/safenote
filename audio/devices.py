"""
SafeNote – Microphone device management.

Provides utilities for discovering, querying, and validating audio input
devices via the ``sounddevice`` library.
"""

from __future__ import annotations

from typing import Optional

import sounddevice as sd


def list_input_devices() -> list[dict]:
    """Return a list of available audio input devices.

    Each entry is a dict with the keys:

    * ``id`` – integer device index used by sounddevice / PortAudio
    * ``name`` – human-readable device name
    * ``channels`` – maximum number of input channels
    * ``default_samplerate`` – default sample rate reported by the driver

    Devices with zero input channels are excluded.
    """
    devices: list[dict] = []
    try:
        all_devices = sd.query_devices()
    except sd.PortAudioError:
        return devices

    # sd.query_devices() returns a single DeviceInfo dict when only one
    # device exists, or a DeviceList (list-like) otherwise.
    if isinstance(all_devices, dict):
        all_devices = [all_devices]

    for idx, dev in enumerate(all_devices):
        max_inputs = dev.get("max_input_channels", 0)
        if max_inputs > 0:
            devices.append(
                {
                    "id": idx,
                    "name": dev.get("name", f"Device {idx}"),
                    "channels": max_inputs,
                    "default_samplerate": dev.get("default_samplerate", 44100.0),
                }
            )

    return devices


def get_default_input_device() -> Optional[dict]:
    """Return info for the system's default input device, or ``None``.

    Returns ``None`` when no default input device is configured or when
    PortAudio is not available.
    """
    try:
        default_idx = sd.default.device[0]  # (input, output) tuple
        if default_idx is None or default_idx < 0:
            raise sd.PortAudioError("No default input device")
        return get_device_info(default_idx)
    except (sd.PortAudioError, IndexError, TypeError):
        # Fallback: pick the first available input device
        devices = list_input_devices()
        return devices[0] if devices else None


def is_device_available(device_id: int) -> bool:
    """Check whether *device_id* refers to a usable input device.

    Returns ``False`` for non-existent indices or output-only devices.
    """
    try:
        info = sd.query_devices(device_id)
        return info.get("max_input_channels", 0) > 0
    except (sd.PortAudioError, ValueError, IndexError):
        return False


def get_device_info(device_id: int) -> dict:
    """Return a normalised info dict for the given *device_id*.

    Raises ``ValueError`` when the device does not exist or has no input
    channels.
    """
    try:
        raw = sd.query_devices(device_id)
    except (sd.PortAudioError, ValueError, IndexError) as exc:
        raise ValueError(f"Device {device_id} not found: {exc}") from exc

    max_inputs = raw.get("max_input_channels", 0)
    if max_inputs <= 0:
        raise ValueError(
            f"Device {device_id} ({raw.get('name', '?')}) has no input channels"
        )

    return {
        "id": device_id,
        "name": raw.get("name", f"Device {device_id}"),
        "channels": max_inputs,
        "default_samplerate": raw.get("default_samplerate", 44100.0),
    }
