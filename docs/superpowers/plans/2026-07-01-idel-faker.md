# idel-faker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows system-tray tool that keeps Microsoft Teams presence "Available" by injecting invisible input when the user is genuinely idle, while staying silent during real activity and honestly reporting when a screen lock has forced "Away".

**Architecture:** Five small single-purpose modules. Pure decision logic (`decision.py`) is separated from thin ctypes wrappers (`idle_monitor.py`, `session_state.py`, `activity.py`) so the core is unit-testable. A `pystray` tray app (`tray.py`) runs a worker thread that polls idle + lock state and injects input via the decision function.

**Tech Stack:** Python 3, `ctypes` (stdlib), `pystray`, `Pillow`, `pytest` (dev).

## Global Constraints

- Platform: Windows-only. ctypes calls target `user32`, `kernel32`, `wtsapi32`.
- Config constants live at the top of `tray.py`: `IDLE_THRESHOLD = 60`, `POLL_INTERVAL = 5`.
- Runtime dependencies: `pystray`, `Pillow` only. `ctypes` is stdlib.
- No shared mutable state beyond a single `threading.Event` (`paused`).
- Injected input: F15 keypress (`send_f15`) plus a 1px relative mouse nudge (`nudge_mouse`).
- Every worker-loop iteration wraps work in try/except (log + continue); shutdown always calls `keep_awake(False)`.
- Package layout: source modules in `idel_faker/`, tests in `tests/`.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `idel_faker/__init__.py`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Create `requirements.txt`**

```
pystray
Pillow
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest
```

- [ ] **Step 3: Create `idel_faker/__init__.py`**

```python
"""idel-faker: keep Windows/Teams from going idle when you step away."""
```

- [ ] **Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
build/
dist/
*.egg-info/
```

- [ ] **Step 5: Create `README.md`**

```markdown
# idel-faker

Windows system-tray tool that keeps Microsoft Teams showing "Available" by
injecting invisible input (F15 + 1px mouse nudge) only when you are genuinely
idle. Stays silent while you work. Turns the tray icon orange when the screen is
locked (a state no user-space tool can defeat).

## Install

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```
python -m idel_faker.tray
```

Tray icon: green = active, grey = paused, orange = locked (you are Away).
Right-click for Pause/Resume and Quit.

## Config

Edit constants at the top of `idel_faker/tray.py`:
- `IDLE_THRESHOLD` (seconds idle before injecting, default 60)
- `POLL_INTERVAL` (seconds between checks, default 5)

## Limitations

Cannot keep you "Available" while the workstation is locked (Win+L or GPO
auto-lock) — injected input is not registered as session activity when locked.
The tool reports this honestly via the orange icon.

## Development

```
pip install -r requirements-dev.txt
pytest
```
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt requirements-dev.txt idel_faker/__init__.py .gitignore README.md
git commit -m "chore: scaffold idel-faker project"
```

---

### Task 2: Decision logic (pure, fully tested)

**Files:**
- Create: `idel_faker/decision.py`
- Test: `tests/test_decision.py`

**Interfaces:**
- Produces: `should_inject(idle_seconds: float, paused: bool, locked: bool, threshold: float) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_decision.py
from idel_faker.decision import should_inject


def test_injects_when_idle_past_threshold():
    assert should_inject(idle_seconds=60, paused=False, locked=False, threshold=60) is True


def test_no_inject_below_threshold():
    assert should_inject(idle_seconds=59, paused=False, locked=False, threshold=60) is False


def test_no_inject_when_paused():
    assert should_inject(idle_seconds=120, paused=True, locked=False, threshold=60) is False


def test_no_inject_when_locked():
    assert should_inject(idle_seconds=120, paused=False, locked=True, threshold=60) is False


def test_no_inject_when_paused_and_locked():
    assert should_inject(idle_seconds=120, paused=True, locked=True, threshold=60) is False


def test_exact_threshold_boundary_injects():
    assert should_inject(idle_seconds=60.0, paused=False, locked=False, threshold=60.0) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_decision.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.decision'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/decision.py
"""Pure decision logic — the unit-testable core of idel-faker."""


def should_inject(idle_seconds: float, paused: bool, locked: bool, threshold: float) -> bool:
    """Return True when input should be injected to keep the session active.

    Injects only when not paused, not locked, and idle for at least `threshold`
    seconds. All arguments are plain values — no side effects.
    """
    return (not paused) and (not locked) and (idle_seconds >= threshold)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_decision.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/decision.py tests/test_decision.py
git commit -m "feat: add pure should_inject decision logic"
```

---

### Task 3: Idle monitor (ctypes wrapper)

**Files:**
- Create: `idel_faker/idle_monitor.py`
- Test: `tests/test_idle_monitor.py`

**Interfaces:**
- Produces: `seconds_since_last_input() -> float`

- [ ] **Step 1: Write the failing test**

The wrapper reads a real OS value, so the test asserts contract properties
(returns a non-negative float; two calls with no assumption of ordering are both
non-negative) rather than an exact number.

```python
# tests/test_idle_monitor.py
from idel_faker.idle_monitor import seconds_since_last_input


def test_returns_non_negative_float():
    value = seconds_since_last_input()
    assert isinstance(value, float)
    assert value >= 0.0


def test_repeatable():
    first = seconds_since_last_input()
    second = seconds_since_last_input()
    assert first >= 0.0
    assert second >= 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_idle_monitor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.idle_monitor'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/idle_monitor.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_idle_monitor.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/idle_monitor.py tests/test_idle_monitor.py
git commit -m "feat: add idle_monitor.seconds_since_last_input"
```

---

### Task 4: Activity injection (ctypes wrappers)

**Files:**
- Create: `idel_faker/activity.py`
- Test: `tests/test_activity.py`

**Interfaces:**
- Produces: `send_f15() -> None`, `nudge_mouse() -> None`, `keep_awake(enable: bool) -> None`

- [ ] **Step 1: Write the failing test**

These functions have side effects on the real OS. The test verifies they are
callable and return `None` without raising (smoke test), which is the meaningful
contract for a thin wrapper.

```python
# tests/test_activity.py
from idel_faker import activity


def test_send_f15_runs_without_error():
    assert activity.send_f15() is None


def test_nudge_mouse_runs_without_error():
    assert activity.nudge_mouse() is None


def test_keep_awake_toggle_runs_without_error():
    assert activity.keep_awake(True) is None
    assert activity.keep_awake(False) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_activity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.activity'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/activity.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_activity.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/activity.py tests/test_activity.py
git commit -m "feat: add F15/mouse-nudge injection and keep_awake"
```

---

### Task 5: Session lock state

**Files:**
- Create: `idel_faker/session_state.py`
- Test: `tests/test_session_state.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `is_locked() -> bool`

**Design note:** Robustly detecting lock via `WTSRegisterSessionNotification`
requires a hidden message-pump window, which is heavy for a polled worker. This
task implements a poll-friendly `is_locked()` using `OpenInputDesktop`: when the
workstation is locked, the calling process cannot open the input desktop. This
gives a synchronous boolean each tick without a message loop, matching the
worker's polling model in Task 6.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_session_state.py
from idel_faker.session_state import is_locked


def test_returns_bool():
    assert isinstance(is_locked(), bool)


def test_not_locked_during_test_run():
    # The test runner runs in an interactive, unlocked session.
    assert is_locked() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_session_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.session_state'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/session_state.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_session_state.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/session_state.py tests/test_session_state.py
git commit -m "feat: add session_state.is_locked via input desktop probe"
```

---

### Task 6: Worker loop (testable, injection-free of pystray)

**Files:**
- Create: `idel_faker/worker.py`
- Test: `tests/test_worker.py`

**Interfaces:**
- Consumes: `decision.should_inject`, `idle_monitor.seconds_since_last_input`,
  `session_state.is_locked`, `activity.send_f15`, `activity.nudge_mouse`.
- Produces: `run_once(paused: bool, *, idle_fn, locked_fn, inject_fn, threshold: float) -> str`
  returning one of `"inject"`, `"idle-active"`, `"paused"`, `"locked"`, `"error"`.

**Design note:** The worker's per-tick logic is extracted into `run_once` with
injected dependencies so it is unit-testable without real OS calls or a running
thread. `tray.py` (Task 7) wires the real functions and the loop/timing around it.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_worker.py
from idel_faker.worker import run_once


def _wire(idle, locked, sent):
    def inject():
        sent.append(True)
    return dict(
        idle_fn=lambda: idle,
        locked_fn=lambda: locked,
        inject_fn=inject,
        threshold=60.0,
    )


def test_injects_when_idle():
    sent = []
    result = run_once(paused=False, **_wire(idle=120, locked=False, sent=sent))
    assert result == "inject"
    assert sent == [True]


def test_idle_active_when_below_threshold():
    sent = []
    result = run_once(paused=False, **_wire(idle=5, locked=False, sent=sent))
    assert result == "idle-active"
    assert sent == []


def test_paused_short_circuits():
    sent = []
    result = run_once(paused=True, **_wire(idle=120, locked=False, sent=sent))
    assert result == "paused"
    assert sent == []


def test_locked_reported_and_no_inject():
    sent = []
    result = run_once(paused=False, **_wire(idle=120, locked=True, sent=sent))
    assert result == "locked"
    assert sent == []


def test_error_is_caught():
    def boom():
        raise OSError("ctypes failed")
    result = run_once(
        paused=False,
        idle_fn=boom,
        locked_fn=lambda: False,
        inject_fn=lambda: None,
        threshold=60.0,
    )
    assert result == "error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.worker'`

- [ ] **Step 3: Write minimal implementation**

```python
# idel_faker/worker.py
"""Per-tick worker logic, decoupled from threading and the tray for testing."""

import logging

from .decision import should_inject

log = logging.getLogger(__name__)


def run_once(paused, *, idle_fn, locked_fn, inject_fn, threshold):
    """Evaluate one tick. Returns a status string; never raises.

    Order matters: paused is cheapest and user-intended, so it short-circuits
    before touching the OS. Lock is reported distinctly so callers can surface it.
    """
    try:
        if paused:
            return "paused"
        locked = locked_fn()
        if locked:
            return "locked"
        idle_seconds = idle_fn()
        if should_inject(idle_seconds, paused=False, locked=False, threshold=threshold):
            inject_fn()
            return "inject"
        return "idle-active"
    except Exception:  # noqa: BLE001 - loop must survive transient ctypes failures
        log.exception("worker tick failed")
        return "error"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_worker.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add idel_faker/worker.py tests/test_worker.py
git commit -m "feat: add testable per-tick worker.run_once"
```

---

### Task 7: Tray application (entry point)

**Files:**
- Create: `idel_faker/icons.py`
- Create: `idel_faker/tray.py`
- Test: `tests/test_icons.py`

**Interfaces:**
- Consumes: `worker.run_once`, `activity.keep_awake`, `idle_monitor.seconds_since_last_input`,
  `session_state.is_locked`, `activity.send_f15`, `activity.nudge_mouse`.
- Produces: entry point `python -m idel_faker.tray`; `icons.make_icon(color: str) -> PIL.Image.Image`.

- [ ] **Step 1: Write the failing test (icon factory)**

The tray loop needs a running Windows session and a real tray, so the automated
test covers the pure icon factory. The loop is exercised manually in Step 6.

```python
# tests/test_icons.py
from idel_faker.icons import make_icon


def test_make_icon_returns_image_of_expected_size():
    img = make_icon("green")
    assert img.size == (64, 64)


def test_make_icon_distinct_per_color():
    green = make_icon("green").tobytes()
    orange = make_icon("orange").tobytes()
    grey = make_icon("grey").tobytes()
    assert green != orange != grey
    assert green != grey
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_icons.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'idel_faker.icons'`

- [ ] **Step 3: Write the icon factory**

```python
# idel_faker/icons.py
"""Tray icon images for each state."""

from PIL import Image, ImageDraw

_COLORS = {
    "green": (46, 204, 113),
    "grey": (149, 165, 166),
    "orange": (230, 126, 34),
}


def make_icon(color: str) -> Image.Image:
    """Return a 64x64 filled-circle icon for the given state color."""
    rgb = _COLORS[color]
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=rgb)
    return img
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_icons.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Write the tray application**

```python
# idel_faker/tray.py
"""System-tray entry point: worker thread + pystray icon."""

import logging
import threading

import pystray

from . import activity
from .icons import make_icon
from .idle_monitor import seconds_since_last_input
from .session_state import is_locked
from .worker import run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("idel_faker")

IDLE_THRESHOLD = 60  # seconds idle before injecting
POLL_INTERVAL = 5    # seconds between checks


def _inject() -> None:
    activity.send_f15()
    activity.nudge_mouse()


class TrayApp:
    def __init__(self):
        self._paused = threading.Event()      # set => paused
        self._stop = threading.Event()        # set => shutting down
        self._state = "green"
        self.icon = pystray.Icon(
            "idel-faker",
            make_icon("green"),
            "idel-faker",
            menu=pystray.Menu(
                pystray.MenuItem(self._pause_label, self._toggle_pause),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def _pause_label(self, _item) -> str:
        return "Resume" if self._paused.is_set() else "Pause"

    def _toggle_pause(self, _icon, _item) -> None:
        if self._paused.is_set():
            self._paused.clear()
        else:
            self._paused.set()
        self.icon.update_menu()

    def _quit(self, _icon, _item) -> None:
        self._stop.set()
        activity.keep_awake(False)
        self.icon.stop()

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self.icon.icon = make_icon(state)

    def _worker(self) -> None:
        activity.keep_awake(True)
        while not self._stop.wait(POLL_INTERVAL):
            result = run_once(
                paused=self._paused.is_set(),
                idle_fn=seconds_since_last_input,
                locked_fn=is_locked,
                inject_fn=_inject,
                threshold=IDLE_THRESHOLD,
            )
            if result == "paused":
                self._set_state("grey")
            elif result == "locked":
                self._set_state("orange")
            else:
                self._set_state("green")
            log.info("tick: %s", result)

    def run(self) -> None:
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()
        try:
            self.icon.run()
        finally:
            self._stop.set()
            activity.keep_awake(False)


def main() -> None:
    TrayApp().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Manual smoke test**

Run: `python -m idel_faker.tray`
Expected:
- A green tray icon appears.
- Leave the mouse/keyboard untouched >60s → logs show `tick: inject`; Teams stays Available.
- Move the mouse → logs show `tick: idle-active`; no injection.
- Right-click → Pause → icon turns grey, logs show `tick: paused`.
- Resume, then lock the screen (Win+L) → icon turns orange, logs show `tick: locked`.
- Unlock → icon returns to green.
- Right-click → Quit → process exits cleanly.

- [ ] **Step 7: Commit**

```bash
git add idel_faker/icons.py idel_faker/tray.py tests/test_icons.py
git commit -m "feat: add tray app entry point with state icons"
```

---

### Task 8: Full test run and final verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: all tests pass (decision, idle_monitor, activity, session_state, worker, icons).

- [ ] **Step 2: Verify the module runs**

Run: `python -c "import idel_faker.tray"`
Expected: no import errors.

- [ ] **Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "test: verify full idel-faker suite passes" --allow-empty
```

---

## Self-Review

**Spec coverage:**
- Idle-aware injection → Tasks 2, 3, 6.
- F15 + mouse nudge → Task 4.
- keep_awake / execution state → Task 4 (+ wired in Task 7).
- Lock detection + orange icon → Tasks 5, 7.
- Pure `should_inject` → Task 2.
- Tray icon states + Pause/Resume/Quit → Task 7.
- Config constants `IDLE_THRESHOLD` / `POLL_INTERVAL` → Task 7.
- Error handling (try/except per tick) → Task 6.
- Clean shutdown restores execution state → Task 7 (`_quit`, `run` finally).
- Dependencies `pystray`, `Pillow` → Task 1.

**Type consistency:** `should_inject`, `seconds_since_last_input`, `is_locked`,
`send_f15`, `nudge_mouse`, `keep_awake`, `run_once`, `make_icon` are referenced
with identical names/signatures across producing and consuming tasks.

**Placeholder scan:** No TBD/TODO; all code steps contain complete code.
