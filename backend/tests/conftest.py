"""
Shared test fixtures for the Gambling Comment Detector backend tests.
"""

import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis profiles
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=50, deadline=None)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Use dev profile by default
settings.load_profile("dev")


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest-asyncio default fixture loop scope."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test."
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"
