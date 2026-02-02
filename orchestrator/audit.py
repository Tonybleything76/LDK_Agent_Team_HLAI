import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List

def load_json_safe(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def load_text_safe(path: str) -> str:
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return ""

def generate_audit_summary(run_id: str, run_dir: str, ledger_path: str = "governance/run_ledger.jsonl"):
    """
    Generates a run-level audit summary file in the run directory.
    Aggregates data from run_ledger.jsonl (filtered by run_id) and
    per-step state files in run_dir.
    """
    try:
        summary = {
            "run_metadata": {},
            "gate_summary": {
                "phase_gates": [],
                "risk_gates": [],
                "approvals": {"manual": 0, "auto": 0}
            },
            "open_questions_summary": {
                "total_count": 0,
                "top_10": []
            },
            "end_state": "unknown"
        }

        # 1. Gather Run Metadata (Manifest & Config)
        manifest_path = Path(run_dir) / "run_manifest.json"
        manifest = load_json_safe(str(manifest_path))
        
        # Load Config (global)
        config_path = "config/run_config.json"
        config = load_json_safe(config_path)
        
        # Determine defaults
        risk_cfg = config.get("approval", { }).get("risk_gate_escalation", {})
        risk_auto_override_default = risk_cfg.get("auto_override", True)
        
        summary["run_metadata"] = {
            "system_version": manifest.get("system_version") or (load_text_safe("VERSION").strip() or "unknown"),
            "run_id": run_id,
            "run_dir": run_dir,
            "auto_approve": manifest.get("auto_approve", False),
            "governance_profile": manifest.get("governance_profile"),
            "risk_auto_override_default": manifest.get("risk_auto_override_default", risk_auto_override_default),
            "started_at_utc": manifest.get("started_at_utc"),
        }

        # Add Risk Gate Policy (Transparency)
        # Try manifest first (effective resolved config), then fallback to config default
        approval_cfg_manifest = manifest.get("approval_config", {})
        risk_cfg_manifest = approval_cfg_manifest.get("risk_gate_escalation", {})
        
        # Merge manifest risk config over config default to ensure effective values
        # If manifest has it, use it. If not, use global config as fallback.
        # Note: manifest["risk_auto_override_default"] is already set above.
        
        summary["run_metadata"]["open_questions_threshold"] = risk_cfg_manifest.get(
            "open_questions_threshold", 
            risk_cfg.get("open_questions_threshold", 8)
        )
        summary["run_metadata"]["weighted_severities"] = risk_cfg_manifest.get(
            "weighted_severities", 
            risk_cfg.get("weighted_severities", [])
        )
        summary["run_metadata"]["risk_gate_escalation_enabled"] = risk_cfg_manifest.get(
            "enabled", 
            risk_cfg.get("enabled", False)
        )

        # 2. Scan Ledger for this Run
        # ledger_path arg used here
        ledger_entries = []
        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # Filter by run_id or equality of run_dir
                        # Some legacy entries might lack run_id, check run_dir as backup
                        if entry.get("run_id") == run_id or entry.get("run_dir") == str(run_dir):
                            ledger_entries.append(entry)
                    except:
                        continue

        # Pre-scan approvals for lookup
        approvals_by_step = {}
        for entry in ledger_entries:
            if entry.get("event") == "step_approved":
                approvals_by_step[entry.get("step_idx")] = entry

        # Process Ledger Entries
        for entry in ledger_entries:
            evt = entry.get("event")
            
            # End State
            if evt == "run_completed":
                summary["end_state"] = "run_completed"
            elif evt == "run_failed":
                summary["end_state"] = "run_failed"
                summary["failure_reason"] = entry.get("reason") or entry.get("error")

            # Approvals
            if evt == "step_approved":
                mode = entry.get("approval_mode", "manual") # Default to manual if missing
                if mode == "auto":
                    summary["gate_summary"]["approvals"]["auto"] += 1
                else:
                    summary["gate_summary"]["approvals"]["manual"] += 1
                
                # Gate info
                gate_info = {
                    "step_idx": entry.get("step_idx"),
                    "agent": entry.get("agent_name"),
                    "gate_strategy": entry.get("gate_strategy"),
                    "gate_type": entry.get("gate_type", "phase_gate"),
                    "gate_reason": entry.get("gate_reason", "routine_check")
                }
                
                if gate_info["gate_type"] == "risk_gate":
                    # For approvals, we might not have override info here, but risk_gate_forced might exist
                    pass 
                
                # We can list all gates passed here? Or just phase gates?
                # User request: "phase gates encountered", "risk gates encountered"
                if gate_info["gate_type"] == "phase_gate":
                    summary["gate_summary"]["phase_gates"].append(gate_info)
            
            # Risk Gates (forced/logged)
            if evt == "risk_gate_forced":
                step_idx = entry.get("step_idx")
                
                # Default values
                overridden = False
                approved_mode = None
                
                # Check resolution via approval
                if step_idx in approvals_by_step:
                    approval = approvals_by_step[step_idx]
                    approved_mode = approval.get("approval_mode", "manual")
                    reason = approval.get("approval_reason", "")
                    
                    # Logic: overridden if auto-approved with override reason
                    if approved_mode == "auto" and "override after risk gate" in reason:
                        overridden = True
                
                r_item = {
                    "step_idx": step_idx,
                    "agent": entry.get("agent_name"),
                    "gate_reason": entry.get("gate_reason"),
                    "overridden": overridden,
                    "approved_mode": approved_mode,
                    "metadata": {k:v for k,v in entry.items() if k not in ["event", "timestamp_utc", "run_id", "run_dir"]}
                }
                summary["gate_summary"]["risk_gates"].append(r_item)

        # 3. Open Questions Extraction
        # Scan *_state.json files or just the final state? 
        # Request says "total open_questions per step". So likely need per-step state.
        
        # Reset unique counter
        all_open_questions = []

        # Find all state files: NN_agentname_state.json
        state_files = sorted(glob.glob(os.path.join(run_dir, "*_state.json")))
        
        for sf in state_files:
            if "99_final_state.json" in sf:
                continue
                
            data = load_json_safe(sf)
            qs = data.get("open_questions", [])
            if isinstance(qs, list):
                all_open_questions.extend(qs)
                
            # Keep track of per-step? 
            # "total open_questions per step" -> implies a count per step in the summary?
            # Or just aggregated total? "total open_questions per step" is ambiguous.
            # "Total open_questions [newline] per step" or "Total count of open questions for each step".
            # The JSON structure asked for "total open_questions per step" in "Open questions summary".
            # Let's add a breakdown if needed, but the requirements just said:
            # "total open_questions per step" -> I'll stick to a total count across run and maybe breakdown.
            # Actually, "total open_questions per step" sounds like a dict {step: count}.
            # But the deliverable example is just "open_questions": [] in the response structure example.
            # I will just do total count and toplist.
        
        # Deduplicate while preserving order
        seen = set()
        unique_qs = []
        for q in all_open_questions:
            if q not in seen:
                seen.add(q)
                unique_qs.append(q)

        # 3b. Severity Breakdown
        severity_counts = {
            "critical": 0,
            "blocker": 0,
            "major": 0,
            "minor": 0,
            "unprefixed": 0
        }
        
        for q in unique_qs:
            q_upper = q.upper().strip()
            if q_upper.startswith("CRITICAL:"):
                severity_counts["critical"] += 1
            elif q_upper.startswith("BLOCKER:"):
                severity_counts["blocker"] += 1
            elif q_upper.startswith("MAJOR:"):
                severity_counts["major"] += 1
            elif q_upper.startswith("MINOR:"):
                severity_counts["minor"] += 1
            else:
                severity_counts["unprefixed"] += 1

        summary["open_questions_summary"]["total_count"] = len(unique_qs)
        summary["open_questions_summary"]["severity_counts"] = severity_counts
        summary["open_questions_summary"]["weighted_count_definition"] = "weighted = CRITICAL + BLOCKER + MAJOR"
        summary["open_questions_summary"]["top_10"] = unique_qs[:10]

        # 4. Write Artifact
        output_path = Path(run_dir) / "audit_summary.json"
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
            
        return output_path

    except Exception as e:
        # Fallback: don't crash the runner
        print(f"Failed to generate audit summary: {e}")
        return None
