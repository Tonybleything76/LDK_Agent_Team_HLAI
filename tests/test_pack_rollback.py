import os
import shutil
import json
import pytest
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.commands import pack_rollback, pack_apply
from utils import hashing
import governance.approval_ledger

def setup_pack(root, version, files, corrupted_manifest=False):
    pack_dir = root / "knowledge" / "packs" / version
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_files = []
    
    for fname, content in files.items():
        fpath = pack_dir / fname
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, 'w') as f:
            f.write(content)
            
        rel_path = str(fpath.relative_to(pack_dir))
        sha = hashing.compute_string_sha256(content)
        manifest_files.append({"path": rel_path, "sha256": sha})
        
    manifest_data = {
        "pack_version": version,
        "git_commit_hash": "abc1234",
        "files": manifest_files
    }
    
    # Compute manifest hash
    check_data = manifest_data.copy()
    canonical = hashing.canonical_json_dumps(check_data)
    m_hash = hashing.compute_string_sha256(canonical)
    
    if corrupted_manifest:
        m_hash = "badhash" * 10
        
    manifest_data['manifest_hash'] = m_hash
    
    with open(pack_dir / "manifest.json", 'w') as f:
        json.dump(manifest_data, f)
        
    return manifest_data

class TestPackRollback:
    
    @pytest.fixture
    def setup_env(self, tmp_path, monkeypatch):
        # Create directory structure
        (tmp_path / "knowledge" / "packs").mkdir(parents=True)
        (tmp_path / "knowledge" / "active").mkdir(parents=True)
        (tmp_path / "knowledge" / "active" / "_snapshots").mkdir(parents=True)
        (tmp_path / "knowledge" / "active" / "packs").mkdir(parents=True)
        (tmp_path / "governance").mkdir(parents=True)
        (tmp_path / "cli" / "commands").mkdir(parents=True)
        
        # Monkeypatch __file__ for pack_rollback to find root
        monkeypatch.setattr(pack_rollback, '__file__', str(tmp_path / "cli" / "commands" / "pack_rollback.py"))
        
        # Patch approval ledger path
        monkeypatch.setattr(governance.approval_ledger, '_get_ledger_path', lambda: str(tmp_path / "governance" / "approval_ledger.jsonl"))
        
        # Capture exit code
        self.exit_code = None
        def mock_exit(code):
            self.exit_code = code
            raise SystemExit(code)
        monkeypatch.setattr(sys, 'exit', mock_exit)
        
        return tmp_path

    def test_rollback_happy_path(self, setup_env):
        root = setup_env
        current_ver = "v2"
        target_ver = "v1"
        
        # 1. Setup Active State (v2)
        active_marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        with open(active_marker, 'w') as f:
            json.dump({"pack_version": current_ver}, f)
            
        # 2. Setup Snapshot (v1)
        snapshot_path = root / "knowledge" / "active" / "_snapshots" / "snap_v1.json"
        with open(snapshot_path, 'w') as f:
            json.dump({"pack_version": target_ver, "git_commit_hash": "hash_v1"}, f)
            
        # 3. Setup Target Pack in Active Store
        (root / "knowledge" / "active" / "packs" / target_ver).mkdir(parents=True)
        
        # Run Rollback
        args = MagicMock()
        args.to_snapshot = "snap_v1"
        args.actor_id = "tester"
        args.notes = "oops"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 0
        
        # Verify ACTIVE_PACK.json restored
        with open(active_marker, 'r') as f:
            data = json.load(f)
        assert data['pack_version'] == target_ver
        
        # Verify Ledger
        ledger = root / "governance" / "approval_ledger.jsonl"
        lines = ledger.read_text().strip().split('\n')
        last = json.loads(lines[-1])
        assert last['action'] == "PACK_ROLLED_BACK"
        assert last['decision_metadata']['previous_pack_version'] == current_ver
        assert last['decision_metadata']['restored_pack_version'] == target_ver

    def test_rollback_restores_pack_dir(self, setup_env):
        root = setup_env
        target_ver = "v1"
        
        # Setup Snapshot
        active_marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        with open(active_marker, 'w') as f:
            json.dump({"pack_version": "v2"}, f)
            
        snapshot_path = root / "knowledge" / "active" / "_snapshots" / "snap_v1.json"
        with open(snapshot_path, 'w') as f:
            json.dump({"pack_version": target_ver}, f)
            
        # Setup Source Pack (but NOT in active store)
        setup_pack(root, target_ver, {"f.txt": "content"})
        
        args = MagicMock()
        args.to_snapshot = "snap_v1.json"
        args.actor_id = "tester"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 0
        
        # Verify Pack Restored
        restored_path = root / "knowledge" / "active" / "packs" / target_ver / "f.txt"
        assert restored_path.exists()
        assert restored_path.read_text() == "content"

    def test_rollback_missing_snapshot(self, setup_env):
        args = MagicMock()
        args.to_snapshot = "missing"
        args.actor_id = "tester"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
        assert self.exit_code == 2

    def test_rollback_corrupted_snapshot(self, setup_env):
        root = setup_env
        snap = root / "knowledge" / "active" / "_snapshots" / "bad.json"
        snap.write_text("{invalid")
        
        args = MagicMock()
        args.to_snapshot = "bad"
        args.actor_id = "tester"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
        assert self.exit_code == 2

    def test_rollback_missing_active_marker(self, setup_env):
        root = setup_env
        # active marker missing
        
        snap = root / "knowledge" / "active" / "_snapshots" / "s.json"
        with open(snap, 'w') as f:
            json.dump({"pack_version": "v1"}, f)
            
        args = MagicMock()
        args.to_snapshot = "s"
        args.actor_id = "tester"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
        assert self.exit_code == 2

    def test_rollback_ledger_failure_transactionality(self, setup_env, monkeypatch):
        # Test that if ledger write fails, we restore ACTIVE_PACK.json
        root = setup_env
        
        # Initial State: v2
        active_marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        with open(active_marker, 'w') as f:
            json.dump({"pack_version": "v2"}, f)
            
        # Snapshot: v1
        snap = root / "knowledge" / "active" / "_snapshots" / "s.json"
        with open(snap, 'w') as f:
            json.dump({"pack_version": "v1"}, f)
            
        # Pack v1 exists in active store
        (root / "knowledge" / "active" / "packs" / "v1").mkdir(parents=True)
        
        # Patch ledger to fail
        def mock_append(*args, **kwargs):
            raise Exception("Ledger Down")
        monkeypatch.setattr(governance.approval_ledger, 'append_entry', mock_append)
        
        args = MagicMock()
        args.to_snapshot = "s"
        args.actor_id = "tester"
        
        try:
            pack_rollback.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 1
        
        # Verify ACTIVE_PACK.json is STILL v2 (reverted)
        with open(active_marker, 'r') as f:
            data = json.load(f)
        assert data['pack_version'] == "v2"
