#!/usr/bin/env python3
"""
Validate Course Architecture
============================

CLI tool to validate a course architecture JSON file against the v0.6 schema.

Usage:
    python3 scripts/validate_course_architecture.py --path <path_to_json>
"""

import argparse
import sys
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import orchestrator modules
try:
    from orchestrator.course_architecture import load_course_architecture, validate_course_architecture
except ImportError:
    print("❌ Error: Could not import orchestrator modules. Run from project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    parser = argparse.ArgumentParser(description="Validate Course Architecture JSON")
    parser.add_argument("--path", required=True, help="Path to the course_architecture.json file")
    args = parser.parse_args()
    
    file_path = Path(args.path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
        
    print(f"🔍 Validating: {file_path}")
    
    try:
        # Load
        data = load_course_architecture(file_path)
        print("✅ JSON loaded successfully")
        
        # Validate
        validate_course_architecture(data)
        print("✅ Schema validation passed")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED")
        print(f"   {str(e)}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
