# idel-faker — Design Spec

**Date:** 2026-07-01
**Status:** Approved
**Platform:** Windows-only

## Purpose

Keep Microsoft Teams presence showing "Available" (green) by resetting the
Windows OS idle timer with invisible input whenever the user has genuinely
stepped away, while holding the machine awake. The tool is idle-aware: it never
competes with real user input, and it honestly reports (via the tray icon) when
a screen lock has dropped the user to "Away" — a state no user-space tool can
defeat.

## How Teams presence works (background)

Teams computes "Available → Away" from the OS idle timer (the same
`GetLastInputInfo` value this tool reads) and flips to Away after ~5 minutes of
no input. Injecting an input event resets that timer, keeping Teams green — but
only while the session is **unlocked**. When the workstation is locked, injected
input is not registered as session activity and Teams shows Away/locked. This is
a hard limitation of every tool of this kind.

### Coverage summary

| Scenario | Covered? |
| --- | --- |
| Step away, screen stays unlocked | ✅ Yes — idle timer reset, stays green |
| Auto-lock via screensaver / display sleep | ✅ Prevented via `SetThreadExecutionState(ES_DISPLAY_REQUIRED)` |
| Corporate GPO "machine inactivity limit" auto-lock | ⚠️ May still fire; execution-state cannot override group policy |
| Manual lock (Win+L) | ❌ Not defeatable; tray icon turns orange to report Away |

## Behavior

- **Idle-aware:** every `POLL_INTERVAL` (5s) the worker reads seconds-since-last-input.
  Real keyboard/mouse input resets this to ~0, so the tool stays silent while the
  user is active. Once idle crosses `IDLE_THRESHOLD` (60s) with no real input,
  injection begins. When the user touches anything, the counter resets and the
  tool goes silent again until the next idle stretch.
- **Injected input** (F15 keypress + 1px mouse nudge) is itself input and resets
  the idle counter; the tool then waits another full `IDLE_THRESHOLD` before the
  next injection. Real user input always wins — it happens between polls and
  resets the timer the same way.
- **Lock-aware:** when the workstation is locked, the tool stops injecting and
  turns the tray icon orange to signal the user is Away.

## Architecture

Five small, independent, single-purpose units.

### 1. `idle_monitor.py`
- `seconds_since_last_input() -> float`
- Wraps `GetLastInputInfo` (user32) via ctypes. Stateless.

### 2. `session_state.py`
- `is_locked() -> bool`
- Detects workstation lock. Primary path: register for `WM_WTSSESSION_CHANGE`
  via `WTSRegisterSessionNotification` on a hidden message window, tracking
  `WTS_SESSION_LOCK` / `WTS_SESSION_UNLOCK`. Fallback: polling if registration
  fails. Exposes current lock state to the worker.

### 3. `activity.py`
- `send_f15()` — F15 key down/up via `SendInput` (ctypes). Invisible, no-op in
  virtually every app.
- `nudge_mouse()` — relative cursor move +1px then −1px via `SendInput`
  (`MOUSEEVENTF_MOVE`). Fallback for idle detectors that weight mouse over keyboard.
- `keep_awake(enable: bool)` — toggles
  `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)`
  on enable; `ES_CONTINUOUS` alone on disable to restore normal behavior.

### 4. `decision.py`
- `should_inject(idle_seconds: float, paused: bool, locked: bool, threshold: float) -> bool`
- Pure function: `return (not paused) and (not locked) and (idle_seconds >= threshold)`.
- No side effects; the unit-testable core of the tool.

### 5. `tray.py` (entry point)
- Owns a background worker thread and the `pystray` icon.
- **Worker loop** (every `POLL_INTERVAL`):
  1. Read `idle_seconds` and `locked` state.
  2. If `should_inject(idle_seconds, paused, locked, IDLE_THRESHOLD)` →
     `send_f15()` and `nudge_mouse()`.
  3. `keep_awake(True)` held while running and not paused.
  - Each iteration wrapped in try/except: log and continue on transient failure.
- **Tray icon states:**
  - 🟢 green — active / covering
  - ⚪ grey — paused
  - 🟠 orange — locked (user is Away; tool cannot help until unlocked)
- **Tray menu:** Pause/Resume (toggles a `threading.Event`), Quit (stops thread,
  `keep_awake(False)`, clean exit).

## Data flow

Worker thread reads `idle_monitor` + `session_state` → `decision.should_inject`
→ `activity` injection. Tray callbacks flip a shared `paused` `threading.Event`.
Lock state is read each tick. No shared mutable state beyond the `paused` flag.

## Configuration

Constants at the top of `tray.py`:
- `IDLE_THRESHOLD = 60` (seconds idle before injecting)
- `POLL_INTERVAL = 5` (seconds between checks)

## Error handling

- Worker loop wraps each iteration in try/except (log + continue) so a transient
  ctypes failure does not kill the thread.
- Shutdown always calls `keep_awake(False)` to restore normal power/idle behavior.

## Dependencies

`requirements.txt`:
- `pystray`
- `Pillow`

(`ctypes` is stdlib.)

## Testing

- `decision.should_inject` — fully unit-tested across all combinations of
  paused / locked / idle above and below threshold.
- `idle_monitor` and `session_state` — thin ctypes wrappers kept minimal; the
  testable logic lives in `decision`.

## Out of scope

- Defeating a locked workstation (impossible from user space; reported honestly instead).
- Microsoft Graph API presence setting (no auth flow; input-simulation approach chosen).
- Working-hours scheduling (manual tray control chosen instead).
- Non-Windows platforms.
