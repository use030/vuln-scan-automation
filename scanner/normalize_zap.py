from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

from scanner.models import Evidence, Finding, RISK_LABELS, RISK_RANK, ScanReport, to_dict


def strip_html(value: str) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_references(value: str) -> list[str]:
    if not value:
        return []
    text = html.unescape(value)
    refs = re.findall(r"https?://[^\s<>)]+", text)
    return sorted(set(refs))


def risk_label(riskcode: str) -> str:
    return RISK_LABELS.get(str(riskcode), "Unknown")


def load_zap_report(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _finding_id(plugin_id: str, title: str, severity: str) -> str:
    raw = f"{plugin_id}:{title}:{severity}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def normalize_zap_report(report: dict, target: str = "", scan_type: str = "baseline") -> ScanReport:
    findings: list[Finding] = []
    summary = {
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Informational": 0,
        "Unknown": 0,
    }

    sites = report.get("site", [])
    target_name = target
    if not target_name and sites:
        target_name = sites[0].get("@name", "")

    for site in sites:
        for alert in site.get("alerts", []):
            title = alert.get("alert") or alert.get("name") or "Unknown Alert"
            plugin_id = str(alert.get("pluginid", ""))
            severity = risk_label(alert.get("riskcode", ""))
            summary[severity if severity in summary else "Unknown"] += 1

            evidence_items: list[Evidence] = []
            affected_urls: list[str] = []

            for instance in alert.get("instances", []):
                uri = instance.get("uri", "")
                if uri and uri not in affected_urls:
                    affected_urls.append(uri)

                evidence_items.append(
                    Evidence(
                        uri=uri,
                        method=instance.get("method", ""),
                        param=instance.get("param", ""),
                        attack=instance.get("attack", ""),
                        evidence=instance.get("evidence", ""),
                        other_info=strip_html(instance.get("otherinfo", "")),
                    )
                )

            findings.append(
                Finding(
                    id=_finding_id(plugin_id, title, severity),
                    title=title,
                    severity=severity,
                    severity_rank=RISK_RANK.get(severity, -1),
                    confidence=str(alert.get("confidence", "")),
                    cwe=str(alert.get("cweid", "")),
                    wasc=str(alert.get("wascid", "")),
                    plugin_id=plugin_id,
                    count=len(alert.get("instances", [])),
                    affected_urls=affected_urls,
                    evidence=evidence_items,
                    description=strip_html(alert.get("desc", "")),
                    remediation=strip_html(alert.get("solution", "")),
                    references=extract_references(alert.get("reference", "")),
                )
            )

    findings.sort(key=lambda item: (item.severity_rank, item.count), reverse=True)

    generated_at = report.get("created") or dt.datetime.now(dt.UTC).isoformat()
    scan_id = hashlib.sha256(f"{target_name}:{generated_at}:{scan_type}".encode("utf-8")).hexdigest()[:16]

    return ScanReport(
        id=scan_id,
        target=target_name,
        scan_type=scan_type,
        generated_at=generated_at,
        zap_version=report.get("@version", "unknown"),
        status="completed",
        summary=summary,
        findings=findings,
    )


def write_normalized_report(report: ScanReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(to_dict(report), file, ensure_ascii=False, indent=2)
