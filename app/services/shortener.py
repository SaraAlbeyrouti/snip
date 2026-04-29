import secrets


def generate_short_code(length: int = 7) -> str:
    """Generate a URL-safe random short code.

    Uses ``secrets.token_urlsafe`` (cryptographically random). The output may
    contain ``-`` and ``_``. Default 7 chars gives ~10^12 possible codes;
    collision risk for a portfolio-scale demo is negligible.
    """
    # token_urlsafe(n_bytes) returns roughly ceil(n_bytes * 4/3) characters.
    nbytes = max(1, (length * 3) // 4 + 1)
    return secrets.token_urlsafe(nbytes)[:length]
