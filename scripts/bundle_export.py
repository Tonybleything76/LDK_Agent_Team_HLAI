#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# --- Constants ---
OUTPUTS_DIR = Path("outputs")
GOVERNANCE_DIR = Path("governance")
LEDGER_PATH = GOVERNANCE_DIR / "run_ledger.jsonl"
RUN_ID_PATTERN = re.compile(r"^\d{8}_\d{6}$")
ZIP_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# --- Helpers ---

def get_recent_runs(limit: int = 10) -> List[str]:
    if not OUTPUTS_DIR.exists():
        return []
    runs = []
    for d in OUTPUTS_DIR.iterdir():
        if d.is_dir() and RUN_ID_PATTERN.match(d.name):
            try:
                runs.append((d.stat().st_mtime, d.name))
            except OSError:
                continue
    runs.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in runs[:limit]]

def validate_run_dir(run_path: Path) -> Path:
    if not run_path.exists() or not run_path.is_dir():
        print(f"Error: Run directory not found: {run_path}", file=sys.stderr)
        recent = get_recent_runs()
        if recent:
            print("Recent valid runs:", file=sys.stderr)
            for r in recent:
                print(f"  - {r}", file=sys.stderr)
        sys.exit(1)
    
    if not RUN_ID_PATTERN.match(run_path.name):
        print(f"Error: Directory name '{run_path.name}' does not match run ID pattern", file=sys.stderr)
        sys.exit(1)
    
    if not (run_path / "audit_summary.json").exists():
        print(f"Error: audit_summary.json missing in {run_path}", file=sys.stderr)
        sys.exit(1)
        
    return run_path

def validate_run_exists(run_id: str) -> Path:
    # wrapper for backward compatibility / ID-based lookup
    return validate_run_dir(OUTPUTS_DIR / run_id)

def run_subprocess(cmd: List[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def filter_ledger(run_ids: List[str]) -> Dict[str, str]:
    """
    Reads ledger, filters lines matching ANY of the run_ids.
    Returns a dict mapping run_id -> filtered_ledger_content.
    """
    if not LEDGER_PATH.exists():
        return {}

    filtered = {rid: [] for rid in run_ids}
    
    try:
        with open(LEDGER_PATH, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    rid = record.get("run_id")
                    if rid in run_ids:
                        filtered[rid].append(line.strip())
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Warning: Failed to read ledger: {e}", file=sys.stderr)
        return {}
    
    return {rid: "\n".join(lines) for rid, lines in filtered.items() if lines}

# --- Main Logic ---

def collect_run_files(run_id: str, run_dir: Path, include_state: bool) -> List[Dict[str, Any]]:
    """
    Collects files to include for a single run.
    Returns list of dicts: {'source': Path, 'arcname': str, 'content': Optional[str]}
    If 'content' is set, use that instead of reading 'source'.
    """
    files_to_add = []
    
    # 1. Manifest
    if (run_dir / "run_manifest.json").exists():
        files_to_add.append({
            'source': run_dir / "run_manifest.json",
            'arcname': "run_manifest.json"
        })
    else:
        print(f"Note: run_manifest.json missing for {run_id} (skipping)")

    # 2. Audit Summary (Required, already validated)
    files_to_add.append({
        'source': run_dir / "audit_summary.json",
        'arcname': "audit_summary.json"
    })

    # 3. Audit Summary MD
    audit_md = run_dir / "audit_summary.md"
    if audit_md.exists():
        files_to_add.append({
            'source': audit_md,
            'arcname': "audit_summary.md"
        })
    else:
        # Generate it
        print(f"Generating audit_summary.md for {run_id}...")
        cmd = [sys.executable, "scripts/run_report.py", "--run_id", run_id, "--format", "md"]
        md_content = run_subprocess(cmd)
        files_to_add.append({
            'source': None,
            'arcname': "audit_summary.md",
            'content': md_content
        })

    # 4. Run Report JSON
    print(f"Generating run_report.json for {run_id}...")
    cmd = [sys.executable, "scripts/run_report.py", "--run_id", run_id, "--format", "json"]
    json_content = run_subprocess(cmd)
    files_to_add.append({
        'source': None,
        'arcname': "run_report.json",
        'content': json_content
    })

    # 5. Optional run_diff_* files
    for f in run_dir.iterdir():
        if f.name.startswith("run_diff_") and (f.suffix == ".md" or f.suffix == ".json"):
            files_to_add.append({
                'source': f,
                'arcname': f.name
            })
            
    # 6. State files
    if include_state:
        for f in run_dir.glob("*_state.json"):
            files_to_add.append({
                'source': f,
                'arcname': f.name
            })
            
    return files_to_add

def main():
    parser = argparse.ArgumentParser(description="Deterministic Bundle Export Utility")
    
    # Run Selection
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--run_id", help="Single Run ID")
    group.add_argument("--run_dir", help="Single Run Directory")
    group.add_argument("--latest", action="store_true", help="Latest Run")
    # Python's argparse doesn't easily support "--run_a AND --run_b" as an option in exclusive group with others.
    # We'll allow them as optional and validation logic.
    parser.add_argument("--run_a", help="Run A ID (for two-run bundle)")
    parser.add_argument("--run_b", help="Run B ID (for two-run bundle)")
    
    # Flags
    parser.add_argument("--out", help="Output path for zip bundle")
    parser.add_argument("--format", choices=["md", "json"], default="json", help="Manifest format inside zip")
    parser.add_argument("--include_state", action="store_true", help="Include per-step state JSONs")
    parser.add_argument("--include_ledger", action="store_true", help="Include filtered ledger entries")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing bundle")

    args = parser.parse_args()

    # Resolve Runs
    runs_to_process = [] # List of (run_id, run_dir)
    mode = "single_run"
    
    # Helper to resolve single ID/Dir
    def resolve_single(rid=None, rdir=None):
        if rdir:
            path = Path(rdir)
            validated = validate_run_dir(path)
            return validated.name, validated
        if rid:
            return rid, validate_run_exists(rid)
        return None, None

    if args.run_a and args.run_b:
        mode = "two_run"
        id_a, dir_a = resolve_single(rid=args.run_a)
        id_b, dir_b = resolve_single(rid=args.run_b)
        runs_to_process.append((id_a, dir_a))
        runs_to_process.append((id_b, dir_b))
    elif args.run_a or args.run_b:
        print("Error: Must provide both --run_a and --run_b", file=sys.stderr)
        sys.exit(1)
    elif args.run_id or args.run_dir or args.latest:
        # Single mode
        rid, rdir = None, None
        if args.latest:
            recent = get_recent_runs(1)
            if not recent:
                print("Error: No runs found", file=sys.stderr)
                sys.exit(1)
            rid = recent[0]
            rdir = OUTPUTS_DIR / rid
        elif args.run_id:
            rid, rdir = resolve_single(rid=args.run_id)
        elif args.run_dir:
            rid, rdir = resolve_single(rdir=args.run_dir)
        
        # In run_dir case, resolve_single calls validate_run_dir.
        # In run_id/latest case, resolve_single calls validate_run_exists.
        # So we just append (rid, rdir)
        runs_to_process.append((rid, rdir))
    else:
        parser.print_help()
        sys.exit(1)

    # Determine Output Path
    out_path = args.out
    if not out_path:
        if mode == "single_run":
            rid = runs_to_process[0][0]
            out_path = OUTPUTS_DIR / rid / f"bundle_{rid}.zip"
        else:
            rid_a = runs_to_process[0][0]
            rid_b = runs_to_process[1][0]
            # Prompt default: outputs/<run_a>/bundle_<run_a>__<run_b>.zip
            out_path = OUTPUTS_DIR / rid_a / f"bundle_{rid_a}__{rid_b}.zip"
    
    out_path = Path(out_path)
    if out_path.exists() and not args.overwrite:
        print(f"Error: Bundle exists at {out_path} (use --overwrite to replace)", file=sys.stderr)
        sys.exit(1)

    # Collect Content
    zip_entries = [] # (arcname, source_path, content_str)
    
    # Helper to add entry
    def add_entry(arcname, source=None, content=None):
        zip_entries.append((arcname, source, content))

    # Process Runs
    files_included = []

    for rid, rdir in runs_to_process:
        # If two_run, prefix with run_id
        # We will use folder even for single run for cleanliness
        
        raw_files = collect_run_files(rid, rdir, args.include_state)
        for item in raw_files:
            zip_path = f"{rid}/{item['arcname']}"
            add_entry(zip_path, item['source'], item.get('content'))
            files_included.append(zip_path)

        # Ledger (per run)
        if args.include_ledger:
            # We need to filter for this specific run
            ledger_map = filter_ledger([rid])
            if rid in ledger_map:
                content = ledger_map[rid]
                name = f"ledger_filtered_{rid}.jsonl"
                add_entry(name, content=content)
                files_included.append(name)
    
    # Two-Run Extras (Run Diff)
    if mode == "two_run":
        rid_a = runs_to_process[0][0]
        rid_b = runs_to_process[1][0]
        
        # Generate Diff
        
        print(f"Generating run_diff for {rid_a} vs {rid_b}...")
        
        # MD
        cmd_md = [sys.executable, "scripts/run_diff.py", "--run_a", rid_a, "--run_b", rid_b, "--format", "md"]
        md_content = run_subprocess(cmd_md)
        name_md = f"run_diff_{rid_a}__{rid_b}.md"
        add_entry(name_md, content=md_content)
        files_included.append(name_md)
        
        # JSON
        cmd_json = [sys.executable, "scripts/run_diff.py", "--run_a", rid_a, "--run_b", rid_b, "--format", "json"]
        json_content = run_subprocess(cmd_json)
        name_json = f"run_diff_{rid_a}__{rid_b}.json"
        add_entry(name_json, content=json_content)
        files_included.append(name_json)

    # Bundle Manifest
    manifest_name = f"bundle_manifest.{args.format}"
    files_included.append(manifest_name)
    
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_type": mode,
        "run_ids": [r[0] for r in runs_to_process],
        "included_files": sorted(files_included),
        "include_state": args.include_state,
        "include_ledger": args.include_ledger
    }
    
    
    if args.format == "json":
        manifest_content = json.dumps(manifest, indent=2)
    else:
        # Simple MD format
        lines = ["# Bundle Manifest", ""]
        lines.append(f"- **Created At**: {manifest['created_at_utc']}")
        lines.append(f"- **Type**: {manifest['bundle_type']}")
        lines.append(f"- **Run IDs**: {', '.join(manifest['run_ids'])}")
        lines.append(f"- **Include State**: {manifest['include_state']}")
        lines.append(f"- **Include Ledger**: {manifest['include_ledger']}")
        lines.append("")
        lines.append("## Included Files")
        for f in manifest['included_files']:
            lines.append(f"- {f}")
        manifest_content = "\n".join(lines)

    add_entry(manifest_name, content=manifest_content)

    # Write Zip
    try:
        # Ensure parent exists
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for arcname, source, content in zip_entries:
                if content is not None:
                    # Zip info
                    info = zipfile.ZipInfo(arcname)
                    info.date_time = ZIP_FIXED_TIMESTAMP
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
                elif source:
                    zf.write(source, arcname)
        
        print(f"\nBundle created: {out_path}")
        print(f"Included {len(zip_entries)} files.")
        
    except Exception as e:
        print(f"Error creating zip: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
