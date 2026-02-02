#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a deterministic run report from audit artifacts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run_id", help="The specific run ID to report on.")
    group.add_argument("--run_dir", help="Path to a specific run directory.")
    group.add_argument("--latest", action="store_true", help="Report on the most recent run in outputs/.")

    parser.add_argument("--format", choices=["console", "json", "md"], default="console", help="Output format.")
    parser.add_argument("--write_md", action="store_true", help="Write the markdown report to outputs/<run_id>/audit_summary.md.")
    
    return parser.parse_args()

def find_latest_run_id(outputs_dir: Path) -> Optional[str]:
    if not outputs_dir.exists():
        return None
    
    runs = []
    pattern = re.compile(r"^\d{8}_\d{6}$")
    for d in outputs_dir.iterdir():
        if d.is_dir() and pattern.match(d.name):
             try:
                 runs.append((d.stat().st_mtime, d.name))
             except OSError:
                 continue
    
    if not runs:
        return None
        
    runs.sort(key=lambda x: x[0], reverse=True)
    return runs[0][1]

def find_all_recent_runs(outputs_dir: Path, limit: int = 10) -> List[str]:
    if not outputs_dir.exists():
        return []
    
    runs = []
    pattern = re.compile(r"^\d{8}_\d{6}$")
    for d in outputs_dir.iterdir():
         if d.is_dir() and pattern.match(d.name):
             try:
                 runs.append((d.stat().st_mtime, d.name))
             except OSError:
                 continue
    
    runs.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in runs[:limit]]

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}", file=sys.stderr)
        return None

def generate_report_data(run_dir: Path, audit_summary: Dict[str, Any], run_manifest: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    run_meta = audit_summary.get("run_metadata", {})
    manifest = run_manifest if run_manifest else {}

    gate_summary = audit_summary.get("gate_summary", {})
    open_questions_summary = audit_summary.get("open_questions_summary", {})
    
    # Header
    header = {
        "system_version": run_meta.get("system_version") or manifest.get("system_version", "unknown"),
        "run_id": run_meta.get("run_id", "UNKNOWN"),
        "end_state": audit_summary.get("end_state", "UNKNOWN"),
        "governance_profile": run_meta.get("governance_profile") or manifest.get("governance_profile", "N/A"),
        "auto_approve": run_meta.get("auto_approve") if "auto_approve" in run_meta else manifest.get("auto_approve", False),
        "risk_gate_escalation_enabled": run_meta.get("risk_gate_escalation_enabled", False),
        "open_questions_threshold": run_meta.get("open_questions_threshold") or manifest.get("open_questions_threshold", "N/A"),
        "weighted_severities": run_meta.get("weighted_severities") or manifest.get("weighted_severities", []),
        "failure_reason": audit_summary.get("failure_reason") or run_meta.get("failure_reason")
    }

    # Gates
    approvals = gate_summary.get("approvals", {})
    phase_gates = gate_summary.get("phase_gates", [])
    risk_gates = gate_summary.get("risk_gates", [])
    
    gates = {
        "approvals": approvals,
        "phase_gates_count": len(phase_gates),
        "risk_gates_count": len(risk_gates),
        "risk_gates_details": []
    }
    
    for rg in risk_gates:
        gates["risk_gates_details"].append({
            "step_idx": rg.get("step_idx"),
            "agent": rg.get("agent"),
            "gate_reason": rg.get("gate_reason"),
            "overridden": rg.get("overridden"),
            "approved_mode": rg.get("approved_mode", "N/A")
        })

    # Open Questions
    oq = {
        "total_count": open_questions_summary.get("total_count", 0),
        "severity_counts": open_questions_summary.get("severity_counts", {}),
        "top_5": open_questions_summary.get("top_10", [])[:5] # audit summary stores top_10
    }

    # Artifacts
    artifacts = {
        "audit_summary_path": str(run_dir / "audit_summary.json"),
        "run_manifest_path": str(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else None,
        "output_directory": str(run_dir)
    }

    return {
        "header": header,
        "gates": gates,
        "open_questions": oq,
        "artifacts": artifacts
    }

def print_console_report(data: Dict[str, Any]):
    h = data["header"]
    g = data["gates"]
    oq = data["open_questions"]
    a = data["artifacts"]

    print("\n=== RUN REPORT ===")
    if h.get('system_version') != "unknown":
        print(f"System Version:    {h['system_version']}")
    print(f"Run ID:            {h['run_id']}")
    print(f"End State:         {h['end_state']}" + (f" (Reason: {h['failure_reason']})" if h.get('failure_reason') else ""))
    print(f"Profile:           {h['governance_profile']}")
    print(f"Auto Approve:      {h['auto_approve']}")
    print(f"Risk Escalation:   {h['risk_gate_escalation_enabled']}")
    print(f"OQ Threshold:      {h['open_questions_threshold']}")
    ws_str = ", ".join(h['weighted_severities']) if h['weighted_severities'] else "None"
    print(f"Weighted Sevs:     [{ws_str}]")

    print("\n--- GATES ---")
    print(f"Approvals:         Manual: {g['approvals'].get('manual', 0)} | Auto: {g['approvals'].get('auto', 0)}")
    print(f"Phase Gates:       {g['phase_gates_count']}")
    print(f"Risk Gates:        {g['risk_gates_count']}")
    
    if g["risk_gates_details"]:
        print("\n  Risk Gate Details:")
        for rg in g["risk_gates_details"]:
            print(f"    - Step {rg['step_idx']} ({rg['agent']}): Reason='{rg['gate_reason']}', Overridden={rg['overridden']}, Mode={rg['approved_mode']}")

    print("\n--- OPEN QUESTIONS ---")
    print(f"Total Count:       {oq['total_count']}")
    if oq['severity_counts']:
        sc = oq['severity_counts']
        sc_str = ", ".join([f"{k}={v}" for k, v in sc.items()])
        print(f"Severity Counts:   {sc_str}")
    
    if oq['top_5']:
        print("\n  Top 5 Open Questions:")
        for q in oq['top_5']:
            print(f"    - {q}")

    print("\n--- ARTIFACTS ---")
    print(f"Audit Summary:     {a['audit_summary_path']}")
    print(f"Run Manifest:      {a['run_manifest_path'] or 'N/A'}")
    print(f"Output Dir:        {a['output_directory']}")
    print("==================\n")

def generate_markdown_report(data: Dict[str, Any]) -> str:
    h = data["header"]
    g = data["gates"]
    oq = data["open_questions"]
    a = data["artifacts"]
    
    lines = []
    lines.append(f"# Run Report: {h['run_id']}")
    if h.get('system_version') != "unknown":
        lines.append(f"**System Version**: {h['system_version']}")
    lines.append("")
    lines.append("## Run Header")
    lines.append(f"- **End State**: {h['end_state']}")
    if h.get('failure_reason'):
        lines.append(f"- **Failure Reason**: {h['failure_reason']}")
    lines.append(f"- **Governance Profile**: {h['governance_profile']}")
    lines.append(f"- **Auto Approve**: {h['auto_approve']}")
    lines.append(f"- **Risk Gate Escalation**: {h['risk_gate_escalation_enabled']}")
    lines.append(f"- **Open Questions Threshold**: {h['open_questions_threshold']}")
    ws_str = ", ".join(h['weighted_severities']) if h['weighted_severities'] else "None"
    lines.append(f"- **Weighted Severities**: `{ws_str}`")

    lines.append("")
    lines.append("## Gates")
    lines.append(f"- **Manual Approvals**: {g['approvals'].get('manual', 0)}")
    lines.append(f"- **Auto Approvals**: {g['approvals'].get('auto', 0)}")
    lines.append(f"- **Phase Gates Count**: {g['phase_gates_count']}")
    lines.append(f"- **Risk Gates Count**: {g['risk_gates_count']}")
    
    if g["risk_gates_details"]:
        lines.append("")
        lines.append("### Risk Gate Details")
        lines.append("| Step | Agent | Reason | Overridden | Mode |")
        lines.append("|---|---|---|---|---|")
        for rg in g["risk_gates_details"]:
            lines.append(f"| {rg['step_idx']} | {rg['agent']} | {rg['gate_reason']} | {rg['overridden']} | {rg['approved_mode']} |")

    lines.append("")
    lines.append("## Open Questions")
    lines.append(f"- **Total Count**: {oq['total_count']}")
    if oq['severity_counts']:
        sc = oq['severity_counts']
        lines.append("- **Severity Counts**:")
        for k, v in sc.items():
            lines.append(f"  - {k}: {v}")
    
    if oq['top_5']:
        lines.append("")
        lines.append("### Top 5 Open Questions")
        for q in oq['top_5']:
            lines.append(f"- {q}")

    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- **Audit Summary**: `{a['audit_summary_path']}`")
    lines.append(f"- **Run Manifest**: `{a['run_manifest_path'] or 'N/A'}`")
    lines.append(f"- **Output Directory**: `{a['output_directory']}`")
    
    return "\n".join(lines)

def main():
    args = parse_args()
    
    root_dir = Path(os.getcwd())
    outputs_dir = root_dir / "outputs"
    
    run_id = None
    run_dir = None
    
    if args.run_id:
        run_id = args.run_id
        run_dir = outputs_dir / run_id
    elif args.run_dir:
        run_dir = Path(args.run_dir)
        run_id = run_dir.name
    elif args.latest:
        run_id = find_latest_run_id(outputs_dir)
        if not run_id:
            print("No recent runs found in outputs/.", file=sys.stderr)
            sys.exit(1)
        run_dir = outputs_dir / run_id

    if not run_dir or not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}", file=sys.stderr)
        if outputs_dir.exists():
             recent = find_all_recent_runs(outputs_dir)
             if recent:
                 print("Available recent runs:", file=sys.stderr)
                 for r in recent:
                     print(f"  - {r}", file=sys.stderr)
        sys.exit(1)

    audit_path = run_dir / "audit_summary.json"
    manifest_path = run_dir / "run_manifest.json"
    
    if not audit_path.exists():
        print(f"Error: audit_summary.json not found in {run_dir}", file=sys.stderr)
        sys.exit(1)

    audit_summary = load_json(audit_path)
    run_manifest = load_json(manifest_path)
    
    if not audit_summary:
        print("Error: Failed to load audit_summary.json", file=sys.stderr)
        sys.exit(1)

    report_data = generate_report_data(run_dir, audit_summary, run_manifest)
    
    # Handle Output
    if args.format == "json":
        print(json.dumps(report_data, indent=2))
    elif args.format == "md":
        print(generate_markdown_report(report_data))
    else:
        print_console_report(report_data)
        if (Path(__file__).parent / "run_diff.py").exists():
            print("Tip: To compare runs, use: python3 scripts/run_diff.py <run_a> <run_b>")

    # Handle Write MD
    if args.write_md:
        md_content = generate_markdown_report(report_data)
        out_md_path = run_dir / "audit_summary.md"
        try:
            with open(out_md_path, 'w') as f:
                f.write(md_content)
            print(f"\nReport written to: {out_md_path}")
        except Exception as e:
            print(f"Error writing markdown report: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
