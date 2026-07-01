"""Pure decision logic — the unit-testable core of idel-faker."""


def should_inject(idle_seconds: float, paused: bool, locked: bool, threshold: float) -> bool:
    """Return True when input should be injected to keep the session active.

    Injects only when not paused, not locked, and idle for at least `threshold`
    seconds. All arguments are plain values — no side effects.
    """
    return (not paused) and (not locked) and (idle_seconds >= threshold)
