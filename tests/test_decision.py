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
