"""
Approval gate logic and risk gate evaluation.

Extracted from root_agent.py to keep the orchestrator focused on pipeline flow.
"""

import os
from typing import Any, Dict, List, Tuple


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

class ApprovalRejectedError(Exception):
    """Raised when a user rejects an approval gate prompt."""
    pass


# --------------------------------------------------------------------------
# Approval Gate
# --------------------------------------------------------------------------

def approval_gate(
    step_idx: int,
    agent_name: str,
    gate_strategy: str,
    run_id: str,
    run_dir: str,
    write_ledger_fn,
    utc_now_fn,
    approval_token: str = "APPROVE",
    gate_type: str = "phase_gate",
    gate_reason: str = "routine_check",
    risk_metadata: Dict[str, Any] = None,
):
    """
    Pause execution and require approval before continuing.

    Supports three approval modes:
    - auto:       AUTO_APPROVE env var is set → log and continue
    - ci_harness: CI_SIMULATE_MANUAL_RISK_APPROVAL is set (risk gates only) → log and continue
    - manual:     Prompt user via stdin

    Args:
        step_idx:        Current pipeline step number.
        agent_name:      Name of the agent at this step.
        gate_strategy:   'per_phase' or 'per_agent'.
        run_id:          Current run identifier.
        run_dir:         Path to the run output directory.
        write_ledger_fn: Callable(event_dict) for audit logging.
        utc_now_fn:      Callable() returning current UTC ISO timestamp string.
        approval_token:  Token the user must type to approve (default: 'APPROVE').
        gate_type:       'phase_gate' or 'risk_gate'.
        gate_reason:     Human-readable reason for the gate.
        risk_metadata:   Extra metadata attached to risk gate ledger events.
    """
    if risk_metadata is None:
        risk_metadata = {}

    # Log risk gate trigger event before any approval decision
    if gate_type == "risk_gate":
        event = {
            "timestamp_utc": utc_now_fn(),
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
        event.update(risk_metadata)
        write_ledger_fn(event)

    # ── Auto-approval ─────────────────────────────────────────────────────
    auto_approve_env = os.getenv("AUTO_APPROVE", "").lower()
    is_auto_approve = auto_approve_env in ("1", "true", "yes", "on")
    auto_approve_source = os.getenv("AUTO_APPROVE_SOURCE", "cli_flag")

    if is_auto_approve:
        should_pause = False

        if auto_approve_source == "profile":
            profile_name = os.getenv("AUTO_APPROVE_PROFILE", "unknown")
            approval_reason = f"Auto-approval enabled by governance profile: {profile_name}"
        else:
            approval_reason = "Auto-approval enabled via CLI flag"

        if gate_type == "risk_gate":
            risk_auto_override = risk_metadata.get("risk_auto_override", True)
            if not risk_auto_override:
                should_pause = True
                print(f"\n🛑 RISK GATE (STRICT): Auto-approve disabled for risk gates.")
            else:
                approval_reason = "Auto-approve override after risk gate"
                print(f"\n⚡ AUTO-APPROVED risk gate at step {step_idx} ({approval_reason})")
        else:
            print(f"\n⚡ AUTO-APPROVED gate at step {step_idx} ({agent_name}, {gate_strategy})")

        if not should_pause:
            write_ledger_fn({
                "timestamp_utc": utc_now_fn(),
                "event": "step_approved",
                "approval_mode": "auto",
                "approval_source": auto_approve_source,
                "approval_reason": approval_reason,
                "gate_strategy": gate_strategy,
                "step_idx": step_idx,
                "agent_name": agent_name,
                "agent": agent_name,
                "run_id": run_id,
                "run_dir": run_dir,
                "gate_type": gate_type,
                "gate_reason": gate_reason,
            })
            return

    # ── CI harness simulation (risk gates only) ───────────────────────────
    ci_simulate = os.getenv("CI_SIMULATE_MANUAL_RISK_APPROVAL", "").lower() in ("1", "true", "yes", "on")
    if ci_simulate and gate_type == "risk_gate":
        print(f"\n🤖 CI HARNESS: Simulating manual approval for risk gate at step {step_idx}")
        print(f"   Gate Type: {gate_type}")
        print(f"   Gate Reason: {gate_reason}")
        print(f"   Agent: {agent_name}")
        write_ledger_fn({
            "timestamp_utc": utc_now_fn(),
            "event": "step_approved",
            "approval_mode": "manual",
            "approval_source": "ci_harness",
            "approval_reason": "Simulated manual approval for CI",
            "gate_strategy": gate_strategy,
            "step_idx": step_idx,
            "agent_name": agent_name,
            "agent": agent_name,
            "run_id": run_id,
            "run_dir": run_dir,
            "gate_type": gate_type,
            "gate_reason": gate_reason,
        })
        return

    # ── Manual approval (stdin) ───────────────────────────────────────────
    if gate_type == "risk_gate":
        print(f"\n⚠️  RISK GATE: {gate_reason}")
        print(f"Triggered by agent: {agent_name} at step {step_idx}")
        prompt_text = f"Type {approval_token} to OVERRIDE and continue, anything else to stop: "
    else:
        prompt_text = (
            f"\n⛔ APPROVAL GATE\n"
            f"Step {step_idx}: {agent_name}\n"
            f"Type {approval_token} to continue, anything else to stop: "
        )

    user_input = input(prompt_text).strip()

    if user_input.lower() != approval_token.lower():
        write_ledger_fn({
            "timestamp_utc": utc_now_fn(),
            "event": "run_failed",
            "reason": "approval_rejected",
            "step_idx": step_idx,
            "agent": agent_name,
            "agent_name": agent_name,
            "gate_strategy": gate_strategy,
            "gate_type": gate_type,
            "gate_reason": gate_reason,
            "run_id": run_id,
            "run_dir": run_dir,
        })
        raise ApprovalRejectedError("Approval rejected by user")

    # Approved manually
    if gate_type == "risk_gate":
        write_ledger_fn({
            "timestamp_utc": utc_now_fn(),
            "event": "risk_gate_approved",
            "run_id": run_id,
            "run_dir": run_dir,
            "step_idx": step_idx,
            "agent": agent_name,
            "gate_reason": gate_reason,
            "approval_mode": "manual",
            "approval_source": "stdin",
        })

    write_ledger_fn({
        "timestamp_utc": utc_now_fn(),
        "event": "step_approved",
        "approval_mode": "manual",
        "approval_source": "stdin",
        "step_idx": step_idx,
        "agent": agent_name,
        "agent_name": agent_name,
        "gate_strategy": gate_strategy,
        "gate_type": gate_type,
        "gate_reason": gate_reason,
        "run_id": run_id,
        "run_dir": run_dir,
    })


# --------------------------------------------------------------------------
# Risk Gate Evaluation
# --------------------------------------------------------------------------

def evaluate_risk_gate(
    open_questions: List[str],
    deliverable: str,
    agent_name: str,
    risk_cfg: Dict[str, Any],
) -> Tuple[bool, str, str, Dict[str, Any]]:
    """
    Evaluate whether a risk gate should trigger after an agent step.

    Checks two conditions:
    1. Weighted open_questions count meets or exceeds threshold.
    2. QA agent output contains CRITICAL/BLOCKER findings (when enabled).

    Args:
        open_questions: List of question strings from the agent output.
        deliverable:    Deliverable markdown string from the agent output.
        agent_name:     Name of the agent that just ran.
        risk_cfg:       The 'risk_gate_escalation' config dict.

    Returns:
        Tuple of (should_gate, gate_type, gate_reason, risk_metadata).
        gate_type is 'risk_gate' if triggered, otherwise 'phase_gate'.
        gate_reason is 'open_questions_threshold' or 'qa_critical' if triggered.
    """
    risk_open_questions_threshold = risk_cfg.get("open_questions_threshold", 8)
    risk_force_on_qa_critical = risk_cfg.get("force_gate_on_qa_critical", True)
    weighted_severities = risk_cfg.get(
        "weighted_severities", ["CRITICAL", "BLOCKER", "MAJOR", "UNPREFIXED"]
    )
    weighted_severities_set = {s.upper() for s in weighted_severities}

    # ── Check 1: Weighted open questions threshold ────────────────────────
    weighted_count = 0
    for q in open_questions:
        q_upper = q.upper().strip()
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

    if weighted_count >= risk_open_questions_threshold:
        return (
            True,
            "risk_gate",
            "open_questions_threshold",
            {
                "observed_open_questions_count_weighted": weighted_count,
                "observed_open_questions_count_total": len(open_questions),
                "observed_open_questions_count": weighted_count,  # legacy compat
                "open_questions_threshold": risk_open_questions_threshold,
                "weighted_severities": list(weighted_severities_set),
            },
        )

    # ── Check 2: QA critical errors ───────────────────────────────────────
    if risk_force_on_qa_critical and agent_name == "qa_agent":
        critical_questions = [
            q for q in open_questions
            if q.upper().strip().startswith("CRITICAL:") or q.upper().strip().startswith("BLOCKER:")
        ]
        has_severity_critical = "Severity: Critical" in deliverable
        critical_count = len(critical_questions)
        if has_severity_critical:
            critical_count = max(critical_count, 1)

        if critical_count > 0:
            return (
                True,
                "risk_gate",
                "qa_critical",
                {"qa_critical_error_count": critical_count},
            )

    return False, "phase_gate", "routine_check", {}


# --------------------------------------------------------------------------
# Phase Gate Config Loader
# --------------------------------------------------------------------------

def load_phase_gates(approval_cfg: Dict[str, Any], gate_strategy: str) -> List[int]:
    """
    Load and validate phase_gates from approval config.

    Raises ValueError if gate_strategy is 'per_phase' and phase_gates is
    missing or contains non-integer values.
    """
    if gate_strategy != "per_phase":
        return []

    if "phase_gates" not in approval_cfg:
        raise ValueError(
            "config.approval.phase_gates is required when gate_strategy is 'per_phase'. "
            "Add it to config/run_config.json (e.g. \"phase_gates\": [3, 6, 9])."
        )

    try:
        gates = [int(x) for x in approval_cfg["phase_gates"]]
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"config.approval.phase_gates contains invalid values: {e}. "
            "Expected a list of integers, e.g. [3, 6, 9]."
        )

    return gates
