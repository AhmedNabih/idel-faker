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
