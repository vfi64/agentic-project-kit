"""Conservative classification for retrying GitHub reads, never mutations."""
from __future__ import annotations


def transient_github_read_failure(message: str) -> bool:
    text = message.lower()
    if any(value in text for value in (
        "rate limit", "http 401", "http 403", "bad credentials", "forbidden",
        "unauthorized", "permission denied",
    )):
        return False
    return any(value in text for value in (
        "http 502", "http 503", "http 504", "tls handshake timeout",
        "connection reset by peer", "temporary failure in name resolution",
    ))
