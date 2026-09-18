import pytest

from src import cities
from src.errors import CityError


def test_default_city_resolves():
    key, city = cities.get_city(cities.DEFAULT_CITY_KEY)
    assert key == "jacksonvilleFL"
    assert city["label"] == "Jacksonville, FL"


def test_unknown_city_raises():
    with pytest.raises(CityError):
        cities.get_city("nowhereXYZ")
