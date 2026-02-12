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

def utc_now():
    from datetime import datetime
    return datetime.utcnow().isoformat()

def write_ledger(event: Dict[str, Any], ledger_path: str = "governance/run_ledger.jsonl"):
    try:
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        with open(ledger_path, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


def generate_audit_summary(run_id: str, run_dir: str, ledger_path: str = "governance/run_ledger.jsonl", suppress_ledger_events: bool = False):
    """
    Generates a run-level audit summary file in the run directory.
    Aggregates data from run_ledger.jsonl (filtered by run_id) and
    per-step state files in run_dir.
    """
    try:
        summary = {
            "run_id": run_id,
            "run_metadata": {},
            "gate_manifest": {}, # Will be populated with gate_summary content
            "gate_summary": {
                "planned_phase_gates": [],  # Configured phase gates from config
                "phase_gates": [],  # Actually encountered phase gates
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
        
        # Extract planned phase gates from config for transparency
        approval_cfg = config.get("approval", {})
        planned_phase_gates = approval_cfg.get("phase_gates", [])
        try:
            planned_phase_gates = [int(x) for x in planned_phase_gates]
        except Exception:
            planned_phase_gates = []
        summary["gate_summary"]["planned_phase_gates"] = planned_phase_gates
        
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

        # 3c. Populate Risk Gates based on final state
        # Logic: If risk escalation is enabled, check conditions and add to gate_summary.risk_gates if met.
        # This ensures audit summary reflects the risk state even if the run didn't explicitly log a risk_gate_forced event
        # (e.g. if run failed before gate, or if we are re-auditing an old run).
        
        # Calculate weighted count based on Metadata or Default
        # User constraint: "Weighted definition in your audit_summary says: weighted = CRITICAL + BLOCKER + MAJOR"
        # We reuse the severity_counts we just calculated.
        
        # Resolve weighted severities from metadata (which came from manifest/config)
        # If metadata is empty, fallback to the required default
        eff_weighted_severities = summary["run_metadata"]["weighted_severities"]
        if not eff_weighted_severities:
             eff_weighted_severities = ["CRITICAL", "BLOCKER", "MAJOR"]

        weighted_count = 0
        for sev in eff_weighted_severities:
            sev_key = sev.lower()
            weighted_count += severity_counts.get(sev_key, 0)
            
        summary["open_questions_summary"]["weighted_count"] = weighted_count

        # Check for Risk Gates
        if summary["run_metadata"]["risk_gate_escalation_enabled"]:
            
            # Condition 1: Force Gate on QA Critical
            # Logic: If force_gate_on_qa_critical is true AND critical >= 1
            # We need force_gate_on_qa_critical from config/manifest.
            # It wasn't in run_metadata summary yet, let's fetch it from risk_cfg_manifest or risk_cfg
            
            force_gate_critical = risk_cfg_manifest.get(
                "force_gate_on_qa_critical",
                risk_cfg.get("force_gate_on_qa_critical", True) # Default true per text? check root_agent.
            )
            # In root_agent: risk_force_on_qa_critical = risk_cfg.get("force_gate_on_qa_critical", True)
            
            if force_gate_critical and severity_counts["critical"] >= 1:
                # Check if this gate is already in risk_gates (from ledger)
                # If so, we don't need to duplicate it, but requirements say "add a risk gate entry".
                # If we rely on ledger, we might miss it if the run crushed or if we are auditing a run that didn't have the logic yet.
                # Since this is "risk gate escalation", we should probably ensure it's visible.
                # Let's check for duplicates based on gate_reason.
                
                existing_reasons = [g.get("gate_reason") for g in summary["gate_summary"]["risk_gates"]]
                if "qa_critical_open_questions" not in existing_reasons:
                    summary["gate_summary"]["risk_gates"].append({
                        "gate_type": "risk_gate",
                        "gate_reason": "qa_critical_open_questions",
                        "threshold": summary["run_metadata"]["open_questions_threshold"], # Not exactly relevant but keeps schema
                        "observed": severity_counts["critical"],
                        "policy": "force_gate_on_qa_critical"
                    })

            # Condition 2: Open Questions Threshold Exceeded
            threshold = summary["run_metadata"]["open_questions_threshold"]
            if weighted_count > threshold: # User said "exceed", so >
                # Check duplicates
                existing_reasons = [g.get("gate_reason") for g in summary["gate_summary"]["risk_gates"]]
                if "open_questions_threshold_exceeded" not in existing_reasons:
                     summary["gate_summary"]["risk_gates"].append({
                        "gate_type": "risk_gate",
                        "gate_reason": "open_questions_threshold_exceeded",
                        "threshold": threshold,
                        "observed": weighted_count,
                        "policy": "open_questions_threshold"
                     })

        # Ensure gate_manifest reflects gate_summary as requested
        summary["gate_manifest"] = summary["gate_summary"]

        # 4. Write Artifact
        output_path = Path(run_dir) / "audit_summary.json"
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
            
        # 5. Log Risk Gate Triggered Event (if any)
        # This event serves as the official "Risk Gate Encountered" signal for governance.
        risk_gates = summary["gate_summary"].get("risk_gates", [])
        if risk_gates and not suppress_ledger_events:
            risk_event = {
                "timestamp_utc": utc_now(),
                "event": "risk_gate_triggered",
                "run_id": run_id,
                "run_dir": run_dir,
                "risk_gate_count": len(risk_gates),
                "gates": risk_gates
            }
            write_ledger(risk_event, ledger_path=ledger_path)

        return output_path

    except Exception as e:
        # Fallback: don't crash the runner
        print(f"Failed to generate audit summary: {e}")
        return None
