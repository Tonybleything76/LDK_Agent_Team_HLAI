import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add project root to sys.path so we can import utils
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.worktree_guard import enforce_preflight, enforce_postflight, get_tracked_dirty_files

class TestWorktreeGuard(unittest.TestCase):
    def setUp(self):
        self.ledger_mock = MagicMock()
        self.run_id = "test_run_id"

    def test_get_tracked_dirty_files_clean(self):
        # Empty output
        self.assertEqual(get_tracked_dirty_files(""), [])
        # Untracked files only
        self.assertEqual(get_tracked_dirty_files("?? file1.txt\n?? folder/"), [])

    def test_get_tracked_dirty_files_dirty(self):
        status = "M  file1.py\n A file2.txt\n?? untracked.txt"
        dirty = get_tracked_dirty_files(status)
        self.assertIn("file1.py", dirty)
        self.assertIn("file2.txt", dirty)
        # Should not include untracked
        self.assertNotIn("untracked.txt", dirty)
        self.assertEqual(len(dirty), 2)

    def test_preflight_clean(self):
        # Clean status -> passed event
        enforce_preflight(
            allow_dirty=False,
            profile="dev",
            ledger_writer=self.ledger_mock,
            run_id=self.run_id,
            status_provider=lambda: ""
        )
        self.ledger_mock.assert_called_once()
        event = self.ledger_mock.call_args[0][0]
        self.assertEqual(event["event_type"], "preflight_passed")

    def test_preflight_dirty_disallowed(self):
        # Dirty status, allow=False -> Raises, failed event
        with self.assertRaises(RuntimeError):
            enforce_preflight(
                allow_dirty=False,
                profile="dev",
                ledger_writer=self.ledger_mock,
                run_id=self.run_id,
                status_provider=lambda: "M  file.py"
            )
        self.ledger_mock.assert_called_once()
        event = self.ledger_mock.call_args[0][0]
        self.assertEqual(event["event_type"], "preflight_failed")
        self.assertEqual(event["dirty_files"], ["file.py"])

    def test_preflight_dirty_allowed_dev(self):
        # Dirty status, allow=True, profile=dev -> Passed w/ warning
        enforce_preflight(
            allow_dirty=True,
            profile="dev",
            ledger_writer=self.ledger_mock,
            run_id=self.run_id,
            status_provider=lambda: "M  file.py"
        )
        self.ledger_mock.assert_called_once()
        event = self.ledger_mock.call_args[0][0]
        self.assertEqual(event["event_type"], "preflight_passed")
        self.assertIn("warning", event)

    def test_preflight_dirty_allowed_non_dev(self):
        # Dirty, allow=True, profile=prod -> Raises (guardrails), failed
        with self.assertRaises(RuntimeError):
            enforce_preflight(
                allow_dirty=True,
                profile="prod",
                ledger_writer=self.ledger_mock,
                run_id=self.run_id,
                status_provider=lambda: "M  file.py"
            )
        event = self.ledger_mock.call_args[0][0]
        self.assertEqual(event["event_type"], "preflight_failed")

    def test_postflight_drift(self):
        # Dirty -> Failed Postflight
        with self.assertRaises(RuntimeError):
            enforce_postflight(
                allow_dirty=False,
                profile="ci",
                ledger_writer=self.ledger_mock,
                run_id=self.run_id,
                status_provider=lambda: "M  file.py"
            )
        event = self.ledger_mock.call_args[0][0]
        self.assertEqual(event["event_type"], "postflight_failed")

if __name__ == "__main__":
    unittest.main()
