"""Workstation lock detection via the input desktop handle."""

import ctypes

DESKTOP_SWITCHDESKTOP = 0x0100


def is_locked() -> bool:
    """Return True if the workstation is locked.

    When locked, the current process cannot open the input desktop; OpenInputDesktop
    returns NULL. Any opened handle is closed immediately.
    """
    user32 = ctypes.windll.user32
    hdesk = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    if not hdesk:
        return True
    user32.CloseDesktop(hdesk)
    return False
