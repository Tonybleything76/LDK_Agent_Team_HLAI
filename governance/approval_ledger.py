"""
Hash-chained append-only approval ledger.

Each entry is a JSON line in ``governance/approval_ledger.jsonl`` with:
  - ledger_seq        Sequential integer (1-based)
  - integrity_hash    SHA-256 of the entry payload (excluding this field)
  - previous_entry_hash  integrity_hash of the preceding entry (genesis = "0"*64)

This provides tamper-evidence: any mutation to a historical entry breaks the
chain and is detected by ``verify_ledger()``.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_GENESIS_HASH = "0" * 64


def _get_ledger_path() -> Path:
    """Return the ledger file path, resolved from this file's location. Patchable in tests."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "governance" / "approval_ledger.jsonl"


def _canonical_json(data: Any) -> str:
    """Canonical JSON for hashing (sorted keys, no whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_last_entry() -> "tuple[int, str]":
    """Return (last_seq, last_hash) from the ledger, or (0, genesis) if empty."""
    ledger_path = Path(_get_ledger_path())
    if not ledger_path.exists():
        return 0, _GENESIS_HASH

    with ledger_path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
            return entry.get("ledger_seq", 0), entry.get("integrity_hash", _GENESIS_HASH)
        except json.JSONDecodeError:
            raise ValueError("Ledger is corrupted: last non-empty line is not valid JSON.")

    return 0, _GENESIS_HASH


def append_entry(
    action: str,
    actor: str,
    target_artifact_id: str,
    evidence_ref: Optional[str] = None,
    decision_metadata: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Append a new entry to the ledger.

    Args:
        action:             Event type (e.g. ``"gate_approved"``).
        actor:              Who/what performed the action (e.g. ``"AUTO_APPROVE"``).
        target_artifact_id: Identifier of the artifact being acted upon.
        evidence_ref:       Optional reference to supporting evidence.
        decision_metadata:  Optional free-form metadata dict.

    Returns:
        The full entry dict that was written (including ``integrity_hash``).
    """
    last_seq, previous_hash = _read_last_entry()
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    payload: Dict[str, Any] = {
        "timestamp_utc": timestamp,
        "ledger_seq": last_seq + 1,
        "action": action,
        "actor": actor,
        "target_artifact_id": target_artifact_id,
        "evidence_ref": evidence_ref,
        "decision_metadata": decision_metadata or {},
        "previous_entry_hash": previous_hash,
    }

    payload["integrity_hash"] = _sha256(_canonical_json(payload))

    ledger_path = Path(_get_ledger_path())
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")

    return payload


def verify_ledger() -> bool:
    """
    Verify the integrity of the entire ledger.

    Returns:
        ``True`` if the ledger is valid.

    Raises:
        ValueError: On the first detected inconsistency (bad sequence, hash
                    mismatch, or corrupt JSON).
    """
    ledger_path = Path(_get_ledger_path())
    if not ledger_path.exists():
        return True  # Empty ledger is valid

    expected_prev = _GENESIS_HASH
    expected_seq = 1

    with ledger_path.open("r", encoding="utf-8") as fh:
        for line_num, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                raise ValueError(f"Line {line_num}: invalid JSON")

            if entry.get("ledger_seq") != expected_seq:
                raise ValueError(
                    f"Line {line_num}: sequence mismatch "
                    f"(expected {expected_seq}, got {entry.get('ledger_seq')})"
                )

            if entry.get("previous_entry_hash") != expected_prev:
                raise ValueError(
                    f"Line {line_num}: previous_entry_hash mismatch"
                )

            stored_hash = entry.get("integrity_hash")
            calc_payload = {k: v for k, v in entry.items() if k != "integrity_hash"}
            if _sha256(_canonical_json(calc_payload)) != stored_hash:
                raise ValueError(f"Line {line_num}: Integrity hash mismatch — content tampered")

            expected_prev = stored_hash
            expected_seq += 1

    return True
