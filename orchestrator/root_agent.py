import json
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from orchestrator.providers import get_provider
from orchestrator.validation import validate_agent_output, ValidationConfig
from orchestrator.json_tools import parse_json_object
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

class ApprovalRejectedError(Exception):
    pass

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

# ------------------------------------------------------------------------------
# Approval Gate
# ------------------------------------------------------------------------------

def approval_gate(
    step_idx: int,
    agent_name: str,
    gate_strategy: str,
    run_id: str,
    run_dir: str,
    approval_token: str = "APPROVE",
    gate_type: str = "phase_gate",
    gate_reason: str = "routine_check",
    force_gate: bool = False,
    risk_metadata: Dict[str, Any] = None,
):
    
    # Log Risk Gate Event (Audit Requirement)
    if gate_type == "risk_gate":
        event = {
            "timestamp_utc": utc_now(),
            "event": "risk_gate_forced",
            "step_idx": step_idx,
            "agent": agent_name,
            "agent_name": agent_name,
            "gate_strategy": gate_strategy,
            "gate_type": gate_type,
            "gate_reason": gate_reason,
            "run_id": run_id,
            "run_dir": run_dir,
        }
        if risk_metadata:
            event.update(risk_metadata)
        write_ledger(event)

    # Check for Auto-Approval
    auto_approve_env = os.getenv("AUTO_APPROVE", "").lower()
    is_auto_approve = auto_approve_env in ("1", "true", "yes", "on")

    # Risk Gate Override Logic
    # If it's a risk gate and auto-approve is ON, we check strictness policy.
    # Default: auto_override=True (Don't pause, just log override)
    # Strict: auto_override=False (Force pause even if auto_approve is ON)
    
    if is_auto_approve:
        should_pause = False
        approval_reason = "Auto-approval enabled via CLI"

        if gate_type == "risk_gate":
            # Check for risk gate specific override policy
            # Default to True (safe default that preserves non-blocking behavior unless configured otherwise)
            # The caller passes risk_auto_override.
            risk_auto_override = risk_metadata.get("risk_auto_override", True) if risk_metadata else True
            
            if not risk_auto_override:
                # STRICT MODE: Force pause
                should_pause = True
                print(f"\n🛑 RISK GATE (STRICT): Auto-approve disabled for risk gates.")
            else:
                # DEFAULT MODE: Override and log
                approval_reason = "Auto-approve override after risk gate"
                print(f"\n⚡ AUTO-APPROVED risk gate at step {step_idx} ({approval_reason})")
        else:
            print(f"\n⚡ AUTO-APPROVED gate at step {step_idx} ({agent_name}, {gate_strategy})")

        if not should_pause:
            write_ledger({
                "timestamp_utc": utc_now(),
                "event": "step_approved",
                "approval_mode": "auto",
                "approval_source": "cli_flag",
                "approval_reason": approval_reason,
                "gate_strategy": gate_strategy,
                "step_idx": step_idx,
                "agent_name": agent_name,
                "agent": agent_name, # Attribution compatibility
                "run_id": run_id,
                "run_dir": run_dir,
                "gate_type": gate_type,
                "gate_reason": gate_reason,
            })
            return

    # If we are here, either auto-approve is OFF, OR it's a strict risk gate that forces pause.

    # Check if this gate is FORCED (cannot be auto-approved, but we handled auto-approve above for now)
    # Note: Requirement says "force a gate" which implies even if auto-approve might be on? 
    # Logic check: "force a gate at that step (even if not in phase_gates)"
    # However, user constraint: "Do NOT remove phase gates [3,6,9]".
    # Auto-approval currently bypasses everything. 
    # Requirement 4: CLI approval prompt must clearly say it is a risk-triggered gate.
    
    # If auto-approve is ON, should we still stop for risk?
    # The requirement says "force a gate". Usually "force" implies overriding auto-approve, 
    # but the prompt says "If risk escalation enabled ... THEN force a gate ... (even if not in phase_gates)".
    # It does NOT explicitly say "override auto-approve". 
    # Standard interpretation: "force a gate" means add a gate where one usually isn't.
    # Auto-approval bypasses gates. So if auto-approve is True, it will bypass this forced gate too unless specified otherwise.
    # Given "safe defaults off", and "force a gate", I will assume it behaves like a normal gate 
    # that is subject to auto-approval unless the user explicitly wants INTERVENTION.
    # BUT, "risk-triggered" usually implies safety. 
    # Let's look at the constraints: "UX requirement: CLI approval prompt must clearly say it is a risk-triggered gate."
    # If auto-approve skips it, the CLI prompt won't be seen.
    # Let's stick to standard gate behavior for now (skippable by auto-approve) to avoid breaking "auto-run" workflows,
    # unless "force" implies "manual intervention required".
    # Wait, if I am running in CI/CD with auto-approve, I probably don't want it to hang on a prompt.
    # So I will treat it as a gate that IS present, but adheres to auto-approve flag.

    # Update prompt for Risk Gates
    if gate_type == "risk_gate":
        print(f"\n⚠️  RISK GATE: {gate_reason}")
        print(f"Triggered by agent: {agent_name} at step {step_idx}")
        prompt = f"Type {approval_token} to OVERRIDE and continue, anything else to stop: "
    else:
        prompt = (
            f"\n⛔ APPROVAL GATE\n"
            f"Step {step_idx}: {agent_name}\n"
            f"Type {approval_token} to continue, anything else to stop: "
        )
    user_input = input(prompt).strip()

    if user_input.lower() != approval_token.lower():
        write_ledger({
            "timestamp_utc": utc_now(),
            "event": "run_failed",
            "reason": "approval_rejected",
            "step_idx": step_idx,
            "agent": agent_name,
            "agent_name": agent_name, # Attribution compatibility
            "gate_strategy": gate_strategy,
            "gate_type": gate_type,
            "gate_reason": gate_reason,
            "run_id": run_id,
            "run_dir": run_dir,
        })
        raise ApprovalRejectedError("Approval rejected by user")

    write_ledger({
        "timestamp_utc": utc_now(),
        "event": "step_approved",
        "approval_mode": "manual",
        "approval_source": "stdin",
        "step_idx": step_idx,
        "agent": agent_name,
        "agent_name": agent_name, # Attribution compatibility
        "gate_strategy": gate_strategy,
        "gate_strategy": gate_strategy,
        "gate_type": gate_type,
        "gate_reason": gate_reason,
        "run_id": run_id,
        "run_dir": run_dir,
    })

# ------------------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------------------

def run_pipeline(
    config_path: str = None,
    run_dir: str = None,
    start_step: int = 1,
    initial_state: dict = None,
    config_overrides: dict = None,
    governance_profile: str = None,
) -> None:
    """
    Execute the agent pipeline with optional resume support.
    
    Args:
        config_path: Path to config file (default: config/run_config.json)
        run_dir: Existing run directory for resume (default: create new)
        start_step: Step index to start from (default: 1)
        initial_state: Initial state for resume (default: get_initial_state())
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
        # Load Inputs
        # ----------------------------------------------------------------------

        business_brief = load_text(os.path.join(INPUTS_DIR, "business_brief.md"))
        sme_notes = load_text(os.path.join(INPUTS_DIR, "sme_notes.md"))

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
                    Path(INPUTS_DIR) / "business_brief.md",
                    Path(INPUTS_DIR) / "sme_notes.md",
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

        # Default phase gates: 3 / 6 / 9
        phase_gates = approval_cfg.get("phase_gates", [3, 6, 9])
        try:
            phase_gates = [int(x) for x in phase_gates]
        except Exception:
            phase_gates = [3, 6, 9]

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
            system_state_json = json.dumps(system_state, indent=2)
            
            prompt = prompt_template
            prompt = prompt.replace("{business_brief}", business_brief)
            prompt = prompt.replace("{sme_notes}", sme_notes)
            prompt = prompt.replace("{system_state}", system_state_json)

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

            # risk_gate_logic
            gate_type = "phase_gate"
            gate_reason = "routine_check"
            risk_metadata = {}

            if risk_enabled:
                # Check 1: Open Questions Threshold
                # Weighted counting: CRITICAL/BLOCKER/MAJOR count, MINOR usually does not.
                # Controlled by weighted_severities AllowList.
                
                # Default: Count everything except MINOR (match previous hardcoded logic + unprefixed)
                # Actually, previous logic was: count if NOT MINOR. 
                # New Logic: Count if severity IN weighted_severities.
                
                weighted_severities = risk_cfg.get("weighted_severities", ["CRITICAL", "BLOCKER", "MAJOR", "UNPREFIXED"])
                # Normalize to set for fast lookup
                weighted_severities_set = {s.upper() for s in weighted_severities}

                weighted_count = 0
                for q in open_questions:
                    q_upper = q.upper().strip()
                    
                    # Determine severity
                    severity = "UNPREFIXED"
                    if q_upper.startswith("CRITICAL:"):
                        severity = "CRITICAL"
                    elif q_upper.startswith("BLOCKER:"):
                        severity = "BLOCKER"
                    elif q_upper.startswith("MAJOR:"):
                        severity = "MAJOR"
                    elif q_upper.startswith("MINOR:"):
                        severity = "MINOR"
                    
                    if severity in weighted_severities_set:
                        weighted_count += 1
                
                total_count = len(open_questions)

                if weighted_count >= risk_open_questions_threshold:
                    should_gate = True
                    gate_type = "risk_gate"
                    gate_reason = "open_questions_threshold"
                    risk_metadata = {
                        "observed_open_questions_count_weighted": weighted_count,
                        "observed_open_questions_count_total": total_count,
                        "observed_open_questions_count": weighted_count, # Legacy compat
                        "open_questions_threshold": risk_open_questions_threshold,
                        "weighted_severities": list(weighted_severities_set)
                    }
                
                # Check 2: QA Critical Errors
                # Only applicable if this agent is the qa_agent
                # Triggers if:
                # A) open_questions has items starting with "CRITICAL:" or "BLOCKER:"
                # B) deliverable_markdown line contains "Severity: Critical"
                if risk_force_on_qa_critical and agent_name == "qa_agent":
                    # Count critical open questions
                    critical_questions = [
                        q for q in open_questions 
                        if q.upper().strip().startswith("CRITICAL:") or q.upper().strip().startswith("BLOCKER:")
                    ]
                    
                    # Check markdown for Severity: Critical
                    has_severity_critical = "Severity: Critical" in deliverable
                    
                    critical_count = len(critical_questions)
                    if has_severity_critical:
                        critical_count = max(critical_count, 1) # Ensure at least 1 count if severity line exists
                        
                    if critical_count > 0:
                        should_gate = True
                        gate_type = "risk_gate"
                        gate_reason = "qa_critical"
                        risk_metadata = {
                            "qa_critical_error_count": critical_count
                        }

            if should_gate:
                # Add auto_override policy to risk metadata if it's a risk gate
                if gate_type == "risk_gate":
                    risk_metadata["risk_auto_override"] = risk_cfg.get("auto_override", True)

                approval_gate(
                    step_idx, 
                    agent_name, 
                    gate_strategy, 
                    run_id, 
                    run_dir, 
                    approval_token,
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