#!/usr/bin/env python3
"""
Test script for JSON extraction functionality.
Tests various LLM output patterns to ensure robust parsing.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.json_tools import extract_json_object, parse_json_object


def test_case(name: str, raw_text: str, should_succeed: bool = True):
    """Run a single test case."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Input:\n{raw_text[:200]}{'...' if len(raw_text) > 200 else ''}\n")
    
    try:
        result = parse_json_object(raw_text)
        if should_succeed:
            print(f"✅ PASS - Successfully parsed: {result}")
            return True
        else:
            print(f"❌ FAIL - Expected failure but succeeded: {result}")
            return False
    except Exception as e:
        if not should_succeed:
            print(f"✅ PASS - Failed as expected: {str(e)[:100]}")
            return True
        else:
            print(f"❌ FAIL - Unexpected error: {e}")
            return False


def main():
    """Run all test cases."""
    print("\n" + "="*60)
    print("JSON EXTRACTION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Pure JSON
    results.append(test_case(
        "Pure JSON",
        '{"deliverable_markdown": "test", "updated_state": {}, "open_questions": []}',
        should_succeed=True
    ))
    
    # Test 2: Fenced with language specifier
    results.append(test_case(
        "Fenced with 'json' language",
        '''```json
{
  "deliverable_markdown": "test content",
  "updated_state": {"key": "value"},
  "open_questions": ["question 1"]
}
```''',
        should_succeed=True
    ))
    
    # Test 3: Fenced without language specifier
    results.append(test_case(
        "Fenced without language",
        '''```
{
  "deliverable_markdown": "test",
  "updated_state": {},
  "open_questions": []
}
```''',
        should_succeed=True
    ))
    
    # Test 4: Leading commentary
    results.append(test_case(
        "Leading commentary",
        '''Here is the result you requested:

{"deliverable_markdown": "content here", "updated_state": {}, "open_questions": []}''',
        should_succeed=True
    ))
    
    # Test 5: Trailing commentary
    results.append(test_case(
        "Trailing commentary",
        '''{"deliverable_markdown": "test", "updated_state": {}, "open_questions": []}

I hope this helps! Let me know if you need anything else.''',
        should_succeed=True
    ))
    
    # Test 6: No JSON (should fail)
    results.append(test_case(
        "No JSON - Expected Failure",
        "This is just plain text with no JSON object at all.",
        should_succeed=False
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
