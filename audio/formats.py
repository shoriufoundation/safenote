"""
SafeNote – Audio format utilities.

Helper functions for PCM-16 / WAV conversion that operate entirely
in-memory.  No temporary files are ever written to disk.
"""

from __future__ import annotations

import struct


def get_wav_header(
    data_size: int,
    sample_rate: int,
    channels: int,
    bits_per_sample: int = 16,
) -> bytes:
    """Generate a canonical 44-byte RIFF/WAV header.

    Parameters
    ----------
    data_size:
        Length of the raw PCM data in bytes (the ``data`` chunk size).
    sample_rate:
        Samples per second (e.g. 44 100).
    channels:
        Number of audio channels (1 = mono, 2 = stereo).
    bits_per_sample:
        Bit depth per sample (default 16).

    Returns
    -------
    bytes
        A 44-byte WAV header ready to be prepended to PCM data.
    """
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)
    # RIFF chunk size = 36 + data_size
    riff_size = 36 + data_size

    header = struct.pack(
        "<4sI4s"     # RIFF header
        "4sIHHIIHH"  # fmt  sub-chunk
        "4sI",       # data sub-chunk header
        b"RIFF",
        riff_size,
        b"WAVE",
        b"fmt ",
        16,                # fmt chunk size (PCM)
        1,                 # audio format  (1 = PCM)
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header


def pcm16_to_wav(
    pcm_data: bytes,
    sample_rate: int,
    channels: int,
) -> bytes:
    """Wrap raw signed-16-bit PCM data in a WAV container.

    The entire result is built in memory and returned as ``bytes``.

    Parameters
    ----------
    pcm_data:
        Raw PCM audio (signed 16-bit little-endian).
    sample_rate:
        Samples per second.
    channels:
        Number of audio channels.

    Returns
    -------
    bytes
        A complete WAV file as a bytes object.
    """
    header = get_wav_header(len(pcm_data), sample_rate, channels)
    return header + pcm_data


def estimate_duration(
    data_size: int,
    sample_rate: int,
    channels: int,
    bits_per_sample: int = 16,
) -> float:
    """Estimate playback duration from raw PCM data size.

    Parameters
    ----------
    data_size:
        Length of the PCM data in bytes.
    sample_rate:
        Samples per second.
    channels:
        Number of audio channels.
    bits_per_sample:
        Bit depth per sample (default 16).

    Returns
    -------
    float
        Estimated duration in seconds.  Returns ``0.0`` when any
        parameter would cause a division-by-zero.
    """
    bytes_per_sample = bits_per_sample // 8
    denominator = sample_rate * channels * bytes_per_sample
    if denominator == 0:
        return 0.0
    return data_size / denominator
