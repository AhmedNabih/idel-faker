<div align="center">

# 🟢 idel-faker

**Keep Microsoft Teams "Available" while you're away — honestly, and only when you're actually idle.**

[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](#requirements)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](#requirements)
[![Tests](https://img.shields.io/badge/tests-20%20passing-brightgreen)](#testing)
[![Dependencies](https://img.shields.io/badge/deps-pystray%20%7C%20Pillow-lightgrey)](#requirements)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)

</div>

---

`idel-faker` is a lightweight Windows system-tray utility that stops your Microsoft Teams
presence from flipping to **Away** when you step back from the keyboard. It does this by
resetting the Windows idle timer with an **invisible** input event — but **only after you've
genuinely gone idle**, so it never fights you while you're working.

Unlike crude "mouse jigglers," it is **idle-aware**, **silent during real activity**, and
**honest**: when your screen is locked (a state no user-space tool can defeat), it says so with
an orange tray icon instead of pretending you're still active.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Tray Icon States](#tray-icon-states)
- [Limitations](#limitations)
- [Architecture](#architecture)
- [Testing](#testing)
- [Ethical Use](#ethical-use)
- [License](#license)

## Features

- 🧠 **Idle-aware** — only injects input after you've been idle for a configurable threshold; your real keystrokes and mouse movements always win.
- 🫥 **Invisible input** — sends an `F15` keypress (a key that does nothing in virtually every app) plus a 1px mouse nudge. No typed characters, no triggered shortcuts.
- ☕ **Keeps the machine awake** — uses `SetThreadExecutionState` to suppress display-sleep and the screensaver (a common auto-lock trigger).
- 🖱️ **System-tray control** — pause/resume and quit from a right-click menu; the icon color reflects the current state.
- 🔒 **Honest about locks** — turns orange when the workstation is locked, so you know you've actually dropped to *Away* rather than being misled.
- 🪶 **Tiny footprint** — pure `ctypes` for all OS calls; only `pystray` and `Pillow` as dependencies.

## How It Works

Teams (like Windows itself) decides you're **Away** by reading the OS idle timer — the time
since your last real keyboard or mouse input — and flips your status after roughly five minutes
of inactivity.

Every few seconds `idel-faker`:

1. Reads how long you've been idle (`GetLastInputInfo`).
2. Checks whether it's **paused** or the workstation is **locked**.
3. If you're active, or paused, or locked → it does **nothing**.
4. If you've crossed the idle threshold → it injects an `F15` keypress and a 1px mouse nudge, resetting the idle timer well before Teams' ~5-minute cutoff.

Because your real input resets the same timer, the tool stays completely silent whenever you're
at the machine. The moment you step away long enough, it quietly keeps you green.

```
 you're typing ──► idle ≈ 0s ──► do nothing (you're active)
 you step away ──► idle ≥ 60s ─► inject F15 + nudge ──► Teams stays "Available"
 you return ─────► idle ≈ 0s ──► do nothing again
 you lock (Win+L)► locked ─────► stop + turn icon orange (honestly "Away")
```

## Requirements

- **Windows** (uses `user32` / `kernel32` via `ctypes`; not portable to macOS/Linux)
- **Python 3.8+**
- Dependencies: [`pystray`](https://pypi.org/project/pystray/), [`Pillow`](https://pypi.org/project/Pillow/)

## Installation

```powershell
git clone https://github.com/<your-username>/idel-faker.git
cd idel-faker

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```powershell
python -m idel_faker.tray
```

A tray icon appears in the Windows notification area. Right-click it for **Pause/Resume** and
**Quit**. That's it — leave it running and it manages your presence automatically.

## Configuration

Edit the constants at the top of [`idel_faker/tray.py`](idel_faker/tray.py):

| Constant | Default | Description |
| --- | --- | --- |
| `IDLE_THRESHOLD` | `60` | Seconds of genuine inactivity before input is injected. |
| `POLL_INTERVAL` | `5` | Seconds between idle/lock checks. |

## Tray Icon States

| Icon | State | Meaning |
| --- | --- | --- |
| 🟢 Green | Active | Running and keeping you "Available" when idle. |
| ⚪ Grey | Paused | Manually paused; no input is injected and sleep is not suppressed. |
| 🟠 Orange | Locked | Workstation is locked — you are *Away* and no tool can change that. |

## Limitations

> [!IMPORTANT]
> `idel-faker` cannot keep you "Available" while your **screen is locked**.

- **Locked workstation (`Win+L`):** injected input is not registered as session activity while locked, so Teams shows *Away*/locked. The tool reports this honestly with the orange icon rather than pretending otherwise.
- **Corporate Group Policy auto-lock:** a GPO *"Interactive logon: Machine inactivity limit"* can force a lock even while the tool runs unpaused. `SetThreadExecutionState` suppresses sleep/screensaver idle timers but **cannot override a GPO-enforced inactivity lock**.

In short: it reliably keeps you green whenever you step away **without locking** — the normal
scenario — and is transparent about the cases it can't handle.

## Architecture

The code is split into small, single-responsibility modules. Pure decision logic is isolated
from the thin `ctypes` wrappers so the core is fully unit-testable without touching the OS.

| Module | Responsibility |
| --- | --- |
| [`decision.py`](idel_faker/decision.py) | Pure function `should_inject(idle_seconds, paused, locked, threshold)` — the testable core. |
| [`idle_monitor.py`](idel_faker/idle_monitor.py) | `seconds_since_last_input()` via `GetLastInputInfo`. |
| [`activity.py`](idel_faker/activity.py) | `send_f15()`, `nudge_mouse()`, `keep_awake(enable)` via `SendInput` / `SetThreadExecutionState`. |
| [`session_state.py`](idel_faker/session_state.py) | `is_locked()` — probes the input desktop to detect lock. |
| [`worker.py`](idel_faker/worker.py) | `run_once(...)` — one dependency-injected tick; never raises. |
| [`icons.py`](idel_faker/icons.py) | `make_icon(color)` — generates the tray icon images. |
| [`tray.py`](idel_faker/tray.py) | Entry point: pystray icon + background worker thread wiring it all together. |

```
idel_faker/
├── decision.py        # pure logic — should we inject?
├── idle_monitor.py    # how long idle?
├── session_state.py   # is the screen locked?
├── activity.py        # inject input / hold machine awake
├── worker.py          # per-tick orchestration (testable)
├── icons.py           # tray icon images
└── tray.py            # tray app + worker thread (entry point)
tests/                 # unit tests for every module
```

## Testing

```powershell
pip install -r requirements-dev.txt
pytest
```

The suite (20 tests) covers the pure decision logic across all input combinations, the OS-wrapper
contracts, the worker's per-tick behavior including its error path, and the icon factory. The
tray's GUI loop is validated manually, since pystray offers no headless test harness.

## Ethical Use

This tool is intended for **personal, legitimate use** — for example, staying "Available" during
short breaks, long-running local tasks, or while reading/thinking away from the keyboard. It does
**not** connect to Teams, log in, or manipulate any account; it simply prevents your own machine
from registering as idle.

Be mindful of your employer's and organization's policies on presence and monitoring. Use
responsibly and at your own discretion.

## License

Released under the [MIT License](LICENSE).
