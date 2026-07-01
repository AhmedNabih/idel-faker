from idel_faker import startup


def test_build_command_frozen_quotes_spaces():
    cmd = startup._build_command(frozen=True, executable=r"C:\Program Files\idel-faker.exe")
    assert cmd == r'"C:\Program Files\idel-faker.exe"'


def test_build_command_frozen_no_spaces_unquoted():
    cmd = startup._build_command(frozen=True, executable=r"C:\apps\idel-faker.exe")
    assert cmd == r"C:\apps\idel-faker.exe"


def test_build_command_source_uses_module():
    cmd = startup._build_command(
        frozen=False, executable=r"C:\Py\python.exe", pythonw=r"C:\Py\pythonw.exe"
    )
    assert cmd == r"C:\Py\pythonw.exe -m idel_faker.tray"


def test_build_command_source_quotes_spaces():
    cmd = startup._build_command(
        frozen=False, executable="", pythonw=r"C:\Program Files\Py\pythonw.exe"
    )
    assert cmd == r'"C:\Program Files\Py\pythonw.exe" -m idel_faker.tray'


def test_roundtrip_enable_check_disable():
    name = "idel-faker-test"
    try:
        assert startup.is_startup_enabled(name) is False
        startup.enable_startup(name)
        assert startup.is_startup_enabled(name) is True
    finally:
        startup.disable_startup(name)
    assert startup.is_startup_enabled(name) is False


def test_disable_absent_value_does_not_raise():
    startup.disable_startup("idel-faker-nonexistent-xyz")
