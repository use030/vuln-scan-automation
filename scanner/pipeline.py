from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from scanner.models import RISK_RANK, to_dict
from scanner.normalize_zap import load_zap_report, normalize_zap_report, write_normalized_report
from scanner.report import write_final_report
from scanner.redact import redact_report


# Read environment variables injected by Docker Compose or the shell.
def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def resolve_raw_report(report_dir: Path) -> Path:
    configured = env("RAW_REPORT_PATH")
    if configured:
        path = Path(configured)
        if path.exists():
            return path

    # Fallback: use the first JSON report generated under reports/raw.
    candidates = sorted((report_dir / "raw").glob("*.json"))
    if candidates:
        return candidates[0]

    raise FileNotFoundError(f"No raw ZAP JSON report found in {report_dir / 'raw'}")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def should_fail(report: dict, fail_on: str) -> bool:
    if fail_on == "none":
        return False

    threshold = RISK_RANK[fail_on.capitalize()]
    for finding in report.get("findings", []):
        if finding.get("severity_rank", -1) >= threshold:
            return True
    return False


def main() -> int:
    report_dir = Path(env("REPORT_DIR", "reports"))
    target_url = env("TARGET_URL")
    scan_mode = env("SCAN_MODE", "baseline")
    fail_on = env("FAIL_ON", "none").lower()

    if fail_on not in {"none", "low", "medium", "high"}:
        print(f"Invalid FAIL_ON value: {fail_on}", file=sys.stderr)
        return 2

    raw_path = resolve_raw_report(report_dir)
    normalized_path = report_dir / "normalized" / "normalized-report.json"
    redacted_path = report_dir / "normalized" / "redacted-report.json"
    final_path = report_dir / "final" / "security-report.md"

    print(f"Reading raw ZAP report: {raw_path}")
    raw_report = load_zap_report(raw_path)

    normalized = normalize_zap_report(raw_report, target=target_url, scan_type=scan_mode)
    write_normalized_report(normalized, normalized_path)
    print(f"Normalized report written: {normalized_path}")

    normalized_dict = to_dict(normalized)
    redacted = redact_report(normalized_dict)
    write_json(redacted_path, redacted)
    print(f"Redacted report written: {redacted_path}")

    write_final_report(redacted, final_path)
    print(f"Final Markdown report written: {final_path}")

    if should_fail(normalized_dict, fail_on):
        print(f"Security gate failed: findings >= {fail_on}")
        return 1

    print("Security gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

