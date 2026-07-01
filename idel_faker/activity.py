"""Invisible input injection and system-awake control via ctypes SendInput."""

import ctypes
from ctypes import wintypes

# --- SendInput structures ---
ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_MOVE = 0x0001

VK_F15 = 0x7E

# SetThreadExecutionState flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _send(*inputs: _INPUT) -> None:
    n = len(inputs)
    array = (_INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, ctypes.byref(array), ctypes.sizeof(_INPUT))


def send_f15() -> None:
    """Inject an F15 key down + up. Invisible; no-op in virtually every app."""
    down = _INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=_KEYBDINPUT(wVk=VK_F15)))
    up = _INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUTUNION(ki=_KEYBDINPUT(wVk=VK_F15, dwFlags=KEYEVENTF_KEYUP)),
    )
    _send(down, up)


def nudge_mouse() -> None:
    """Move the cursor +1px then -1px (relative). Fallback for mouse-weighted detectors."""
    right = _INPUT(type=INPUT_MOUSE, u=_INPUTUNION(mi=_MOUSEINPUT(dx=1, dy=0, dwFlags=MOUSEEVENTF_MOVE)))
    back = _INPUT(type=INPUT_MOUSE, u=_INPUTUNION(mi=_MOUSEINPUT(dx=-1, dy=0, dwFlags=MOUSEEVENTF_MOVE)))
    _send(right, back)


def keep_awake(enable: bool) -> None:
    """Toggle the system/display awake requirement via SetThreadExecutionState."""
    if enable:
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    else:
        flags = ES_CONTINUOUS
    ctypes.windll.kernel32.SetThreadExecutionState(flags)
