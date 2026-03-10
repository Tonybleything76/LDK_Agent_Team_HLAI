import json
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import copy

from orchestrator.providers import get_provider
from orchestrator.validation import validate_agent_output, ValidationConfig
from orchestrator.json_tools import parse_json_object
from orchestrator.approval_handler import (
    ApprovalRejectedError,
    approval_gate,
    evaluate_risk_gate,
    load_phase_gates,
)
from orchestrator.run_artifacts import (
    ensure_run_dirs,
    write_checkpoint,
    write_manifest,
    read_manifest,
    compute_config_hash,
    compute_inputs_hash,
)
from schemas.system_state import get_initial_state
from schemas.agent_output_contract import REQUIRED_KEYS
from orchestrator.audit import generate_audit_summary

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

CONFIG_PATH = Path("config/run_config.json")
LEDGER_PATH = "governance/run_ledger.jsonl"
OUTPUTS_DIR = "outputs"
INPUTS_DIR = "inputs"

# ------------------------------------------------------------------------------
# Errors
# ------------------------------------------------------------------------------

# ApprovalRejectedError is imported from orchestrator.approval_handler

class ValidationError(Exception):
    pass

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------

def utc_now():
    return datetime.utcnow().isoformat()

def write_ledger(event: Dict[str, Any]):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")

def deep_merge(a: Dict, b: Dict) -> Dict:
    result = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result

def get_system_version() -> str:
    """Read system version from VERSION file or return 'unknown'."""
    try:
        if os.path.exists("VERSION"):
            with open("VERSION", "r") as f:
                return f.read().strip()
        # Fallback if needed, but strict constraint says VERSION or pyproject.toml
        return "unknown"
    except Exception:
        return "unknown"

def load_text(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def load_config() -> Dict[str, Any]:
    """Load and validate run configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Create it before running."
        )
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    # Validate required fields
    if "agents" not in config:
        raise ValueError("Config missing required 'agents' field")
    
    if not isinstance(config["agents"], list) or len(config["agents"]) == 0:
        raise ValueError("Config 'agents' must be a non-empty list")
    
    # Validate each agent has required fields
    for idx, agent in enumerate(config["agents"], start=1):
        if "name" not in agent:
            raise ValueError(f"Agent {idx} missing required 'name' field")
        if "prompt_path" not in agent:
            raise ValueError(f"Agent {idx} ({agent.get('name', 'unknown')}) missing required 'prompt_path' field")
    
    return config

# approval_gate(), evaluate_risk_gate(), and load_phase_gates() are
# defined in orchestrator/approval_handler.py and imported above.

# ------------------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------------------

def prune_system_state(state: dict, agent_name: str) -> dict:
    """
    Selectively prune the system state to keep prompts concise.
    Focuses LLM attention on relevant context and avoids token bloat.
    """
    # Defensive copy to avoid mutating the master state
    pruned = {
        "inputs": copy.deepcopy(state.get("inputs", {})),
        "strategy": copy.deepcopy(state.get("strategy", {})),
        "research": copy.deepcopy(state.get("research", {})),
        "curriculum": copy.deepcopy(state.get("curriculum", {})),
    }

    # Agent-specific inclusions
    if agent_name == "instructional_designer_agent":
        pruned["module_designs"] = copy.deepcopy(state.get("module_designs", []))
    elif agent_name == "storyboard_agent":
        pruned["module_designs"] = copy.deepcopy(state.get("module_designs", []))
        pruned["storyboards"] = copy.deepcopy(state.get("storyboards", []))
    elif agent_name == "media_producer_agent":
        pruned["storyboards"] = copy.deepcopy(state.get("storyboards", []))
    elif agent_name in ["qa_agent", "change_management_agent", "operations_librarian_agent"]:
        # These agents are auditing/librarian roles and need broad context
        # However, we still return a copy to be safe
        return copy.deepcopy(state)

    # For other agents (like learner_research, learning_architect), 
    # the core keys are usually sufficient or they are starting fresh.
    return pruned


def run_pipeline(
    config_path: str = None,
    run_dir: str = None,
    start_step: int = 1,
    initial_state: dict = None,
    config_overrides: dict = None,
    governance_profile: str = None,
    max_step: int = None,
    inputs_dir: str = "inputs",
) -> None:
    """
    Execute the agent pipeline with optional resume support.
    
    Args:
        config_path: Path to config file (default: config/run_config.json)
        run_dir: Existing run directory for resume (default: create new)
        start_step: Step index to start from (default: 1)
        initial_state: Initial state for resume (default: get_initial_state())
        max_step: Stop execution after completing this step number (inclusive)
        inputs_dir: Directory containing input files (default: "inputs")
    """
    # Track manifest in outer scope for error handlers
    manifest = None
    
    try:
        # ----------------------------------------------------------------------
        # Load Configuration
        # ----------------------------------------------------------------------

        if config_path is None:
            config_path = str(CONFIG_PATH)
        
        config = load_config()

        # Apply Overrides
        if config_overrides:
            print(f"Applying config overrides: {json.dumps(config_overrides, indent=2)}")
            config = deep_merge(config, config_overrides)

        # ----------------------------------------------------------------------
        # Pilot Profile Validation
        # ----------------------------------------------------------------------
        if governance_profile == "pilot":
            env_provider = os.getenv("PROVIDER")
            # If PROVIDER is strictly "dry_run" or if default config uses "dry_run" and no env override
            resolved_provider = env_provider or config.get("provider", "")
            
            if resolved_provider == "dry_run":
                raise ValueError(
                    "❌ PILOT SAFETY: Cannot use 'dry_run' provider with 'pilot' governance profile. "
                    "You must use a real provider (e.g., openai)."
                )
            
            # Ensure CI Simulation is disabled
            if os.getenv("CI_SIMULATE_MANUAL_RISK_APPROVAL", "").lower() in ("1", "true", "yes", "on"):
                print("⚠️  PILOT SAFETY: Disabling CI_SIMULATE_MANUAL_RISK_APPROVAL for pilot run.")
                os.environ.pop("CI_SIMULATE_MANUAL_RISK_APPROVAL", None)

        # ----------------------------------------------------------------------
        # Load Inputs
        # ----------------------------------------------------------------------

        business_brief_path = os.path.join(inputs_dir, "business_brief.md")
        sme_notes_path = os.path.join(inputs_dir, "sme_notes.md")

        if not os.path.exists(business_brief_path):
             raise FileNotFoundError(f"Missing input file: {business_brief_path}")
        if not os.path.exists(sme_notes_path):
             raise FileNotFoundError(f"Missing input file: {sme_notes_path}")

        business_brief = load_text(business_brief_path)
        sme_notes = load_text(sme_notes_path)

        # ----------------------------------------------------------------------
        # Initial State and Run Directory
        # ----------------------------------------------------------------------

        # Resume mode: use provided state and directory
        if run_dir is not None and initial_state is not None:
            system_state = initial_state
            run_id = Path(run_dir).name
            print(f"\n🔄 RESUMING RUN: {run_id} from step {start_step}")
            
            # Load existing manifest
            manifest = read_manifest(Path(run_dir))
            manifest["status"] = "running"  # Reset to running
            
            # v0.3 Hardening: Update auto_approve intent on resume
            # Only set if missing (legacy manifests). If present, MUST preserve original run intent.
            if "auto_approve" not in manifest:
                manifest["auto_approve"] = os.getenv("AUTO_APPROVE", "").lower() in ("1", "true", "yes", "on")
            
            # v0.3 Hardening: Restore governance_profile if resuming
            if "governance_profile" not in manifest and governance_profile:
                # If resuming a legacy run with a new profile flag? 
                # Strict: The original run manifest is truth. But if we want to "upgrade" the run context?
                # Safer: Only set if missing.
                manifest["governance_profile"] = governance_profile
            # If manifest has it, we respect manifest or do we allow override on resume?
            # Usually resume respects original intent. But we might want to change governance mid-flight?
            # Let's assume manifest is source of truth for continuity, but if passed in CLI, maybe we update?
            # For now, let's treat manifest as authoritative once set. 
            # But wait, config overrides are applied fresh on every run (resume or new).
            # So the profile logic in run_pipeline.py runs every time.
            # So `governance_profile` arg reflects the CURRENT execution intent.
            # We should probably update the manifest to reflect the active profile for this session?
            # But the manifest tracks the *Start* of the run.
            # Let's stick to: set if missing (backward compat), or update if explicit?
            # Requirement says "Persist resolved profile name".
            # I'll update it to match current run args if provided.
            if governance_profile:
                manifest["governance_profile"] = governance_profile
            
            write_manifest(Path(run_dir), manifest)
        else:
            # Fresh run: create new state and directory
            system_state = get_initial_state()
            run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            run_dir = os.path.join(OUTPUTS_DIR, run_id)
            os.makedirs(run_dir, exist_ok=True)
            
            # Initialize manifest
            manifest = {
                "system_version": get_system_version(),
                "run_id": run_id,
                "started_at_utc": utc_now(),
                "config_hash": compute_config_hash(Path(config_path)),
                "inputs_hash": compute_inputs_hash(
                    Path(business_brief_path),
                    Path(sme_notes_path),
                ),
                "current_step_completed": 0,
                "providers_used_by_step": {},
                "status": "running",
                "auto_approve": os.getenv("AUTO_APPROVE", "").lower() in ("1", "true", "yes", "on"),
                "governance_profile": governance_profile,
                "risk_auto_override_default": config.get("approval", {}).get("risk_gate_escalation", {}).get("auto_override", True),
                "approval_config": {
                    "risk_gate_escalation": config.get("approval", {}).get("risk_gate_escalation", {})
                }
            }
        
        # Ensure checkpoints directory exists
        checkpoints_dir = ensure_run_dirs(Path(run_dir))
        write_manifest(Path(run_dir), manifest)

        write_ledger({
            "timestamp_utc": utc_now(),
            "event": "run_started" if start_step == 1 else "run_resumed",
            "run_dir": run_dir,
            "start_step": start_step,
        })

        # ----------------------------------------------------------------------
        # Approval Configuration (from config file)
        # ----------------------------------------------------------------------

        approval_cfg = config.get("approval", {})
        gate_strategy = (approval_cfg.get("gate_strategy", "per_phase") or "per_phase").strip().lower()
        approval_token = approval_cfg.get("require_approval_token", "APPROVE")

        phase_gates = load_phase_gates(approval_cfg, gate_strategy)

        # Risk Escalation Configuration
        risk_cfg = approval_cfg.get("risk_gate_escalation", {})
        risk_enabled = risk_cfg.get("enabled", False)
        risk_open_questions_threshold = risk_cfg.get("open_questions_threshold", 8)
        risk_force_on_qa_critical = risk_cfg.get("force_gate_on_qa_critical", True)

        # ----------------------------------------------------------------------
        # Validation Configuration (from config file)
        # ----------------------------------------------------------------------

        validation_cfg = config.get("validation", {})
        min_deliverable_chars = validation_cfg.get("min_deliverable_chars", 300)
        placeholder_markers = validation_cfg.get("placeholder_markers", [
            "[Missing", "[Pending", "TODO", "TBD", "PLACEHOLDER", "template"
        ])
        retry_once_on_parse_error = validation_cfg.get("retry_once_on_parse_error", False)

        # ----------------------------------------------------------------------
        # Execute Agents (config-driven)
        # ----------------------------------------------------------------------

        for step_idx, agent_cfg in enumerate(config["agents"], start=1):
            # Skip steps before start_step (for resume)
            if step_idx < start_step:
                continue
            
            # Check for early stop (max_step)
            # Checked at start of loop so we don't start the step if we exceeded max_step
            # But wait, max_step is inclusive "completed this step number".
            # So if max_step=1, we run step 1, then stop.
            # So we check AFTER completion? Or before?
            # If max_step=1, we want loop to run for step_idx=1.
            # Then next iter step_idx=2.
            # So if step_idx > max_step: break
            
            if max_step is not None and step_idx > max_step:
                print(f"\n🛑 Reached max_step ({max_step}) - Stopping early.")
                write_ledger({
                    "timestamp_utc": utc_now(),
                    "event": "run_stopped_early",
                    "max_step": max_step,
                    "last_step_completed": step_idx - 1,
                    "run_id": run_id,
                    "run_dir": run_dir,
                })
                break

            agent_name = agent_cfg["name"]
            prompt_path = agent_cfg["prompt_path"]

            # ------------------------------------------------------------------
            # Provider Selection (per-agent)
            # ------------------------------------------------------------------
            
            # When run_pipeline.py sets PROVIDER env var (via --dry_run or --mode),
            # it should override ALL agents, including per-agent overrides.
            # Otherwise, per-agent overrides take precedence.
            env_provider = os.getenv("PROVIDER")
            
            # If env var is set, use it for all agents (--dry_run or --mode flag)
            # Otherwise, respect per-agent overrides, then config default
            if env_provider:
                provider_name = env_provider
            else:
                provider_name = (
                    agent_cfg.get("provider") or  # Per-agent override
                    config.get("provider")         # Config default
                )
            
            provider = get_provider(provider_name)
            
            # Diagnostic logging
            print(f"[Provider] step={step_idx} agent={agent_name} provider={provider_name}")
            print(f"\n▶ Running Step {step_idx}: {agent_name}")

            # Validate prompt file exists
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(
                    f"Missing prompt file for {agent_name}: {prompt_path}"
                )

            prompt_template = load_text(prompt_path)

            # Use simple string replacement instead of .format() to avoid conflicts
            # with JSON braces in prompt templates (which contain JSON examples)
            # Prune and dump system state
            pruned_state = prune_system_state(system_state, agent_name)
            system_state_json = json.dumps(pruned_state, indent=2)
            
            prompt = prompt_template
            prompt = prompt.replace("{business_brief}", business_brief)
            prompt = prompt.replace("{sme_notes}", sme_notes)
            prompt = prompt.replace("{system_state}", system_state_json)

            # For the assessment designer, inject a pre-computed flat objective list
            # so the LLM cannot truncate or skip later modules.
            if agent_name == "assessment_designer_agent":
                modules = system_state.get("curriculum", {}).get("modules", [])
                obj_rows = []
                for mod in modules:
                    mid = mod.get("module_id", "?")
                    for obj in mod.get("objectives", []):
                        obj_rows.append(f"| {len(obj_rows)+1} | {mid} | {obj} |")
                obj_table = (
                    "## PRE-COMPUTED OBJECTIVE LIST (AUTHORITATIVE — DO NOT DEVIATE)\n"
                    f"Total objectives: {len(obj_rows)}\n"
                    "| # | module_id | objective_text |\n"
                    "|---|---|---|\n"
                    + "\n".join(obj_rows)
                    + f"\n\nYou MUST generate EXACTLY {len(obj_rows)} questions, one per row above, in order.\n"
                    "Each question's objective_ref MUST exactly match the objective_text column.\n"
                )
                prompt = obj_table + "\n\n" + prompt


            response = provider.run(prompt)

            # ------------------------------------------------------------------
            # Validation
            # ------------------------------------------------------------------

            # Parse JSON response with robust extraction
            parsed = None
            parse_error = None
            
            try:
                parsed = parse_json_object(response)
            except Exception as e:
                parse_error = e
                
                # Retry logic: only for parse errors, only once
                if retry_once_on_parse_error and "PARSE_ERROR" in str(e):
                    print(f"⚠️  Parse failed, retrying {agent_name} once...")
                    write_ledger({
                        "timestamp_utc": utc_now(),
                        "event": "parse_retry",
                        "step_idx": step_idx,
                        "agent": agent_name,
                        "error": str(e)[:200],
                    })
                    
                    # Retry the provider call
                    response = provider.run(prompt)
                    
                    try:
                        parsed = parse_json_object(response)
                        parse_error = None  # Success on retry
                        print(f"✅ Retry successful for {agent_name}")
                    except Exception as retry_error:
                        parse_error = retry_error
            
            # If parsing still failed, stop immediately
            if parse_error:
                error_category = "PARSE_ERROR" if "PARSE_ERROR" in str(parse_error) else "VALIDATION_ERROR"
                error_snippet = response[:300] if len(response) > 300 else response
                
                # Write error file
                error_file = os.path.join(run_dir, f"{step_idx:02d}_{agent_name}_error.txt")
                with open(error_file, "w") as f:
                    f.write(f"Error Category: {error_category}\n")
                    f.write(f"Step: {step_idx}\n")
                    f.write(f"Agent: {agent_name}\n")
                    f.write(f"Provider: {provider_name}\n")
                    f.write(f"\nError Message:\n{str(parse_error)}\n")
                    f.write(f"\nRaw Response (first 1000 chars):\n{response[:1000]}\n")
                
                # Console error
                print(f"\n❌ PIPELINE FAILURE")
                print(f"Step: {step_idx}")
                print(f"Agent: {agent_name}")
                print(f"Provider: {provider_name}")
                print(f"Category: {error_category}")
                print(f"Error: {str(parse_error)}")
                print(f"\nResponse snippet (first 300 chars):\n{error_snippet}...")
                print(f"\nFull error details saved to: {error_file}")
                
                # Ledger entry
                write_ledger({
                    "timestamp_utc": utc_now(),
                    "event": "run_failed",
                    "reason": error_category.lower(),
                    "step_idx": step_idx,
                    "agent": agent_name,
                    "provider": provider_name,
                    "error": str(parse_error)[:500],
                    "error_file": error_file,
                    "run_id": run_id,
                    "run_dir": run_dir,
                })
                
                raise ValidationError(f"{error_category}: {str(parse_error)}")
            
            # Validate using config-driven validation settings
            validation_config = ValidationConfig(
                min_deliverable_chars=min_deliverable_chars,
                placeholder_markers=placeholder_markers
            )
            
            try:
                validate_agent_output(agent_name, parsed, validation_config)
            except Exception as val_error:
                # Validation failure (not parse error)
                error_snippet = response[:300] if len(response) > 300 else response
                
                # Write error file
                error_file = os.path.join(run_dir, f"{step_idx:02d}_{agent_name}_error.txt")
                with open(error_file, "w") as f:
                    f.write(f"Error Category: VALIDATION_ERROR\n")
                    f.write(f"Step: {step_idx}\n")
                    f.write(f"Agent: {agent_name}\n")
                    f.write(f"Provider: {provider_name}\n")
                    f.write(f"\nError Message:\n{str(val_error)}\n")
                    f.write(f"\nParsed Output:\n{json.dumps(parsed, indent=2)}\n")
                
                # Console error
                print(f"\n❌ PIPELINE FAILURE")
                print(f"Step: {step_idx}")
                print(f"Agent: {agent_name}")
                print(f"Provider: {provider_name}")
                print(f"Category: VALIDATION_ERROR")
                print(f"Error: {str(val_error)}")
                print(f"\nFull error details saved to: {error_file}")
                
                # Ledger entry
                write_ledger({
                    "timestamp_utc": utc_now(),
                    "event": "run_failed",
                    "reason": "validation_error",
                    "step_idx": step_idx,
                    "agent": agent_name,
                    "provider": provider_name,
                    "error": str(val_error)[:500],
                    "error_file": error_file,
                    "run_id": run_id,
                    "run_dir": run_dir,
                })
                
                raise ValidationError(f"VALIDATION_ERROR: {str(val_error)}")

            deliverable = parsed["deliverable_markdown"]
            updated_state = parsed["updated_state"]
            open_questions = parsed["open_questions"]

            # ------------------------------------------------------------------
            # Save Outputs
            # ------------------------------------------------------------------

            md_path = os.path.join(run_dir, f"{step_idx:02d}_{agent_name}.md")
            state_path = os.path.join(run_dir, f"{step_idx:02d}_{agent_name}_state.json")

            with open(md_path, "w") as f:
                f.write(deliverable)

            with open(state_path, "w") as f:
                json.dump(parsed, f, indent=2)

            # ------------------------------------------------------------------
            # Merge State
            # ------------------------------------------------------------------

            system_state = deep_merge(system_state, updated_state)
            
            # ------------------------------------------------------------------
            # Write Checkpoint and Update Manifest
            # ------------------------------------------------------------------
            
            write_checkpoint(checkpoints_dir, step_idx, system_state)
            manifest["current_step_completed"] = step_idx
            manifest["providers_used_by_step"][str(step_idx)] = provider_name
            write_manifest(Path(run_dir), manifest)

            # ------------------------------------------------------------------
            # Approval Gate Logic
            # ------------------------------------------------------------------

            should_gate = False

            if gate_strategy == "per_phase":
                should_gate = step_idx in phase_gates
            elif gate_strategy == "per_agent":
                should_gate = agent_cfg.get("gate", False)

            gate_type = "phase_gate"
            gate_reason = "routine_check"
            risk_metadata = {}

            if risk_enabled:
                risk_triggered, gate_type, gate_reason, risk_metadata = evaluate_risk_gate(
                    open_questions, deliverable, agent_name, risk_cfg
                )
                if risk_triggered:
                    should_gate = True

            if should_gate:
                if gate_type == "risk_gate":
                    risk_metadata["risk_auto_override"] = risk_cfg.get("auto_override", True)

                approval_gate(
                    step_idx=step_idx,
                    agent_name=agent_name,
                    gate_strategy=gate_strategy,
                    run_id=run_id,
                    run_dir=run_dir,
                    write_ledger_fn=write_ledger,
                    utc_now_fn=utc_now,
                    approval_token=approval_token,
                    gate_type=gate_type,
                    gate_reason=gate_reason,
                    risk_metadata=risk_metadata,
                )

        # ----------------------------------------------------------------------
        # Final State
        # ----------------------------------------------------------------------

        final_state_path = os.path.join(run_dir, "99_final_state.json")
        with open(final_state_path, "w") as f:
            json.dump(system_state, f, indent=2)
        
        # Update manifest to completed
        manifest["status"] = "completed"
        write_manifest(Path(run_dir), manifest)

        write_ledger({
            "timestamp_utc": utc_now(),
            "event": "run_completed",
            "run_dir": run_dir,
        })

        # Generate Audit Summary
        summary_path = generate_audit_summary(run_id, run_dir, ledger_path=LEDGER_PATH)
        if summary_path:
            print(f"📄 Audit summary generated: {summary_path}")

        print("\n✅ RUN COMPLETE")

    except ApprovalRejectedError:
        if manifest:
            manifest["status"] = "aborted"
            write_manifest(Path(run_dir), manifest)
        print("\n⛔ Run stopped by user approval rejection.")
        
        # Generate Audit Summary (attempt best effort)
        try:
            # We need to access run_id/run_dir from outer scope
            # They are defined in run_pipeline before try block, but safely accessed here?
            # run_pipeline local variables are accessible in except block.
            # However, if run_dir wasn't set yet (extremely early failure), we check.
            if run_dir:
                run_id_val = Path(run_dir).name
                summary_path = generate_audit_summary(run_id_val, run_dir, ledger_path=LEDGER_PATH)
                if summary_path:
                    print(f"📄 Audit summary generated: {summary_path}")
        except Exception:
            pass

        sys.exit(1)

    except Exception as e:
        if manifest:
            manifest["status"] = "failed"
            write_manifest(Path(run_dir), manifest)
        write_ledger({
            "timestamp_utc": utc_now(),
            "event": "run_failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "run_id": run_id if 'run_id' in locals() else None,
            "run_dir": run_dir if 'run_dir' in locals() else None,
        })
        print("\n❌ RUN FAILED")
        traceback.print_exc()

        # Generate Audit Summary (attempt best effort)
        try:
            if run_dir:
                run_id_val = Path(run_dir).name
                summary_path = generate_audit_summary(run_id_val, run_dir, ledger_path=LEDGER_PATH)
                if summary_path:
                    print(f"📄 Audit summary generated: {summary_path}")
        except Exception:
            pass

        sys.exit(1)


def main():
    """Entry point for running a fresh pipeline."""
    run_pipeline()

# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()