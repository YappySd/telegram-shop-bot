import pytest

from bot.parsing import parse_add_args


def test_full_arguments():
    assert parse_add_args("Кружка | 8.50 | Белая, 300 мл") == ("Кружка", 850, "Белая, 300 мл")


def test_comma_as_decimal_separator():
    assert parse_add_args("Блокнот | 4,5") == ("Блокнот", 450, "")


def test_price_is_rounded_to_cents():
    assert parse_add_args("X | 0.019")[1] == 2


@pytest.mark.parametrize(
    "bad",
    [None, "", "   ", "Кружка", "| 5", "Кружка | abc", "Кружка | 0", "Кружка | -3", "Кружка | nan", "Кружка | 0.001"],
)
def test_invalid_arguments_raise(bad):
    with pytest.raises(ValueError):
        parse_add_args(bad)
