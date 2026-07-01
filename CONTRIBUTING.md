# Contributing to idel-faker

Thanks for your interest in improving `idel-faker`! This is a small, focused Windows
utility, and contributions that keep it that way are very welcome.

## Getting Started

1. Fork and clone the repository.
2. Set up a development environment (Windows required — the tool uses `ctypes` against `user32`/`kernel32`):

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. Run the test suite to confirm everything passes:

   ```powershell
   pytest
   ```

## Development Guidelines

- **Keep modules small and single-purpose.** The project deliberately separates pure logic (`decision.py`, `worker.py`) from thin OS wrappers (`idle_monitor.py`, `activity.py`, `session_state.py`). Please preserve that boundary.
- **Test-driven.** Add or update tests alongside any behavior change. Pure logic should be unit-tested directly; OS wrappers use lightweight contract/smoke tests.
- **Declare your ctypes prototypes.** Set `restype`/`argtypes` for any Win32 function you call — untyped handles truncate on 64-bit Windows.
- **No new runtime dependencies** without discussion. The tool ships with only `pystray` and `Pillow`.
- **Keep it honest.** A core principle of this project is never faking a state it cannot actually achieve (e.g. presence while locked).

## Submitting Changes

1. Create a feature branch: `git checkout -b feat/short-description`.
2. Make your change with accompanying tests.
3. Ensure `pytest` passes and output is clean.
4. Open a pull request describing **what** changed and **why**, and note how you tested it (including any manual GUI verification, since the tray loop isn't automatically tested).

## Reporting Issues

Please use the issue templates and include your Windows version, Python version, and clear
steps to reproduce.
