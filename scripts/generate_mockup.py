#!/usr/bin/env python3
"""
Generate HTML mockup from ZAP JSON report
"""
import json
from pathlib import Path

def load_zap_json(json_path: Path) -> dict:
    """Load ZAP JSON report"""
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def convert_to_mockup_data(zap_data: dict) -> dict:
    """Convert ZAP JSON to mockup data format"""
    site_info = zap_data.get("site", [{}])[0]
    site_name = site_info.get("@name", "Unknown")
    alerts = site_info.get("alerts", [])

    # Convert date format
    generated = zap_data.get("@generated", "")

    mockup_alerts = []
    mockup_summary = []

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
        unique_urls = len(set(inst.get("uri", "") for inst in instances))

        # Create summary entry
        summary_entry = {
            "name": alert.get("alert", "Unknown Alert"),
            "risk": risk,
            "count": int(alert.get("count", len(instances))),
            "urls": unique_urls,
            "description": alert.get("desc", "").replace("<p>", "").replace("</p>", "")[:200] + "..."
        }
        mockup_summary.append(summary_entry)

        # Process all instances for this alert
        instance_details = []
        for inst in instances:
            instance_detail = {
                "url": inst.get("uri", ""),
                "method": inst.get("method", "GET"),
                "param": inst.get("param", ""),
                "attack": inst.get("attack", ""),
                "evidence": inst.get("evidence", ""),
                "otherinfo": inst.get("otherinfo", "")
            }
            instance_details.append(instance_detail)

        mockup_alert = {
            "name": alert.get("alert", "Unknown Alert"),
            "risk": risk,
            "description": alert.get("desc", "").replace("<p>", "").replace("</p>", ""),
            "solution": alert.get("solution", "").replace("<p>", "").replace("</p>", ""),
            "reference": alert.get("reference", "").replace("<p>", "").replace("</p>", ""),
            "instances": instance_details
        }
        mockup_alerts.append(mockup_alert)

    return {
        "site": site_name,
        "date": generated,
        "summary": mockup_summary,
        "alerts": mockup_alerts
    }

def generate_mockup_html(mockup_data: dict, template_path: Path, output_path: Path):
    """Generate mockup HTML"""
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Convert data to JavaScript format
    summary_js = json.dumps(mockup_data["summary"], ensure_ascii=False, indent=4)
    alerts_js = json.dumps(mockup_data["alerts"], ensure_ascii=False, indent=4)

    # Replace the reportData in template
    mockup_html = template.replace(
        '        const reportData = {',
        f'''        const reportData = {{
            site: "{mockup_data['site']}",
            date: "{mockup_data['date']}",
            summary: {summary_js},
            alerts: {alerts_js}
        }};
        const reportData_old = {{'''
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mockup_html)

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    json_path = project_root / "tmp" / "scan-report.json"
    template_path = project_root / "tmp" / "sample.html"
    output_path = project_root / "tmp" / "mockup.html"

    print(f"Loading ZAP JSON from: {json_path}")
    zap_data = load_zap_json(json_path)

    print("Converting to mockup data...")
    mockup_data = convert_to_mockup_data(zap_data)
    print(f"Found {len(mockup_data['alerts'])} alerts")

    print(f"Generating mockup HTML: {output_path}")
    generate_mockup_html(mockup_data, template_path, output_path)

    print("✅ Mockup HTML generated successfully!")
