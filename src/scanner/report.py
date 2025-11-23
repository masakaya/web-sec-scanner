#!/usr/bin/env python3
"""Security scan report generator using Jinja2 templates."""

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from prefect import flow, task

from src.utils.datetime_utils import convert_utc_to_jst


@task(name="Load ZAP JSON Report")
def load_zap_json(json_path: Path) -> dict[str, Any]:
    """Load ZAP JSON report."""
    with open(json_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


@task(name="Convert ZAP Data to Report Format")
def convert_zap_to_report_data(zap_data: dict[str, Any]) -> dict[str, Any]:
    """Convert ZAP JSON to report data format for Jinja2 template."""
    site_info = zap_data.get("site", [{}])[0]
    site_name = site_info.get("@name", "Unknown")
    alerts = site_info.get("alerts", [])
    created_utc = zap_data.get("created", "")
    generated = convert_utc_to_jst(created_utc) if created_utc else ""

    report_alerts = []
    summary_data = []

    for alert in alerts:
        # Get risk level in English
        risk_desc = alert.get("riskdesc", "")
        risk = "Informational"
        if "高" in risk_desc or "High" in risk_desc:
            risk = "High"
        elif "中" in risk_desc or "Medium" in risk_desc:
            risk = "Medium"
        elif "低" in risk_desc or "Low" in risk_desc:
            risk = "Low"

        # Get all instances for this alert
        instances = alert.get("instances", [])

        # Count unique URLs affected
        unique_urls = len({inst.get("uri", "") for inst in instances})

        # Create summary entry
        summary_entry = {
            "name": alert.get("alert", "Unknown Alert"),
            "risk": risk,
            "count": int(alert.get("count", len(instances))),
            "urls": unique_urls,
        }
        summary_data.append(summary_entry)

        # Process all instances for this alert
        instance_details = []
        for inst in instances:
            # Only include non-empty fields
            instance_detail = {
                "url": inst.get("uri", ""),
                "method": inst.get("method", "GET"),
            }

            # Add optional fields only if they have values
            if param := inst.get("param", "").strip():
                instance_detail["param"] = param
            if attack := inst.get("attack", "").strip():
                instance_detail["attack"] = attack
            if evidence := inst.get("evidence", "").strip():
                instance_detail["evidence"] = evidence
            if otherinfo := inst.get("otherinfo", "").strip():
                instance_detail["otherinfo"] = otherinfo

            instance_details.append(instance_detail)

        # Split reference URLs
        reference = alert.get("reference", "").replace("<p>", "").replace("</p>", "")
        reference_urls = []
        if reference:
            # Split by common URL patterns
            import re

            urls = re.findall(r"https?://[^\s]+", reference)
            reference_urls = urls if urls else [reference] if reference else []

        report_alert = {
            "name": alert.get("alert", "Unknown Alert"),
            "risk": risk,
            "description": alert.get("desc", "").replace("<p>", "").replace("</p>", ""),
            "solution": alert.get("solution", "")
            .replace("<p>", "")
            .replace("</p>", ""),
            "reference_urls": reference_urls,
            "instances": instance_details,
        }
        report_alerts.append(report_alert)

    # Sort by severity
    severity_order = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
    summary_data.sort(key=lambda x: severity_order.get(x["risk"], 4))
    report_alerts.sort(key=lambda x: severity_order.get(x["risk"], 4))

    return {
        "site": site_name,
        "date": generated,
        "summary": summary_data,
        "alerts": report_alerts,
    }


@task(name="Render HTML Report")
def render_html_report(
    report_data: dict[str, Any], template_dir: Path, output_path: Path
) -> Path:
    """Render HTML report using Jinja2 template."""
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("report.html.j2")

    html_content = template.render(**report_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


@flow(name="Generate Security Report")
def generate_security_report(json_path: Path, output_path: Path | None = None) -> Path:
    """Generate HTML security report from ZAP JSON.

    Args:
        json_path: Path to ZAP JSON report
        output_path: Output path for HTML report (default: security-report.html in same dir)

    Returns:
        Path to generated HTML report

    """
    if output_path is None:
        # Use security-report.html to avoid conflict with ZAP's scan-report.html
        output_path = json_path.parent / "security-report.html"

    # Get project root and template directory
    project_root = Path(__file__).parent.parent.parent
    template_dir = project_root / "resources" / "templates"

    # Load and convert data
    zap_data = load_zap_json(json_path)
    report_data = convert_zap_to_report_data(zap_data)

    # Render HTML report
    html_path = render_html_report(report_data, template_dir, output_path)

    return html_path


if __name__ == "__main__":
    # Example usage
    project_root = Path(__file__).parent.parent.parent
    json_path = project_root / "tmp" / "scan-report.json"
    output_path = project_root / "tmp" / "security-report.html"

    result = generate_security_report(json_path, output_path)
    print(f"✅ Report generated: {result}")
