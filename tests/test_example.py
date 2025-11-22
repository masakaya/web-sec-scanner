"""Example test file."""

import pytest


def test_example():
    """Basic example test."""
    assert 1 + 1 == 2


def test_string_operations():
    """Test string operations."""
    text = "Hello, World!"
    assert text.lower() == "hello, world!"
    assert text.upper() == "HELLO, WORLD!"
    assert len(text) == 13


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, 2),
        (2, 4),
        (3, 6),
        (10, 20),
    ],
)
def test_double(input_value, expected):
    """Test parametrized values."""
    assert input_value * 2 == expected


class TestExample:
    """Example test class."""

    def test_addition(self):
        """Test addition."""
        assert 2 + 2 == 4

    def test_subtraction(self):
        """Test subtraction."""
        assert 5 - 3 == 2

    @pytest.mark.slow
    def test_slow_operation(self):
        """This is a slow test (marked)."""
        import time

        time.sleep(0.1)
        assert True


@pytest.fixture
def sample_data():
    """Sample fixture."""
    return {"name": "Test", "value": 42}


def test_fixture_usage(sample_data):
    """Test using a fixture."""
    assert sample_data["name"] == "Test"
    assert sample_data["value"] == 42
