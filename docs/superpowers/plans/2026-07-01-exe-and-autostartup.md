# EXE Packaging & Windows Auto-Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a runtime-toggleable "Start with Windows" tray option (per-user Registry Run key) and a PyInstaller build producing a single self-contained `idel-faker.exe`.

**Architecture:** A new stdlib-`winreg` module (`startup.py`) with a pure command-builder and thin Run-key wrappers; a checkable tray menu item wired to it; an icon `.ico` generator reusing the existing Pillow drawing; and PyInstaller packaging (`run.py` entry + `idel-faker.spec` + `build.ps1`).

**Tech Stack:** Python 3.8+, stdlib `winreg`/`ctypes`, `pystray`, `Pillow`, `pyinstaller` (dev), `pytest` (dev).

## Global Constraints

- Platform: Windows-only.
- Startup mechanism: Registry Run key `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, value name `idel-faker`, via stdlib `winreg` (per-user, no admin).
- Startup control: a checkable "Start with Windows" tray menu item (runtime toggle).
- Packaging: PyInstaller `--onefile --windowed` (`console=False`), name `idel-faker`, icon `build/idel-faker.ico`, `hiddenimports=["pystray._win32"]`, entry script `run.py`.
- No new *runtime* dependencies (`pyinstaller` is dev-only). `winreg` is stdlib.
- Source modules in `idel_faker/`, tests in `tests/`, build helpers in `scripts/`.
- `.gitignore` already ignores `build/` and `dist/` — do not commit build artifacts.

---

### Task 1: Startup registration module

**Files:**
- Create: `idel_faker/startup.py`
- Test: `tests/test_startup.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces: `is_startup_enabled(app_name: str = APP_NAME) -> bool`, `enable_startup(app_name: str = APP_NAME) -> None`, `disable_startup(app_name: str = APP_NAME) -> None`, `_build_command(frozen: bool, executable: str, pythonw: str | None = None) -> str`, constant `APP_NAME = "idel-faker"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_startup.py
from idel_faker import startup


def test_build_command_frozen_quotes_spaces():
    cmd = startup._build_command(frozen=True, executable=r"C:\Program Files\idel-faker.exe")
    assert cmd == r'"C:\Program Files\idel-faker.exe"'


def test_build_command_frozen_no_spaces_unquoted():
    cmd = startup._build_command(frozen=True, executable=r"C:\apps\idel-faker.exe")
    assert cmd == r"C:\apps\idel-faker.exe"


def test_build_command_source_uses_module():
    cmd = startup._build_command(
        frozen=False, executable=r"C:\Py\python.exe", pythonw=r"C:\Py\pythonw.exe"
    )
    assert cmd == r"C:\Py\pythonw.exe -m idel_faker.tray"


def test_build_command_source_quotes_spaces():
    cmd = startup._build_command(
        frozen=False, executable="", pythonw=r"C:\Program Files\Py\pythonw.exe"
    )
    assert cmd == r'"C:\Program Files\Py\pythonw.exe" -m idel_faker.tray'


def test_roundtrip_enable_check_disable():
    name = "idel-faker-test"
    try:
        assert startup.is_startup_enabled(name) is False
        startup.enable_startup(name)
        assert startup.is_startup_enabled(name) is True
    finally:
        startup.disable_startup(name)
    assert startup.is_startup_enabled(name) is False


def test_disable_absent_value_does_not_raise():
    startup.disable_startup("idel-faker-nonexistent-xyz")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_startup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.startup'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/startup.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_startup.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/startup.py tests/test_startup.py
git commit -m "feat: add winreg-based Windows startup registration"
```

---

### Task 2: Icon `.ico` generation

**Files:**
- Modify: `idel_faker/icons.py` (generalize `make_icon` to accept a size; add `save_ico`)
- Create: `scripts/make_ico.py`
- Test: `tests/test_icons.py` (add a `save_ico` test; keep existing tests)

**Interfaces:**
- Consumes: nothing new.
- Produces: `make_icon(color: str, size: int = 64) -> PIL.Image.Image` (backward compatible), `save_ico(path: str) -> None`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_icons.py` (keep the existing tests as-is):

```python
def test_save_ico_writes_valid_icon(tmp_path):
    from idel_faker.icons import save_ico
    from PIL import Image

    out = tmp_path / "idel-faker.ico"
    save_ico(str(out))
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.format == "ICO"


def test_make_icon_accepts_custom_size():
    from idel_faker.icons import make_icon

    assert make_icon("green", 256).size == (256, 256)
    assert make_icon("green").size == (64, 64)  # default unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_icons.py -v`
Expected: FAIL — `ImportError: cannot import name 'save_ico'` (and `make_icon` rejects the size arg).

- [ ] **Step 3: Write minimal implementation**

Replace the body of `idel_faker/icons.py` with:

```python
"""Tray icon images for each state, and .ico export for packaging."""

from PIL import Image, ImageDraw

_COLORS = {
    "green": (46, 204, 113),
    "grey": (149, 165, 166),
    "orange": (230, 126, 34),
}

_ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)]


def make_icon(color: str, size: int = 64) -> Image.Image:
    """Return a filled-circle icon of `size`x`size` for the given state color."""
    rgb = _COLORS[color]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = size // 8
    draw.ellipse((pad, pad, size - pad, size - pad), fill=rgb)
    return img


def save_ico(path: str) -> None:
    """Write a multi-size Windows .ico (from the green state icon) to `path`."""
    make_icon("green", 256).save(path, format="ICO", sizes=_ICO_SIZES)
```

- [ ] **Step 4: Create the build helper script**

```python
# scripts/make_ico.py
"""Generate build/idel-faker.ico for PyInstaller packaging."""

import os
import sys

# Make the repo root importable when run as `python scripts/make_ico.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idel_faker.icons import save_ico

OUT_DIR = "build"
OUT_PATH = os.path.join(OUT_DIR, "idel-faker.ico")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    save_ico(OUT_PATH)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests and the script to verify**

Run: `python -m pytest tests/test_icons.py -v`
Expected: PASS (all existing + 2 new).

Run: `python scripts/make_ico.py`
Expected: prints `wrote build/idel-faker.ico`; the file exists.

- [ ] **Step 6: Commit**

```bash
git add idel_faker/icons.py scripts/make_ico.py tests/test_icons.py
git commit -m "feat: add multi-size .ico export and build/make_ico script"
```

---

### Task 3: Tray "Start with Windows" toggle

**Files:**
- Modify: `idel_faker/tray.py` (add `startup` import, menu item, `_toggle_startup`)

**Interfaces:**
- Consumes: `idel_faker.startup.is_startup_enabled`, `enable_startup`, `disable_startup`.
- Produces: no new public interface (tray-internal).

- [ ] **Step 1: Add the import**

In `idel_faker/tray.py`, add `startup` to the package imports. Change:

```python
from . import activity
```

to:

```python
from . import activity
from . import startup
```

- [ ] **Step 2: Add the checkable menu item**

In `TrayApp.__init__`, change the menu block from:

```python
            menu=pystray.Menu(
                pystray.MenuItem(self._pause_label, self._toggle_pause),
                pystray.MenuItem("Quit", self._quit),
            ),
```

to:

```python
            menu=pystray.Menu(
                pystray.MenuItem(self._pause_label, self._toggle_pause),
                pystray.MenuItem(
                    "Start with Windows",
                    self._toggle_startup,
                    checked=lambda item: startup.is_startup_enabled(),
                ),
                pystray.MenuItem("Quit", self._quit),
            ),
```

- [ ] **Step 3: Add the toggle handler**

Add this method to `TrayApp` (e.g. immediately after `_toggle_pause`):

```python
    def _toggle_startup(self, _icon, _item) -> None:
        try:
            if startup.is_startup_enabled():
                startup.disable_startup()
            else:
                startup.enable_startup()
        except OSError:
            log.exception("failed to toggle Windows startup")
        self.icon.update_menu()
```

- [ ] **Step 4: Verify the module still imports and the suite passes**

Run: `python -c "import idel_faker.tray; print('import OK')"`
Expected: `import OK`

Run: `python -m pytest -q`
Expected: all tests pass (no test regression; tray GUI itself is not unit-tested).

- [ ] **Step 5: Manual smoke test**

Run: `python -m idel_faker.tray`
Expected:
- Right-click the tray icon → menu shows "Start with Windows" with no checkmark.
- Click it → checkmark appears; a `idel-faker` value now exists under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (verify with `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v idel-faker`).
- Click it again → checkmark clears; the value is removed (`reg query ...` reports it is not found).
- Quit exits cleanly.

- [ ] **Step 6: Commit**

```bash
git add idel_faker/tray.py
git commit -m "feat: add Start with Windows tray toggle"
```

---

### Task 4: PyInstaller packaging

**Files:**
- Create: `run.py`
- Create: `idel-faker.spec`
- Create: `build.ps1`
- Modify: `requirements-dev.txt` (add `pyinstaller`)

**Interfaces:**
- Consumes: `idel_faker.tray.main`.
- Produces: build artifact `dist/idel-faker.exe` (not committed).

- [ ] **Step 1: Create the entry point**

```python
# run.py
"""PyInstaller entry point for idel-faker (absolute import bundles the package)."""

from idel_faker.tray import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add pyinstaller to dev requirements**

Change `requirements-dev.txt` from:

```
-r requirements.txt
pytest
```

to:

```
-r requirements.txt
pytest
pyinstaller
```

- [ ] **Step 3: Create the PyInstaller spec**

```python
# idel-faker.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pystray._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='idel-faker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='build/idel-faker.ico',
)
```

- [ ] **Step 4: Create the build script**

```powershell
# build.ps1 — build a one-file, windowed idel-faker.exe with PyInstaller.
$ErrorActionPreference = "Stop"

pip install -r requirements-dev.txt
python scripts/make_ico.py
pyinstaller --clean --noconfirm idel-faker.spec

Write-Host "Built dist/idel-faker.exe"
```

- [ ] **Step 5: Build and verify the executable**

Run: `powershell -ExecutionPolicy Bypass -File build.ps1`
Expected:
- `scripts/make_ico.py` prints `wrote build/idel-faker.ico`.
- PyInstaller completes without error.
- `dist/idel-faker.exe` exists (verify: `Test-Path dist/idel-faker.exe` → `True`).

Then launch it once to confirm it runs as a tray app:
Run: `./dist/idel-faker.exe` (a tray icon should appear; right-click → Quit to exit).
Expected: the tray icon appears and the app behaves like `python -m idel_faker.tray`.

If the build tool is unavailable in the environment, report BLOCKED with the exact error rather than skipping verification.

- [ ] **Step 6: Commit**

```bash
git add run.py idel-faker.spec build.ps1 requirements-dev.txt
git commit -m "build: add PyInstaller one-file windowed packaging"
```

---

### Task 5: Documentation

**Files:**
- Modify: `README.md` (build section + startup toggle)

- [ ] **Step 1: Document the "Start with Windows" toggle**

In `README.md`, update the tray usage/states description. In the **Tray Icon States** or **Usage** area, add a note that the right-click menu includes a checkable **"Start with Windows"** item, and add this subsection after the **Configuration** section:

```markdown
## Start with Windows

Right-click the tray icon and toggle **Start with Windows**. When checked, `idel-faker`
registers itself under the per-user Registry Run key
(`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, value `idel-faker`) and launches
automatically at logon. Unchecking it removes the entry. No administrator rights are required.
```

- [ ] **Step 2: Document building the .exe**

In `README.md`, replace the existing `## Installation` section's reliance on Python-only by adding a **Build a standalone .exe** section after **Usage**:

```markdown
## Build a Standalone .exe

To produce a single self-contained `idel-faker.exe` (no Python needed on the target machine):

```powershell
pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File build.ps1
```

The build (PyInstaller, one-file, windowed) generates the app icon and writes the executable to
`dist/idel-faker.exe`. Copy that file anywhere and run it; use the tray's **Start with Windows**
toggle to have it launch at logon.
```

- [ ] **Step 3: Verify README renders sensibly**

Read the modified `README.md` and confirm the new sections are present, correctly nested, and the fenced code blocks are balanced.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document exe build and Start with Windows toggle"
```

---

### Task 6: Final verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -v`
Expected: all tests pass (existing 20 + new startup/icon tests), output pristine.

- [ ] **Step 2: Confirm the package imports**

Run: `python -c "import idel_faker.tray, idel_faker.startup, run; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "test: verify exe/startup feature suite passes" --allow-empty
```

---

## Self-Review

**Spec coverage:**
- `startup.py` (is/enable/disable + pure `_build_command`) → Task 1.
- Tray checkable "Start with Windows" toggle + error handling → Task 3.
- `save_ico` + `scripts/make_ico.py` → Task 2.
- `run.py` entry point → Task 4.
- `idel-faker.spec` (onefile/windowed/icon/hiddenimports) → Task 4.
- `build.ps1` orchestration → Task 4.
- `pyinstaller` in `requirements-dev.txt` → Task 4.
- README build + startup docs → Task 5.
- Tests (startup `_build_command` + HKCU round-trip + absent-value; `save_ico`) → Tasks 1, 2.
- Final full-suite verification → Task 6.

**Placeholder scan:** No TBD/TODO; every code step contains complete code.

**Type consistency:** `APP_NAME`, `is_startup_enabled`, `enable_startup`, `disable_startup`,
`_build_command`, `make_icon`, `save_ico`, `main` are referenced identically across producing
and consuming tasks. `make_icon`'s new `size` parameter defaults to 64, preserving all existing
call sites (`make_icon("green")` in tray.py and existing tests).
