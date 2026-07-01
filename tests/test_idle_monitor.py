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
