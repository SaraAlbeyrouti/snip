"""Unit tests for app.services.shortener.

These don't touch the DB or HTTP, pure function tests.
"""

from app.services.shortener import generate_short_code


def test_generate_short_code_default_length() -> None:
    code = generate_short_code()
    assert len(code) == 7


def test_generate_short_code_custom_length() -> None:
    code = generate_short_code(length=12)
    assert len(code) == 12


def test_generate_short_code_unique_over_1000_samples() -> None:
    codes = {generate_short_code() for _ in range(1000)}
    # Collisions should be vanishingly rare for 1000 samples; require all unique.
    assert len(codes) == 1000


def test_generate_short_code_url_safe() -> None:
    """Codes must contain only URL-safe characters."""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    for _ in range(100):
        code = generate_short_code()
        assert set(code).issubset(allowed), f"Invalid chars in code: {code}"
