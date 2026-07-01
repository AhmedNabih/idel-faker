from idel_faker import activity


def test_send_f15_runs_without_error():
    assert activity.send_f15() is None


def test_nudge_mouse_runs_without_error():
    assert activity.nudge_mouse() is None


def test_keep_awake_toggle_runs_without_error():
    assert activity.keep_awake(True) is None
    assert activity.keep_awake(False) is None
