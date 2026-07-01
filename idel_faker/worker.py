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
