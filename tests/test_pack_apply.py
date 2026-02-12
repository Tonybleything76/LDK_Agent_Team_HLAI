import os
import shutil
import json
import pytest
import sys
import hashlib
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.commands import pack_apply
from utils import hashing
import governance.approval_ledger

def setup_pack(root, version, files, corrupted_manifest=False, tampered_file=False):
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
        
        if tampered_file:
            # We DON'T update the file on disk, but we record the SHA as if it was content
            # Wait, valid manifest means SHA matches content.
            # To simulate "Tampered", we write content X, record SHA Y.
            # Here: compute SHA of content.
            # We want actual_sha != expected_sha.
            # So let's record a DIFFERENT sha.
            sha = "badsha" * 10
            
        manifest_files.append({"path": rel_path, "sha256": sha})
        
    manifest_data = {
        "pack_version": version,
        "generated_at_utc": "2025-01-01T00:00:00Z",
        "git_commit_hash": "abc1234",
        "proposal_id": "prop-123",
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


class TestPackApply:
    
    @pytest.fixture
    def setup_env(self, tmp_path, monkeypatch):
        # Create directory structure
        (tmp_path / "knowledge" / "packs").mkdir(parents=True)
        (tmp_path / "knowledge" / "active").mkdir(parents=True)
        (tmp_path / "governance").mkdir(parents=True)
        (tmp_path / "cli" / "commands").mkdir(parents=True)
        
        # Mock project root resolution in pack_apply
        fake_dirname = str(tmp_path / "cli" / "commands")
        
        # We need to mock os.path.dirname BUT only when called with __file__ from pack_apply?
        # No, `pack_apply` imports `os`. `pack_apply.os` is the `os` module.
        # If we patch `pack_apply.os.path.dirname`, it affects all calls in that module.
        # `execute` calls `os.path.dirname(__file__)`.
        # We can just patch `os.path.dirname` globally? Danger.
        
        # SAFER: Patch `pack_apply.execute` to locally set project_root? No.
        # Patching `os.path.dirname` is okay if we control the return value based on input?
        # Too complex.
        
        # Alternative: We can set `pack_apply.__file__`?
        # `__file__` is a global in the module.
        monkeypatch.setattr(pack_apply, '__file__', str(tmp_path / "cli" / "commands" / "pack_apply.py"))
        
        # Patch approval_ledger._get_ledger_path
        # We need to patch the function in the MODULE where it is defined.
        monkeypatch.setattr(governance.approval_ledger, '_get_ledger_path', lambda: str(tmp_path / "governance" / "approval_ledger.jsonl"))
        
        # Capture exit code
        self.exit_code = None
        def mock_exit(code):
            self.exit_code = code
            raise SystemExit(code)
        monkeypatch.setattr(sys, 'exit', mock_exit)
        
        return tmp_path

    def test_apply_happy_path(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        files = {"proposal.json": "{}", "data.txt": "hello"}
        setup_pack(root, version, files)
        
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor-1"
        args.notes = "Deploying"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 0
        
        # Verify active content
        active_pack_dir = root / "knowledge" / "active" / "packs" / version
        assert (active_pack_dir / "data.txt").read_text() == "hello"
        
        # Verify ACTIVE_PACK.json
        marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        assert marker.exists()
        data = json.loads(marker.read_text())
        assert data['pack_version'] == version
        assert data['git_commit_hash'] == "abc1234"
        
        # Verify Ledger
        ledger_path = root / "governance" / "approval_ledger.jsonl"
        assert ledger_path.exists()
        lines = ledger_path.read_text().strip().split('\n')
        last_entry = json.loads(lines[-1])
        assert last_entry['action'] == "PACK_APPLIED"
        
    def test_apply_idempotent_fail(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"f": "c"})
        
        # First apply
        marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        with open(marker, 'w') as f:
            json.dump({"pack_version": version}, f)
            
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 2 # Blocked
        
    def test_apply_force_success(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"f": "c"})
        
        # Pre-exist
        marker = root / "knowledge" / "active" / "ACTIVE_PACK.json"
        with open(marker, 'w') as f:
            json.dump({"pack_version": version}, f)
            
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = True
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 0
        
    def test_integrity_tampered_file(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"tampered.txt": "real content"}, tampered_file=True)
        # setup_pack with tampered_file=True records WRONG sha in manifest
        
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 2
        
    def test_integrity_manifest_corrupt(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"f": "c"}, corrupted_manifest=True)
        
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 2
        
    def test_integrity_missing_manifest(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"f": "c"})
        os.remove(root / "knowledge" / "packs" / version / "manifest.json")
        
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
            
        assert self.exit_code == 2

    def test_ledger_verification(self, setup_env):
        root = setup_env
        version = "knowledge_v1.0.0"
        setup_pack(root, version, {"f": "c"})
        
        args = MagicMock()
        args.pack_version = version
        args.actor_id = "actor"
        args.force = False
        
        try:
            pack_apply.execute(args)
        except SystemExit:
            pass
        
        # Now verify ledger
        assert governance.approval_ledger.verify_ledger() is True

