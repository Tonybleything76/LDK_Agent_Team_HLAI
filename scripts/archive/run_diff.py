#!/usr/bin/env python3
import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime

# --- Constants & Configuration ---
OUTPUTS_DIR = Path("outputs")
RUN_ID_PATTERN = re.compile(r"^\d{8}_\d{6}$")

# --- Data Loading & Discovery ---

def get_recent_runs(limit: int = 50) -> List[str]:
    """Return list of run_ids sorted desc by time."""
    if not OUTPUTS_DIR.exists():
        return []
    
    runs = []
    for d in OUTPUTS_DIR.iterdir():
        if d.is_dir() and RUN_ID_PATTERN.match(d.name):
            runs.append(d.name)
    
    return sorted(runs, reverse=True)[:limit]

def resolve_run_path(identifier: str) -> Path:
    """Resolve a run identifier (ID or path) to a directory Path."""
    # 1. Check if it's a directory path
    p = Path(identifier)
    if p.exists() and p.is_dir():
        return p
    
    # 2. Check if it's a run_id in outputs/
    p_run = OUTPUTS_DIR / identifier
    if p_run.exists() and p_run.is_dir():
        return p_run
        
    return None

def load_run_data(run_dir: Path) -> Dict[str, Any]:
    """
    Load audit_summary.json (required) and run_manifest.json (optional fallback).
    Returns a normalized dictionary with 'audit' and 'manifest' keys.
    """
    audit_path = run_dir / "audit_summary.json"
    manifest_path = run_dir / "run_manifest.json"
    
    if not audit_path.exists():
        print(f"Error: Mandatory file missing: {audit_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(audit_path, 'r') as f:
            audit_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse {audit_path}: {e}", file=sys.stderr)
        sys.exit(1)

    manifest_data = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError:
            # Manifest is optional, warn but don't fail? Or fail strict?
            # Prompt says "Load ... (optional fallback)", imply warn is ok or ignore.
            # But "If JSON parse fails, show file and error and exit non-zero." applies generally.
            print(f"Error: Failed to parse {manifest_path}", file=sys.stderr)
            sys.exit(1)
            
    return {
        "path": str(run_dir),
        "audit": audit_data,
        "manifest": manifest_data,
        "audit_path": str(audit_path),
        "manifest_path": str(manifest_path) if manifest_path.exists() else None
    }

def get_field(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """Helper to deeply access dict."""
    curr = data
    for key in path:
        if isinstance(curr, dict) and key in curr:
            curr = curr[key]
        else:
            return default
    return curr

def resolve_header_value(data: Dict[str, Any], field_name: str, audit_keys: List[str], manifest_keys: List[str]) -> Any:
    """Try to find value in audit, then manifest, then 'Unknown'/'None'.""" 
    val = get_field(data['audit'], audit_keys)
    if val is not None:
        return val
    
    val = get_field(data['manifest'], manifest_keys)
    if val is not None:
        return val
        
    return "Unknown"

# --- Comparison Logic ---

def compare_runs(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the diff structure."""
    
    # 1. Header
    def get_h(data, field):
        # Common locations for header fields
        # Most are in run_metadata in audit
        return resolve_header_value(
            data, field, 
            ['run_metadata', field], 
            [field] # often at top level in manifest or similar keys
        )

    # Specific mapping for complex lookups if needed, but standardizing on simpler func for readability
    header = {}
    
    # System Version
    header['system_version'] = {
        'A': resolve_header_value(run_a, 'system_version', ['run_metadata', 'system_version'], ['system_version']),
        'B': resolve_header_value(run_b, 'system_version', ['run_metadata', 'system_version'], ['system_version'])
    }
    
    # Run ID
    header['run_id'] = {
        'A': resolve_header_value(run_a, 'run_id', ['run_metadata', 'run_id'], ['run_id']),
        'B': resolve_header_value(run_b, 'run_id', ['run_metadata', 'run_id'], ['run_id'])
    }
    
    # End State
    # Only in audit usually
    header['end_state'] = {
        'A': run_a['audit'].get('end_state', 'Unknown'),
        'B': run_b['audit'].get('end_state', 'Unknown')
    }
    
    # Failure Reason
    # Check audit["failure_reason"] then audit["run_metadata"]["failure_reason"]
    def get_fail_reason(d):
        fr = d['audit'].get('failure_reason')
        if not fr:
            fr = d['audit'].get('run_metadata', {}).get('failure_reason')
        return fr
    
    fr_a = get_fail_reason(run_a)
    fr_b = get_fail_reason(run_b)
    if fr_a or fr_b:
        header['failure_reason'] = {'A': fr_a, 'B': fr_b}
        
    # Governance Profile
    header['governance_profile'] = {
        'A': get_h(run_a, 'governance_profile'),
        'B': get_h(run_b, 'governance_profile')
    }
    
    # Auto Approve
    header['auto_approve'] = {
        'A': get_h(run_a, 'auto_approve'),
        'B': get_h(run_b, 'auto_approve')
    }
    
    # Risk Gate Escalation
    header['risk_gate_escalation_enabled'] = {
        'A': get_h(run_a, 'risk_gate_escalation_enabled'),
        'B': get_h(run_b, 'risk_gate_escalation_enabled')
    }
    
    # Open Questions Threshold
    header['open_questions_threshold'] = {
        'A': get_h(run_a, 'open_questions_threshold'),
        'B': get_h(run_b, 'open_questions_threshold')
    }
    
    # Weighted Severities
    header['weighted_severities'] = {
        'A': get_h(run_a, 'weighted_severities'),
        'B': get_h(run_b, 'weighted_severities')
    }

    # 2. Gates Diff
    gates = {}
    
    # Approvals
    def get_app(d, key):
        return d['audit'].get('gate_summary', {}).get('approvals', {}).get(key, 0)
    
    gates['approvals.manual'] = {'A': get_app(run_a, 'manual'), 'B': get_app(run_b, 'manual')}
    gates['approvals.auto'] = {'A': get_app(run_a, 'auto'), 'B': get_app(run_b, 'auto')}
    
    # Phase Gates Count
    def get_pg_len(d):
        return len(d['audit'].get('gate_summary', {}).get('phase_gates', []))
    gates['phase_gates_count'] = {'A': get_pg_len(run_a), 'B': get_pg_len(run_b)}
    
    # Risk Gates Count
    def get_rg_len(d):
        return len(d['audit'].get('gate_summary', {}).get('risk_gates', []))
    gates['risk_gates_count'] = {'A': get_rg_len(run_a), 'B': get_rg_len(run_b)}

    # Risk Gate Reasons
    def get_rg_reasons_counts(d):
        rgs = d['audit'].get('gate_summary', {}).get('risk_gates', [])
        counts = {}
        for rg in rgs:
            r = rg.get('gate_reason', 'unknown')
            counts[r] = counts.get(r, 0) + 1
        return counts

    rg_reasons_a = get_rg_reasons_counts(run_a)
    rg_reasons_b = get_rg_reasons_counts(run_b)
    
    all_reasons = sorted(list(set(rg_reasons_a.keys()) | set(rg_reasons_b.keys())))
    gate_reason_counts = {}
    for r in all_reasons:
        gate_reason_counts[r] = {'A': rg_reasons_a.get(r, 0), 'B': rg_reasons_b.get(r, 0)}
        
    new_gate_reasons = sorted([r for r in rg_reasons_b if r not in rg_reasons_a])
    removed_gate_reasons = sorted([r for r in rg_reasons_a if r not in rg_reasons_b])
    
    gates['risk_gate_reasons'] = {
        'counts': gate_reason_counts,
        'new': new_gate_reasons,
        'removed': removed_gate_reasons
    }

    # 3. Open Questions Diff
    oq = {}
    def get_oq_summary(d):
        return d['audit'].get('open_questions_summary', {})
    
    oq_sum_a = get_oq_summary(run_a)
    oq_sum_b = get_oq_summary(run_b)
    
    oq['total_count'] = {'A': oq_sum_a.get('total_count', 0), 'B': oq_sum_b.get('total_count', 0)}
    
    # Severity counts
    sev_a = oq_sum_a.get('severity_counts', {})
    sev_b = oq_sum_b.get('severity_counts', {})
    all_sev = sorted(list(set(sev_a.keys()) | set(sev_b.keys())))
    
    severity_diff = {}
    for s in all_sev:
        severity_diff[s] = {'A': sev_a.get(s, 0), 'B': sev_b.get(s, 0)}
    oq['severity_counts'] = severity_diff
    
    # Sets
    top_a = set(oq_sum_a.get('top_10', []))
    top_b = set(oq_sum_b.get('top_10', []))
    
    # Exact string match
    new_qs = sorted(list(top_b - top_a))
    resolved_qs = sorted(list(top_a - top_b))
    
    # Limit to 10
    oq['top_delta'] = {
        'new': new_qs[:10],
        'resolved': resolved_qs[:10],
        'new_count': len(new_qs),
        'resolved_count': len(resolved_qs)
    }
    
    # 4. Artifacts
    artifacts = {
        'audit_summary_a': run_a['audit_path'],
        'audit_summary_b': run_b['audit_path'],
        'run_manifest_a': run_a['manifest_path'],
        'run_manifest_b': run_b['manifest_path']
    }
    
    return {
        'header': header,
        'gates': gates,
        'open_questions': oq,
        'artifacts': artifacts
    }

# --- Formatting ---

def format_val(val):
    if val is None: return "null"
    if isinstance(val, bool): return str(val).lower()
    return str(val)

def render_console(diff: Dict[str, Any]) -> str:
    lines = []
    lines.append("=== RUN DIFF REPORT ===")
    
    # Header
    lines.append("\n[HEADER]")
    h = diff['header']
    keys = ['system_version', 'run_id', 'end_state', 'failure_reason', 
            'governance_profile', 'auto_approve', 'risk_gate_escalation_enabled',
            'open_questions_threshold', 'weighted_severities']
            
    # Calculate padding for alignment
    max_key = max(len(k) for k in keys if k in h)
    
    for k in keys:
        if k not in h: continue
        val_a = format_val(h[k]['A'])
        val_b = format_val(h[k]['B'])
        sep = "->" if val_a != val_b else "=="
        lines.append(f"{k.ljust(max_key)} : {val_a} {sep} {val_b}")

    # Gates
    lines.append("\n[GATES]")
    g = diff['gates']
    
    # Approvals
    lines.append(f"approvals.manual         : {g['approvals.manual']['A']} -> {g['approvals.manual']['B']}")
    lines.append(f"approvals.auto           : {g['approvals.auto']['A']} -> {g['approvals.auto']['B']}")
    lines.append(f"phase_gates_count        : {g['phase_gates_count']['A']} -> {g['phase_gates_count']['B']}")
    lines.append(f"risk_gates_count         : {g['risk_gates_count']['A']} -> {g['risk_gates_count']['B']}")
    
    lines.append("Risk Gate Reasons:")
    reasons = g['risk_gate_reasons']['counts']
    if not reasons:
        lines.append("  (None)")
    else:
        for r, counts in reasons.items():
            sep = "->" if counts['A'] != counts['B'] else "=="
            lines.append(f"  {r}: {counts['A']} {sep} {counts['B']}")
            
    if g['risk_gate_reasons']['new']:
        lines.append(f"  NEW Reasons: {', '.join(g['risk_gate_reasons']['new'])}")
    if g['risk_gate_reasons']['removed']:
        lines.append(f"  REMOVED Reasons: {', '.join(g['risk_gate_reasons']['removed'])}")

    # Open Questions
    lines.append("\n[OPEN QUESTIONS]")
    oq = diff['open_questions']
    lines.append(f"total_count              : {oq['total_count']['A']} -> {oq['total_count']['B']}")
    
    lines.append("Severity Counts:")
    sev = oq['severity_counts']
    if not sev:
        lines.append("  (None)")
    else:
        for s, counts in sev.items():
            sep = "->" if counts['A'] != counts['B'] else "=="
            lines.append(f"  {s}: {counts['A']} {sep} {counts['B']}")

    top = oq['top_delta']
    if top['new']:
        lines.append(f"\n  NEW ({len(top['new'])} shown):")
        for q in top['new']:
            lines.append(f"    + {q}")
            
    if top['resolved']:
        lines.append(f"\n  RESOLVED ({len(top['resolved'])} shown):")
        for q in top['resolved']:
            lines.append(f"    - {q}")

    # Artifacts
    lines.append("\n[ARTIFACTS]")
    a = diff['artifacts']
    lines.append(f"Run A: {a['audit_summary_a']}")
    lines.append(f"Run B: {a['audit_summary_b']}")
    if a['run_manifest_a']: lines.append(f"Manifest A: {a['run_manifest_a']}")
    if a['run_manifest_b']: lines.append(f"Manifest B: {a['run_manifest_b']}")

    return "\n".join(lines)

def render_markdown(diff: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Run Diff Report")
    
    # Function to create table row
    def row(k, a, b):
        mark = "**CHANGED**" if a != b else "Same"
        # Escaping pipes for MD table not strictly necessary if simple, but good practice.
        return f"| {k} | {format_val(a)} | {format_val(b)} | {mark} |"

    lines.append("## System & Policy")
    lines.append("| Field | Run A | Run B | Status |")
    lines.append("|---|---|---|---|")
    
    h = diff['header']
    keys = ['system_version', 'run_id', 'end_state', 'failure_reason', 
            'governance_profile', 'auto_approve', 'risk_gate_escalation_enabled',
            'open_questions_threshold', 'weighted_severities']
            
    for k in keys:
        if k in h:
            lines.append(row(k, h[k]['A'], h[k]['B']))

    lines.append("\n## Gates")
    g = diff['gates']
    lines.append("| Metric | Run A | Run B | Delta |")
    lines.append("|---|---|---|---|")
    lines.append(row("Approvals (Manual)", g['approvals.manual']['A'], g['approvals.manual']['B']))
    lines.append(row("Approvals (Auto)", g['approvals.auto']['A'], g['approvals.auto']['B']))
    lines.append(row("Phase Gates", g['phase_gates_count']['A'], g['phase_gates_count']['B']))
    lines.append(row("Risk Gates", g['risk_gates_count']['A'], g['risk_gates_count']['B']))
    
    lines.append("\n### Risk Gate Reasons")
    reasons = g['risk_gate_reasons']['counts']
    if reasons:
        lines.append("| Reason | Count A | Count B |")
        lines.append("|---|---|---|")
        for r, counts in reasons.items():
            lines.append(f"| {r} | {counts['A']} | {counts['B']} |")
    else:
        lines.append("No risk gates found.")

    if g['risk_gate_reasons']['new']:
        lines.append(f"\n**New Reasons:** {', '.join(g['risk_gate_reasons']['new'])}")
    if g['risk_gate_reasons']['removed']:
        lines.append(f"\n**Removed Reasons:** {', '.join(g['risk_gate_reasons']['removed'])}")

    lines.append("\n## Open Questions")
    oq = diff['open_questions']
    lines.append(f"**Total Count:** {oq['total_count']['A']} -> {oq['total_count']['B']}")
    
    lines.append("\n### Severity Breakdown")
    sev = oq['severity_counts']
    if sev:
        lines.append("| Severity | Count A | Count B |")
        lines.append("|---|---|---|")
        for s, counts in sev.items():
            lines.append(f"| {s} | {counts['A']} | {counts['B']} |")
    
    top = oq['top_delta']
    if top['new']:
        lines.append("\n### New Questions")
        for q in top['new']:
            lines.append(f"- {q}")
            
    if top['resolved']:
        lines.append("\n### Resolved Questions")
        for q in top['resolved']:
            lines.append(f"- {q}")

    lines.append("\n## Artifacts")
    a = diff['artifacts']
    lines.append(f"- **Audit A:** `{a['audit_summary_a']}`")
    lines.append(f"- **Audit B:** `{a['audit_summary_b']}`")
    return "\n".join(lines)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Deterministic Run Diff Tool")
    
    # Input Patterns
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--latest", action="store_true", help="Use latest run")
    group.add_argument("--run_a", help="Run ID or path for Run A")
    group.add_argument("--dir_a", help="Path for Run A")
    
    parser.add_argument("--prev", action="store_true", help="Use previous run (with --latest)")
    parser.add_argument("--run_b", help="Run ID or path for Run B")
    parser.add_argument("--dir_b", help="Path for Run B")
    
    # Options
    parser.add_argument("--format", choices=['console', 'json', 'md'], default='console', help="Output format")
    parser.add_argument("--write_md", action="store_true", help="Write Markdown report to outputs/<run_a>/run_diff_<run_b>.md")
    parser.add_argument("--out", help="Specific output path for report")
    
    args = parser.parse_args()
    
    id_a = None
    id_b = None
    
    # 1. Resolve Run IDs
    if args.latest:
        recent = get_recent_runs()
        if not recent:
            print("Error: No runs found in outputs/", file=sys.stderr)
            sys.exit(1)
            
        if args.prev:
            if len(recent) < 2:
                print("Error: --prev requested but fewer than 2 runs exist.", file=sys.stderr)
                sys.exit(1)
            id_a = recent[0] # Latest
            id_b = recent[1] # Prev
            # Usually A=prev, B=latest makes mores sense for diff, but prompt says:
            # "compare most recent run to the previous one"
            # Convention: usually A is baseline (prev), B is comparison (latest).
            # But prompt says "--latest --prev".
            # Let's interpret A as Latest, B as Prev? Or A=Prev, B=Latest?
            # Standard diff is `diff old new`.
            # Let's stick to explicitly documented mapping in headers or assume user wants A->B.
            # If user flags --latest --prev, let's map: Run A = Latest, Run B = Previous (Comparison direction A vs B).
            # Actually, `diff A B` implies A is Left, B is Right.
            # If I want to see what CHANGED to produce Latest, I compare Prev -> Latest.
            # So A=Prev, B=Latest is arguably more intuitive for "deltas".
            # BUT, the prompt says "--latest --prev" which implies Latest is the primary subject.
            # Let's assign A=Latest, B=Prev to match the flags literally if we want, OR
            # Map them intelligently.
            # Let's do: A = Latest, B = Previous (literal interpretation of flags).
            # Wait, standard diff is usually Old -> New.
            # Let's flip it: A = Previous, B = Latest. This is more useful.
            # Logic: --latest and --prev are selecting the runs.
            # Run A = Prev (recent[1]), Run B = Latest (recent[0]).
            id_a = recent[1]
            id_b = recent[0]
        else:
            # Just --latest? But we need two runs.
            # Prompt says "C) --latest --prev (compare most recent run to the previous one)"
            # It implies they go together for the mode.
            if not args.prev:
                # If only latest is provided, we can't diff?
                # or maybe compare Latest to... ?
                # Prompt says pattern C is "--latest --prev".
                # If provided separately? Assuming they come together for the pattern.
                print("Error: --latest requires --prev for comparison mode C.", file=sys.stderr)
                sys.exit(1)
    
    elif args.run_a:
        id_a = args.run_a
        if not args.run_b:
             print("Error: --run_a requires --run_b", file=sys.stderr)
             sys.exit(1)
        id_b = args.run_b
        
    elif args.dir_a:
        id_a = args.dir_a
        if not args.dir_b:
             print("Error: --dir_a requires --dir_b", file=sys.stderr)
             sys.exit(1)
        id_b = args.dir_b

    # 2. Resolve Paths
    path_a = resolve_run_path(id_a)
    path_b = resolve_run_path(id_b)

    if not path_a:
        print(f"Error: Run A not found: {id_a}", file=sys.stderr)
        print(f"Available recent runs: {', '.join(get_recent_runs(5))}", file=sys.stderr)
        sys.exit(1)
        
    if not path_b:
        print(f"Error: Run B not found: {id_b}", file=sys.stderr)
        print(f"Available recent runs: {', '.join(get_recent_runs(5))}", file=sys.stderr)
        sys.exit(1)

    # 3. Load Data
    data_a = load_run_data(path_a)
    data_b = load_run_data(path_b)
    
    # 4. Compare
    diff = compare_runs(data_a, data_b)
    
    # 5. Output
    if args.format == 'json':
        print(json.dumps(diff, indent=2))
        
    elif args.format == 'md':
        print(render_markdown(diff))
        
    else:
        print(render_console(diff))
        
    # 6. Write File (Optional)
    content_to_write = None
    if args.write_md:
        content_to_write = render_markdown(diff)
        # Default filename
        # outputs/<run_a>/run_diff_<run_b>.md
        # Use simple basename for filename part if possible
        # path_a is a Path object
        # If path_a is inside outputs, use the dir name.
        name_a = path_a.name
        name_b = path_b.name
        
        # BUT user might have provided arbitrary paths.
        # Let's try to write to path_a / ...
        # If A is previous and B is latest.
        # usually we want the report in the "New" run dir (B).
        # Prompt says: "--write_md (writes outputs/<run_a>/run_diff_<run_b>.md OR a specified --out path)"
        # Okay, following prompt strictly: write to A's folder.
        
        target_path = path_a / f"run_diff_{name_b}.md"
        
        # Override if --out
        if args.out:
            target_path = Path(args.out)
            
        try:
            with open(target_path, 'w') as f:
                f.write(content_to_write)
            print(f"Report written to: {target_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif args.out:
        # User specified out but maybe not --write_md?
        # Implicitly write if out is present? "OR a specified --out path" under --write_md bullet
        # implies --write_md is the trigger, and --out modifies destination.
        # But if --out is passed without --write_md, usually we expect write.
        # Let's support --out standalone too just in case.
        
        # Determine format for file?
        # If extension is .json, write json, if .md write md?
        # Simplified: Use args.format content.
        
        target_path = Path(args.out)
        if args.format == 'json':
            content_to_write = json.dumps(diff, indent=2)
        elif args.format == 'md':
            content_to_write = render_markdown(diff)
        else: # console
            content_to_write = render_console(diff)
            
        try:
            with open(target_path, 'w') as f:
                f.write(content_to_write)
            print(f"Output written to: {target_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
