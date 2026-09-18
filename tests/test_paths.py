import pytest

from mediapy.errors import InvalidName
from mediapy.paths import safe_stem


def test_safe_stem_strips_extension():
    assert safe_stem("foo.mp4") == "foo"
    assert safe_stem("foo") == "foo"


def test_safe_stem_takes_basename():
    assert safe_stem("a/foo.mp4") == "foo"


@pytest.mark.parametrize("bad", ["../evil", "a%b", "", "..", "."])
def test_safe_stem_rejects_invalid_names(bad):
    with pytest.raises(InvalidName):
        safe_stem(bad)
