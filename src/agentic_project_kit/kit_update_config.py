"""Validated optional workspace configuration for Kit installation maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


DEFAULT_INDEX_URL = "https://pypi.org/simple"


@dataclass(frozen=True)
class KitUpdateConfig:
    interpreter: str = ""
    index_url: str = DEFAULT_INDEX_URL


def validate_download_url(url: str) -> None:
    parsed = urlsplit(url)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ValueError("Kit package URLs require HTTPS (HTTP is allowed only on loopback)")
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Kit package URLs must not contain credentials or fragments")


def parse_kit_update_config(value: object) -> KitUpdateConfig:
    if value is None:
        return KitUpdateConfig()
    if not isinstance(value, dict) or set(value) - {"interpreter", "index_url"}:
        raise ValueError("kit must be a mapping with only interpreter and index_url")
    interpreter = value.get("interpreter", "")
    index = value.get("index_url", DEFAULT_INDEX_URL)
    if not isinstance(interpreter, str) or "\x00" in interpreter:
        raise ValueError("kit.interpreter must be a filesystem path string")
    if not isinstance(index, str) or not index.strip():
        raise ValueError("kit.index_url must be a nonempty URL")
    validate_download_url(index)
    if urlsplit(index).query:
        raise ValueError("kit.index_url must not contain query parameters")
    return KitUpdateConfig(interpreter, index.rstrip("/"))
