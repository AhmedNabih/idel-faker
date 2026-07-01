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


def test_save_ico_writes_valid_icon(tmp_path):
    from idel_faker.icons import save_ico
    from PIL import Image

    out = tmp_path / "idel-faker.ico"
    save_ico(str(out))
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.format == "ICO"


def test_make_icon_accepts_custom_size():
    from idel_faker.icons import make_icon

    assert make_icon("green", 256).size == (256, 256)
    assert make_icon("green").size == (64, 64)  # default unchanged
