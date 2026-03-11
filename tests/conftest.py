"""
Pytest configuration for the LD Course Factory test suite.

Tests that import scripts moved to scripts/archive/ are collected but skipped
with a clear message rather than crashing collection for the whole suite.
"""

collect_ignore = [
    # These tests import scripts that have been archived and are no longer on PYTHONPATH.
    # They are preserved for reference but excluded from active CI runs.
    "test_content_consistency_structure.py",
    "test_objective_count_and_storyboard_alignment.py",
    "test_offline_integration.py",
    "test_pilot_acceptance_objectives_and_storyboard.py",
    "test_enforce_promotion_guard.py",
    "test_hybrid_module_count.py",
    "test_input_quality.py",
]
