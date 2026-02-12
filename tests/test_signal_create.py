import unittest
import os
import shutil
import tempfile
import json
import stat
from unittest.mock import patch, MagicMock

from cli.commands import signal_create
from governance import approval_ledger
from utils import schema_validator

class TestSignalCreate(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test project root
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        self.knowledge_dir = os.path.join(self.test_dir, 'knowledge')
        self.schemas_dir = os.path.join(self.knowledge_dir, 'schemas')
        self.signals_dir = os.path.join(self.knowledge_dir, 'signals')
        self.governance_dir = os.path.join(self.test_dir, 'governance')
        
        os.makedirs(self.schemas_dir)
        os.makedirs(self.governance_dir)
        
        # Copy real schema to temp schemas dir
        # We must calculate this path BEFORE starting any mocks that affect path resolution
        # We use explicit os module reference to ensure we use the real one before patching
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        real_schema_path = os.path.join(project_root, 'knowledge', 'schemas', 'improvement_signal.schema.json')
        shutil.copy(real_schema_path, self.schemas_dir)
        
        # Now we can start patches
        # Use addCleanup to ensure they are stopped even if tearDown or other things fail
        
        # Mocking for schema_validator
        self.schema_validator_patch = patch('utils.schema_validator.os.path.abspath')
        self.mock_abspath_val = self.schema_validator_patch.start()
        self.addCleanup(self.schema_validator_patch.stop)
        
        # Mocking for approval_ledger
        self.ledger_patch = patch('governance.approval_ledger._get_ledger_path')
        self.mock_get_ledger_path = self.ledger_patch.start()
        self.mock_get_ledger_path.return_value = os.path.join(self.governance_dir, 'approval_ledger.jsonl')
        self.addCleanup(self.ledger_patch.stop)
        
        # Mocking for signal_create
        self.signal_create_patch = patch('cli.commands.signal_create.os.path.abspath')
        self.mock_abspath_sig = self.signal_create_patch.start()
        self.addCleanup(self.signal_create_patch.stop)

    # tearDown is no longer needed as we use addCleanup

    def test_signal_creation_success(self):
        # Setup mocks to point to temporary directory
        # We need os.path.abspath used in signal_create to return self.test_dir
        # signal_create.py: project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.mock_abspath_sig.return_value = self.test_dir
        
        # We also need schema_validator to find the schema in self.test_dir
        # schema_validator.py: project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.mock_abspath_val.return_value = self.test_dir

        args = MagicMock()
        args.source_type = 'operator_observation'
        args.origin_id = 'test_operator'
        args.signal_type = 'observation'
        args.summary = 'Test Summary'
        args.details = 'Test Details'
        args.affected_artifacts = ['artifact-123']
        args.tenant_id = 'test-tenant'
        args.course_id = 'course-456'
        
        signal_create.execute(args)
        
        # Verify signal file created
        files = os.listdir(self.signals_dir)
        self.assertEqual(len(files), 1)
        signal_file = os.path.join(self.signals_dir, files[0])
        
        with open(signal_file, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data['source']['type'], 'operator_observation')
        self.assertEqual(data['content']['summary'], 'Test Summary')
        self.assertTrue(data['pii_scrubbed'])
        
        # Verify Read-Only
        mode = os.stat(signal_file).st_mode
        self.assertTrue(mode & stat.S_IRUSR)
        self.assertFalse(mode & stat.S_IWUSR) # Not writable
        
    def test_ledger_integrity(self):
        # Add entry
        payload = approval_ledger.append_entry("TEST_ACTION", "actor", "target", "evidence")
        
        # Verify
        self.assertTrue(approval_ledger.verify_ledger())
        
        # Tamper
        ledger_path = os.path.join(self.governance_dir, 'approval_ledger.jsonl')
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            
        entry = json.loads(lines[0])
        entry['action'] = 'TAMPERED_ACTION'
        
        with open(ledger_path, 'w') as f:
            f.write(json.dumps(entry) + '\n')
            
        # Verify failure
        with self.assertRaises(ValueError) as cm:
            approval_ledger.verify_ledger()
        self.assertIn("Integrity hash mismatch", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
