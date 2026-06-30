from __future__ import annotations

import datetime as dt
from pathlib import Path

from scanner.models import RISK_RANK


def build_markdown_report(report: dict) -> str:
    lines: list[str] = []
    summary = report.get("summary", {})
    findings = report.get("findings", [])

    lines.append("# Security Assessment Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Target: `{report.get('target', '-')}`")
    lines.append(f"- Scan Type: `{report.get('scan_type', '-')}`")
    lines.append(f"- ZAP Version: `{report.get('zap_version', '-')}`")
    lines.append(f"- Generated At: `{dt.datetime.now(dt.UTC).isoformat()}`")
    lines.append(f"- Finding Count: `{len(findings)}`")
    lines.append("")

    lines.append("## Severity Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---:|")
    for severity in ["High", "Medium", "Low", "Informational", "Unknown"]:
        lines.append(f"| {severity} | {summary.get(severity, 0)} |")
    lines.append("")

    lines.append("## Priority Findings")
    lines.append("")
    actionable = [item for item in findings if RISK_RANK.get(item.get("severity", "Unknown"), -1) >= 1]
    if not actionable:
        lines.append("No actionable findings were detected.")
        lines.append("")
    else:
        lines.append("| Severity | Finding | Count | CWE | Example URL |")
        lines.append("|---|---|---:|---|---|")
        for finding in actionable:
            urls = finding.get("affected_urls") or []
            example = urls[0] if urls else "-"
            lines.append(
                f"| {finding.get('severity', '-')} | {finding.get('title', '-')} | "
                f"{finding.get('count', 0)} | {finding.get('cwe') or '-'} | `{example}` |"
            )
        lines.append("")

    lines.append("## Finding Details")
    lines.append("")
    if not findings:
        lines.append("No findings were detected.")
        lines.append("")

    for index, finding in enumerate(findings, start=1):
        lines.append(f"### {index}. {finding.get('title', 'Unknown Finding')}")
        lines.append("")
        lines.append(f"- Severity: {finding.get('severity', '-')}")
        lines.append(f"- Confidence: {finding.get('confidence', '-')}")
        lines.append(f"- Plugin ID: {finding.get('plugin_id', '-')}")
        lines.append(f"- CWE: {finding.get('cwe') or '-'}")
        lines.append(f"- WASC: {finding.get('wasc') or '-'}")
        lines.append(f"- Instance Count: {finding.get('count', 0)}")
        lines.append("")

        urls = finding.get("affected_urls") or []
        if urls:
            lines.append("Affected URLs:")
            for url in urls[:5]:
                lines.append(f"- `{url}`")
            lines.append("")

        evidence_items = finding.get("evidence") or []
        evidence_values = []
        for evidence in evidence_items:
            value = evidence.get("evidence") if isinstance(evidence, dict) else ""
            if value and value not in evidence_values:
                evidence_values.append(value)
        if evidence_values:
            lines.append("Evidence:")
            for value in evidence_values[:3]:
                lines.append(f"- `{value}`")
            lines.append("")

        if finding.get("description"):
            lines.append("Description:")
            lines.append("")
            lines.append(f"> {finding['description']}")
            lines.append("")

        if finding.get("remediation"):
            lines.append("Recommended Fix:")
            lines.append("")
            lines.append(f"> {finding['remediation']}")
            lines.append("")

    return "\n".join(lines)


def write_final_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        file.write(build_markdown_report(report))
        file.write("\n")
