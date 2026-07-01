"""Workstation lock detection via the input desktop handle."""

import ctypes
from ctypes import wintypes

DESKTOP_SWITCHDESKTOP = 0x0100

# HDESK is a pointer-sized HANDLE. Without explicit restype/argtypes, ctypes
# assumes a 32-bit int return for OpenInputDesktop, which truncates the handle
# on 64-bit Windows: this can misclassify lock state (if the low 32 bits are
# zero) and passes a bad handle to CloseDesktop, leaking the real one.
# wintypes.HDESK should always be present on Windows, but fall back to
# c_void_p defensively in case a given Python's wintypes lacks it.
_HDESK = getattr(wintypes, "HDESK", ctypes.c_void_p)

user32 = ctypes.windll.user32
user32.OpenInputDesktop.restype = _HDESK
user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.CloseDesktop.restype = wintypes.BOOL
user32.CloseDesktop.argtypes = [_HDESK]


def is_locked() -> bool:
    """Return True if the workstation is locked.

    When locked, the current process cannot open the input desktop; OpenInputDesktop
    returns NULL. Any opened handle is closed immediately.
    """
    hdesk = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    if not hdesk:
        return True
    user32.CloseDesktop(hdesk)
    return False
