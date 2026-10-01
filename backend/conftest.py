import pytest
from app.core.rate_limiter import rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Resets the in-memory rate limiter before each test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()
