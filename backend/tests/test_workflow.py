"""Alert workflow schema tests."""

import pytest
from pydantic import ValidationError

from app.schemas.phase2 import AlertWorkflowUpdate


def test_valid_lifecycle_state():
    m = AlertWorkflowUpdate(lifecycle_state="investigating")
    assert m.lifecycle_state == "investigating"


def test_invalid_lifecycle_state():
    with pytest.raises(ValidationError):
        AlertWorkflowUpdate(lifecycle_state="invalid")
