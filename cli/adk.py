"""
CLI entry point for the ld-course-factory-adk package.

Usage:
    python -m adk                  # Run full pipeline
    python -m adk --help           # Show help
    python scripts/run_pipeline.py # Direct script invocation (equivalent)
"""

import sys
import os

# Ensure project root is on path when invoked as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Primary CLI entry point — delegates to the run_pipeline script."""
    from scripts.run_pipeline import main as run_pipeline_main
    run_pipeline_main()
