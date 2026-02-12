import unittest
import os
import shutil
import tempfile
import json
import stat
from unittest.mock import patch, MagicMock

from cli.commands import proposal_create
from governance import approval_ledger

class TestProposalCreate(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        self.knowledge_dir = os.path.join(self.test_dir, 'knowledge')
        self.schemas_dir = os.path.join(self.knowledge_dir, 'schemas')
        self.signals_dir = os.path.join(self.knowledge_dir, 'signals')
        self.proposals_dir = os.path.join(self.knowledge_dir, 'proposals')
        self.governance_dir = os.path.join(self.test_dir, 'governance')
        
        os.makedirs(self.schemas_dir)
        os.makedirs(self.signals_dir)
        os.makedirs(self.proposals_dir)
        os.makedirs(self.governance_dir)
        
        # Copy real schemas
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        for schema in ['improvement_proposal.schema.json']:
            real_path = os.path.join(project_root, 'knowledge', 'schemas', schema)
            shutil.copy(real_path, self.schemas_dir)
            
        # Mock paths
        self.schema_validator_patch = patch('utils.schema_validator.os.path.abspath')
        self.mock_abspath_val = self.schema_validator_patch.start()
        self.mock_abspath_val.return_value = self.test_dir
        self.addCleanup(self.schema_validator_patch.stop)
        
        self.ledger_patch = patch('governance.approval_ledger._get_ledger_path')
        self.mock_get_ledger_path = self.ledger_patch.start()
        self.mock_get_ledger_path.return_value = os.path.join(self.governance_dir, 'approval_ledger.jsonl')
        self.addCleanup(self.ledger_patch.stop)
        
        self.proposal_create_patch = patch('cli.commands.proposal_create.os.path.abspath')
        self.mock_abspath_prop = self.proposal_create_patch.start()
        self.mock_abspath_prop.return_value = self.test_dir
        self.addCleanup(self.proposal_create_patch.stop)

    def create_signal(self, sig_id, tenant_id='tenant-A'):
        path = os.path.join(self.signals_dir, f"{sig_id}.json")
        data = {
            "governance_id": sig_id,
            "schema_version": "1.0.0",
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source": {"type": "pilot_feedback", "origin_id": "user1"},
            "signal_type": "complaint",
            "content": {"summary": "test", "details": "test"},
            "tenant_context": {"tenant_id": tenant_id},
            "pii_scrubbed": True
        }
        with open(path, 'w') as f:
            json.dump(data, f)
        return sig_id

    def test_happy_path(self):
        sig_id = self.create_signal("12345678-1234-5678-1234-567812345678")
        
        args = MagicMock()
        args.signals = sig_id
        args.author_id = "agent-x"
        args.target_path = "agents.librarian"
        args.version_constraint = ">=1.0.0"
        args.rationale = "Fix bug"
        args.proposed_modification = "- old\n+ new"
        args.risk = "LOW"
        args.parent_proposal_id = None
        
        proposal_create.execute(args)
        
        # Verify file
        files = os.listdir(self.proposals_dir)
        self.assertEqual(len(files), 1)
        prop_file = os.path.join(self.proposals_dir, files[0])
        
        with open(prop_file, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data['governance_state'], 'DRAFT')
        self.assertEqual(data['linked_signal_ids'], ["12345678-1234-5678-1234-567812345678"])
        self.assertEqual(data['risk_level'], 'LOW')
        
        # Verify Permissions
        mode = os.stat(prop_file).st_mode
        self.assertFalse(mode & stat.S_IWUSR)
        
        # Verify Ledger
        with open(os.path.join(self.governance_dir, 'approval_ledger.jsonl'), 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['action'], 'PROPOSAL_CREATED')
            self.assertEqual(last_entry['decision_metadata']['tenant_id_context'], 'tenant-A')

    def test_mixed_tenants_failure(self):
        sig1 = self.create_signal("12345678-1234-5678-1234-567812345678", "tenant-A")
        sig2 = self.create_signal("87654321-4321-8765-4321-876543210987", "tenant-B")
        
        args = MagicMock()
        args.signals = f"{sig1},{sig2}"
        
        with self.assertRaises(SystemExit):
            proposal_create.execute(args)

    def test_missing_signal_failure(self):
        args = MagicMock()
        args.signals = "sig-missing"
        
        with self.assertRaises(SystemExit):
            proposal_create.execute(args)
            
    def test_schema_invalid_failure(self):
        sig1 = self.create_signal("12345678-1234-5678-1234-567812345678")
        args = MagicMock()
        args.signals = sig1
        args.author_id = "agent-x"
        args.target_path = "agents.librarian"
        args.version_constraint = ">=1.0.0"
        args.rationale = "Fix bug"
        args.proposed_modification = "diff"
        args.risk = "INVALID_RISK" # Invalid enum
        
        with self.assertRaises(SystemExit):
            proposal_create.execute(args)

    def test_file_exists_failure(self):
        # Create a proposal file that already exists
        sig_id = self.create_signal("12345678-1234-5678-1234-567812345678")
        
        # We need to mock uuid generation to return a known ID, or just pre-create a file 
        # But the command generates a random UUID. 
        # We should patch uuid.uuid4 to return a fixed ID so we can pre-create the collision.
        
        fixed_uuid = "99999999-9999-9999-9999-999999999999"
        
        with patch('cli.commands.proposal_create.uuid.uuid4', return_value=fixed_uuid):
            # Pre-create the file
            target_file = os.path.join(self.proposals_dir, f"{fixed_uuid}.json")
            with open(target_file, 'w') as f:
                f.write("{}")
                
            args = MagicMock()
            args.signals = sig_id
            args.author_id = "agent-x"
            args.target_path = "agents.librarian"
            args.version_constraint = ">=1.0.0"
            args.rationale = "Fix bug"
            args.proposed_modification = "diff"
            args.risk = "LOW"
            
            with self.assertRaises(SystemExit):
                proposal_create.execute(args)

if __name__ == '__main__':
    unittest.main()
