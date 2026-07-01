"""Windows auto-startup via the per-user Registry Run key."""

import logging
import os
import sys
import winreg

log = logging.getLogger(__name__)

APP_NAME = "idel-faker"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _quote(path: str) -> str:
    """Wrap a path in double quotes if it contains spaces and isn't already quoted."""
    if " " in path and not path.startswith('"'):
        return f'"{path}"'
    return path


def _build_command(frozen: bool, executable: str, pythonw: str | None = None) -> str:
    """Return the command line to register in the Run key.

    Frozen (PyInstaller): the executable path itself.
    Source: `<pythonw> -m idel_faker.tray`.
    """
    if frozen:
        return _quote(executable)
    launcher = pythonw or executable
    return f"{_quote(launcher)} -m idel_faker.tray"


def _current_command() -> str:
    """Compute the launch command for the currently running interpreter/exe."""
    frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        return _build_command(True, sys.executable)
    # Prefer pythonw.exe (no console window) next to python.exe when available.
    candidate = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    launcher = candidate if os.path.exists(candidate) else sys.executable
    return _build_command(False, sys.executable, launcher)


def is_startup_enabled(app_name: str = APP_NAME) -> bool:
    """Return True if a Run-key value named `app_name` exists."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, app_name)
        return True
    except OSError:
        return False


def enable_startup(app_name: str = APP_NAME) -> None:
    """Register the app to launch at logon under the per-user Run key."""
    command = _current_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)


def disable_startup(app_name: str = APP_NAME) -> None:
    """Remove the Run-key value. No error if it is already absent."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, app_name)
    except FileNotFoundError:
        pass
