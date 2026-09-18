from src import geo


def test_haversine_zero_distance():
    assert geo.haversine_miles(30.0, -80.0, 30.0, -80.0) == 0


def test_haversine_known_distance():
    jax = (30.3322, -81.6557)
    orl = (28.5383, -81.3792)
    d = geo.haversine_miles(jax[0], jax[1], orl[0], orl[1])
    assert 110 < d < 140  # Jacksonville <-> Orlando is roughly 120mi


def test_bounding_box_contains_center():
    bbox = geo.bounding_box(30.3322, -81.6557, 100)
    assert bbox["lamin"] < 30.3322 < bbox["lamax"]
    assert bbox["lomin"] < -81.6557 < bbox["lomax"]


def test_bounding_box_clamps_latitude_near_pole():
    bbox = geo.bounding_box(89.5, 0.0, 100)
    assert bbox["lamax"] <= 90.0
