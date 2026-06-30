from __future__ import annotations

import copy
import re
from typing import Any


SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "apikey",
    "access_token",
    "refresh_token",
    "session",
    "sessionid",
    "session_id",
    "token",
    "password",
    "passwd",
    "secret",
}

PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"(?i)(access_token|refresh_token|token|api_key|apikey|sessionid|session_id)=([^&\s]+)"), r"\1=[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "[REDACTED_JWT]"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b(?:10|127|172\.(?:1[6-9]|2\d|3[0-1])|192\.168)\.\d{1,3}\.\d{1,3}\b"), "[REDACTED_INTERNAL_IP]"),
]


def redact_string(value: str) -> str:
    redacted = value
    for pattern, replacement in PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any, key: str = "") -> Any:
    normalized_key = key.lower()

    if normalized_key in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {item_key: redact_value(item_value, item_key) for item_key, item_value in value.items()}

    if isinstance(value, list):
        return [redact_value(item) for item in value]

    if isinstance(value, str):
        return redact_string(value)

    return value


def redact_report(report: dict) -> dict:
    return redact_value(copy.deepcopy(report))
