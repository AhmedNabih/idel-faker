"""Seconds since the last real keyboard/mouse input, via GetLastInputInfo."""

import ctypes
from ctypes import wintypes


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def seconds_since_last_input() -> float:
    """Return seconds elapsed since the last keyboard or mouse input event."""
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError()
    tick_count = ctypes.windll.kernel32.GetTickCount()
    # GetTickCount and dwTime are unsigned 32-bit ms counters; mask handles wrap.
    elapsed_ms = (tick_count - info.dwTime) & 0xFFFFFFFF
    return elapsed_ms / 1000.0
