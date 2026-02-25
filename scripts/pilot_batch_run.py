#!/usr/bin/env python3
import sys
import os
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Pilot Batch Runner - Run multiple iterations to establish baseline.")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations to run")
    parser.add_argument("--mode", help="Provider mode")
    parser.add_argument("--dry_run", action="store_true", help="Use dry run provider")
    parser.add_argument("--governance_profile", default="pilot", help="Governance profile")
    parser.add_argument("--yes", action="store_true", help="Skip cost confirmation")
    parser.add_argument("--auto_approve", action="store_true", help="Auto-approve all gates")
    
    args, extra_args = parser.parse_known_args()
    
    print(f"\n🚀 Starting Batch Run: {args.iterations} iterations")
    print(f"   Profile: {args.governance_profile}")
    if args.dry_run:
        print(f"   Provider: dry_run")
    else:
        print(f"   Provider: {args.mode or 'config default'}")
    
    if extra_args:
        print(f"   Extra Flags: {' '.join(extra_args)}")
    
    run_summaries = []
    
    for i in range(1, args.iterations + 1):
        print(f"\n" + "="*80)
        print(f"ITERATION {i}/{args.iterations}")
        print("="*80)
        
        cmd = [sys.executable, "scripts/run_pipeline.py"]
        
        if args.dry_run:
            cmd.append("--dry_run")
        elif args.mode:
            cmd.append("--mode")
            cmd.append(args.mode)
            
        cmd.extend(["--governance_profile", args.governance_profile])
        if args.yes: cmd.append("--yes")
        if args.auto_approve: cmd.append("--auto_approve")
        cmd.append("--allow-dirty-worktree")
        
        # Pass through any unknown arguments to the pipeline script
        cmd.extend(extra_args)
        
        # We run as subprocess to keep each run isolated
        # Using env to pass provider settings explicitly
        env = os.environ.copy()
        
        result = subprocess.run(cmd, env=env)
        
        if result.returncode != 0:
            print(f"\n❌ Iteration {i} failed with exit code {result.returncode}")
            run_summaries.append({
                "iteration": i,
                "status": "FAILED",
                "run_id": "N/A"
            })
            continue
            
        # Find the latest output dir
        outputs_dir = Path("outputs")
        latest_run = sorted([d for d in outputs_dir.iterdir() if d.is_dir()])[-1]
        
        # Try to pull some metrics from audit_summary
        audit_path = latest_run / "audit_summary.json"
        status = "UNKNOWN"
        open_questions = 0
        
        if audit_path.exists():
            with open(audit_path, "r") as f:
                audit = json.load(f)
                status = audit.get("end_state", "UNKNOWN")
                open_questions = audit.get("open_questions_summary", {}).get("total_count", 0)
        
        run_summaries.append({
            "iteration": i,
            "run_id": latest_run.name,
            "status": status,
            "open_questions": open_questions
        })
        
        # Small delay to ensure unique timestamps for the next run
        if i < args.iterations:
            import time
            time.sleep(1.1)

    print("\n" + "="*80)
    print("BATCH RUN SUMMARY (BASELINE EVALUATION)")
    print("="*80)
    print(f"{'Iter':<5} | {'Run ID':<17} | {'Status':<10} | {'Open Ques':<10}")
    print("-" * 80)
    for s in run_summaries:
        run_id = s.get("run_id", "N/A")
        print(f"{s['iteration']:<5} | {run_id:<17} | {s['status']:<10} | {s.get('open_questions', 0):<10}")
    print("="*80)

if __name__ == "__main__":
    main()
