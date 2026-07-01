from idel_faker.session_state import is_locked


def test_returns_bool():
    assert isinstance(is_locked(), bool)


def test_not_locked_during_test_run():
    # The test runner runs in an interactive, unlocked session.
    assert is_locked() is False
