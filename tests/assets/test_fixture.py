import pytest

@pytest.fixture
def fixt():
    return 1

def test_fixture(fixt):
    assert fixt == 1