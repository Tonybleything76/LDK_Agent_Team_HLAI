import json
import os
import hashlib
from datetime import datetime, timezone

LEDGER_PATH_REL = 'governance/approval_ledger.jsonl'

def _get_ledger_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(project_root, LEDGER_PATH_REL)

def _canonical_json_dumps(data):
    """
    Returns a canonical JSON string for hashing:
    - Sorted keys
    - No whitespace (separators=(',', ':'))
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def _calculate_hash(entry):
    """
    Calculates SHA256 hash of the entry (without integrity_hash).
    """
    canonical = _canonical_json_dumps(entry)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def append_entry(action, actor, target_artifact_id, evidence_ref=None, decision_metadata=None):
    """
    Appends a new entry to the approval ledger with hash chaining.
    """
    ledger_path = _get_ledger_path()
    
    # Read last entry to get sequence number and hash
    last_seq = 0
    previous_hash = "0" * 64 # Genesis hash
    
    if os.path.exists(ledger_path):
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            if lines:
                try:
                    last_line = lines[-1].strip()
                    if last_line:
                        last_entry = json.loads(last_line)
                        last_seq = last_entry.get('ledger_seq', 0)
                        previous_hash = last_entry.get('integrity_hash', "0" * 64)
                except json.JSONDecodeError:
                    raise ValueError("Ledger file is corrupted (last line invalid JSON).")

    new_seq = last_seq + 1
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    entry_payload = {
        "timestamp_utc": timestamp,
        "ledger_seq": new_seq,
        "action": action,
        "actor": actor,
        "target_artifact_id": target_artifact_id,
        "evidence_ref": evidence_ref,
        "decision_metadata": decision_metadata or {},
        "previous_entry_hash": previous_hash
    }
    
    # Calculate integrity hash
    integrity_hash = _calculate_hash(entry_payload)
    entry_payload['integrity_hash'] = integrity_hash
    
    # Append to file
    # Ensure directory exists
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    
    with open(ledger_path, 'a') as f:
        f.write(json.dumps(entry_payload) + '\n')
        
    return entry_payload

def verify_ledger():
    """
    Verifies the integrity of the ledger.
    Returns True if valid, raises ValueError if invalid.
    """
    ledger_path = _get_ledger_path()
    if not os.path.exists(ledger_path):
        return True # Empty ledger is valid
        
    with open(ledger_path, 'r') as f:
        lines = f.readlines()
        
    expected_prev_hash = "0" * 64
    expected_seq = 1
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(f"Line {i+1}: Invalid JSON")
            
        # Check sequence
        if entry.get('ledger_seq') != expected_seq:
            raise ValueError(f"Line {i+1}: Sequence mismatch. Expected {expected_seq}, got {entry.get('ledger_seq')}")
            
        # Check previous hash
        if entry.get('previous_entry_hash') != expected_prev_hash:
            raise ValueError(f"Line {i+1}: Previous hash mismatch. Expected {expected_prev_hash}, got {entry.get('previous_entry_hash')}")
            
        # Verify integrity hash
        stored_hash = entry.get('integrity_hash')
        # Create copy without integrity_hash for calculation
        calc_payload = entry.copy()
        calc_payload.pop('integrity_hash', None)
        
        calculated_hash = _calculate_hash(calc_payload)
        
        if calculated_hash != stored_hash:
            raise ValueError(f"Line {i+1}: Integrity hash mismatch. Content tampered.")
            
        # Prepare for next iteration
        expected_prev_hash = stored_hash
        expected_seq += 1
        
    return True
