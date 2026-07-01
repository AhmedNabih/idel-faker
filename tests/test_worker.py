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
