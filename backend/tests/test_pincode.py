import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.pincode_mapper import get_region_from_pincode


def test_karnataka_prefix():
    info = get_region_from_pincode("560001")
    assert info is not None
    assert info["state"] == "Karnataka"
    assert info["agro_zone"] == "Deccan-South"


def test_delhi_prefix():
    info = get_region_from_pincode("110001")
    assert info is not None
    assert info["state"] == "Delhi"


def test_punjab_prefix():
    info = get_region_from_pincode("141001")
    assert info["state"] == "Punjab"


def test_invalid_pincode():
    assert get_region_from_pincode("abc") is None
    assert get_region_from_pincode("123") is None
