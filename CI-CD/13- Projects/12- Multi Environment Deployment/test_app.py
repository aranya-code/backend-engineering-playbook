import pytest
from app import release_target

@pytest.mark.parametrize("environment", ["staging", "production"])
def test_release_target(environment):
    assert release_target(environment) == environment

def test_invalid_environment():
    with pytest.raises(ValueError):
        release_target("dev")
