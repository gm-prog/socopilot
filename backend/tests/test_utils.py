import pytest
from app.core.utils import AttributeDict


def test_attribute_dict_access_and_set():
    """Test getting and setting keys via dot notation."""
    d = AttributeDict()
    d.foo = "bar"

    # Verify dot notation access & normal dict access work identically
    assert d.foo == "bar"
    assert d["foo"] == "bar"

    # Verify updating values via dot notation
    d.foo = "baz"
    assert d.foo == "baz"
    assert d["foo"] == "baz"


def test_attribute_dict_missing_attribute():
    """Test raising AttributeError when accessing a non-existent key."""
    d = AttributeDict()
    d["existing"] = 123

    with pytest.raises(AttributeError) as exc_info:
        _ = d.non_existent

    assert "'AttributeDict' object has no attribute 'non_existent'" in str(exc_info.value)
