from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RISK_LABELS = {
    "3": "High",
    "2": "Medium",
    "1": "Low",
    "0": "Informational",
}

RISK_RANK = {
    "Informational": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Unknown": -1,
}


@dataclass
class Evidence:
    uri: str = ""
    method: str = ""
    param: str = ""
    attack: str = ""
    evidence: str = ""
    other_info: str = ""


@dataclass
class Finding:
    id: str
    title: str
    severity: str
    severity_rank: int
    confidence: str
    cwe: str
    wasc: str
    plugin_id: str
    count: int
    affected_urls: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    description: str = ""
    remediation: str = ""
    references: list[str] = field(default_factory=list)


@dataclass
class ScanReport:
    id: str
    target: str
    scan_type: str
    generated_at: str
    zap_version: str
    status: str
    summary: dict[str, int]
    findings: list[Finding]


def to_dict(value: Any) -> Any:
    return asdict(value)
