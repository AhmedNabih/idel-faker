# idel-faker — EXE Packaging & Windows Auto-Startup Design Spec

**Date:** 2026-07-01
**Status:** Approved
**Platform:** Windows-only
**Builds on:** [2026-07-01-idel-faker-design.md](2026-07-01-idel-faker-design.md)

## Purpose

Add two capabilities to the existing `idel-faker` tray tool:

1. **Standalone executable** — a single self-contained `idel-faker.exe` (PyInstaller,
   one-file, windowed) so the tool runs on any Windows machine without a Python install.
2. **Windows auto-startup** — a runtime-toggleable "Start with Windows" tray menu item that
   registers/unregisters the app in the per-user Registry Run key.

## Decisions

- Startup control: **tray menu toggle** (checkable menu item), not build-time or first-run automatic.
- Startup mechanism: **Registry Run key** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, value name `idel-faker`, via stdlib `winreg` (per-user, no admin).
- Packaging: **PyInstaller `--onefile --windowed`** with a bundled `.ico`.

## Components

### 1. `idel_faker/startup.py` (new)

Thin `winreg` wrapper plus a pure command builder.

- `APP_NAME = "idel-faker"` — the Run value name.
- `RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"` — under `HKEY_CURRENT_USER`.
- `is_startup_enabled(app_name: str = APP_NAME) -> bool` — True if the Run value exists.
- `enable_startup(app_name: str = APP_NAME) -> None` — writes the Run value = launch command.
- `disable_startup(app_name: str = APP_NAME) -> None` — deletes the Run value (no error if absent).
- `_build_command(frozen: bool, executable: str, pythonw: str | None = None) -> str` — **pure**.
  - When `frozen` (PyInstaller): return `executable` (the `.exe` path), quoted.
  - When not frozen (source): return `"<pythonw>" -m idel_faker.tray`, quoted.
  - Paths containing spaces are wrapped in double quotes.

The `app_name` parameter exists so tests can round-trip against a throwaway Run value.

### 2. `idel_faker/tray.py` (modified)

Add a checkable menu item above `Quit`:

```python
pystray.MenuItem(
    "Start with Windows",
    self._toggle_startup,
    checked=lambda item: startup.is_startup_enabled(),
)
```

- `_toggle_startup(self, _icon, _item)` — if enabled → `disable_startup()`, else → `enable_startup()`;
  wrapped in try/except (registry writes can fail in locked-down environments → log, don't crash);
  then `self.icon.update_menu()` so the checkmark refreshes.

No change to the worker loop or existing shutdown/keep_awake logic.

### 3. Icon generation

- `idel_faker/icons.py` (modified): add `save_ico(path: str) -> None` — writes a multi-size
  `.ico` (16, 32, 48, 64, 256) derived from `make_icon("green")`, using Pillow's ICO writer.
- `scripts/make_ico.py` (new): ensures `build/` exists and calls `save_ico("build/idel-faker.ico")`.

### 4. PyInstaller entry point — `run.py` (new)

```python
from idel_faker.tray import main

if __name__ == "__main__":
    main()
```

Uses an **absolute** import so PyInstaller bundles the whole `idel_faker` package. (Targeting
`idel_faker/tray.py` directly would break its relative imports when run as `__main__`.)

### 5. PyInstaller spec — `idel-faker.spec` (new)

- One-file, windowed (`console=False`).
- `name="idel-faker"`, `icon="build/idel-faker.ico"`.
- `hiddenimports=["pystray._win32"]` (pystray's Windows backend is imported lazily).
- Entry script: `run.py`.

### 6. Build script — `build.ps1` (new)

Convenience orchestrator:
1. `pip install -r requirements-dev.txt`
2. `python scripts/make_ico.py` (generates `build/idel-faker.ico`)
3. `pyinstaller idel-faker.spec`

Output: `dist/idel-faker.exe`.

### 7. Dependencies & ignores

- `requirements-dev.txt`: add `pyinstaller`.
- `.gitignore`: already ignores `build/` and `dist/` — no change needed.

### 8. Documentation — `README.md` (modified)

- New "Build a standalone .exe" section (run `build.ps1`, output path).
- Document the "Start with Windows" tray toggle in the usage/tray sections.

## Data flow

Tray menu click → `_toggle_startup` → `startup.enable_startup()` / `disable_startup()` →
`winreg` writes/deletes the Run value → `is_startup_enabled()` (via the `checked=` lambda)
reflects the new state on next menu render. On next Windows logon, the Run key launches
`idel-faker.exe`, which starts the tray app exactly as `python -m idel_faker.tray` does today.

## Error handling

- All `winreg` operations in `enable_startup`/`disable_startup`/`is_startup_enabled` are wrapped
  so a missing key/value is treated as "not enabled" rather than an error.
- `_toggle_startup` catches and logs any failure so a registry write error never crashes the tray.

## Testing

- `tests/test_startup.py`:
  - `_build_command` — frozen returns the exe path (quoted); source returns `pythonw -m idel_faker.tray`;
    paths with spaces are quoted.
  - Round-trip — `enable_startup` → `is_startup_enabled` True → `disable_startup` → False,
    using a throwaway `app_name` (e.g. `idel-faker-test`) and cleaned up in `finally`
    (per-user HKCU, no admin, reversible).
  - `disable_startup` on an absent value does not raise.
- `tests/test_icons.py` (extended): `save_ico` writes a file that Pillow reopens as a valid `.ico`.
- Tray menu wiring: manual smoke test (GUI), consistent with the existing tray-loop verification.

## Out of scope

- Startup folder shortcut and Task Scheduler mechanisms (Registry Run key chosen).
- Code signing / installer (MSI/Inno Setup).
- Auto-update.
- Non-Windows packaging.
