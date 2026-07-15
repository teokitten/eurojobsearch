import pytest
from app import _normalize_title_for_dedup


@pytest.mark.parametrize("a, b", [
    ("Content Manager (M/W/D)*", "Content Manager (M/F/D)*"),
    ("Developer (w/m/d)",        "Developer (m/f/d)"),
    ("Engineer [M/W/X]",         "Engineer [m/f/x]"),
    ("Designer (all genders)",   "Designer (M/W/D)"),
])
def test_gender_variants_normalize_equal(a, b):
    assert _normalize_title_for_dedup(a) == _normalize_title_for_dedup(b)


@pytest.mark.parametrize("raw, expected", [
    ("Content Manager (M/W/D)*",  "Content Manager"),
    ("Developer (m / w / d)",     "Developer"),
    ("Engineer [m/f/x]",          "Engineer"),
    ("Designer (all genders)",    "Designer"),
    ("Frontend Dev (w/m/d)*",     "Frontend Dev"),
    ("Developer",                 "Developer"),
    ("Frontend Developer (React)", "Frontend Developer (React)"),
])
def test_gender_marker_stripped(raw, expected):
    assert _normalize_title_for_dedup(raw) == expected
