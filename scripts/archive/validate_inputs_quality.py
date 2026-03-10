import argparse
import sys
import re
from pathlib import Path

def check_headers_present(content, required_headers):
    missing = []
    content_lower = content.lower()
    for header in required_headers:
        if header.lower() not in content_lower:
            missing.append(header)
    return missing

def extract_section(text, header_keyword):
    pattern = r'(?i)\n#+[^\n]*' + re.escape(header_keyword) + r'[^\n]*\n(.*?)(?=\n#+ |\Z)'
    padded_text = "\n" + text
    match = re.search(pattern, padded_text, re.DOTALL)
    if match:
        return match.group(1)
    return ""

def validate_quality(inputs_dir: Path, required_keyword="Copilot"):
    errors = []
    brief_path = inputs_dir / "business_brief.md"
    notes_path = inputs_dir / "sme_notes.md"

    if not brief_path.exists() or not notes_path.exists():
        return False, [f"Missing core input files in {inputs_dir}"]

    with open(brief_path, "r", encoding="utf-8") as f:
        brief_content = f.read()
    with open(notes_path, "r", encoding="utf-8") as f:
        notes_content = f.read()

    # BRIEF
    brief_headers = [
        "Business Context",
        "Organizational Goals",
        "Target Audience",
        "Learning Objectives",
        "Success Metrics",
        "Delivery Modality",
        "Strategic Framing"
    ]
    missing_brief_headers = check_headers_present(brief_content, brief_headers)
    if missing_brief_headers:
        errors.append(f"Business Brief missing headers: {', '.join(missing_brief_headers)}")

    goals_sec = extract_section(brief_content, "Organizational Goals")
    if len(re.findall(r'^\s*[-*]\s+', goals_sec, re.MULTILINE)) < 3:
        errors.append("Business Brief must include at least 3 explicit goals (bullets) under Organizational Goals.")

    metrics_sec = extract_section(brief_content, "Success Metrics")
    metric_bullets = re.findall(r'^\s*[-*]\s+(.*)', metrics_sec, re.MULTILINE)
    valid_metrics = 0
    for m in metric_bullets:
        if bool(re.search(r'\d|%|percent|daily|weekly|monthly|annually|quarterly', m, re.IGNORECASE)):
            valid_metrics += 1
    if valid_metrics < 3:
        errors.append("Business Brief must include at least 3 measurable success metrics (number, %, timeframe, frequency).")

    objs_sec = extract_section(brief_content, "Learning Objectives")
    if len(re.findall(r'^\s*[-*]\s+', objs_sec, re.MULTILINE)) < 4:
        errors.append("Business Brief must include a learning objectives list with 4+ items.")

    if required_keyword.lower() not in brief_content.lower():
        errors.append(f"Business Brief must contain named tool context ('{required_keyword}').")

    # SME NOTES
    notes_headers = [
        "Core Instructional Philosophy",
        "Essential Concept Coverage",
        "Gotchas",
        "Responsible AI Behavior Model",
        "Systems & Policy Alignment",
        "Tone & Human Experience",
        "Non-Negotiable Learning Outcomes"
    ]
    missing_notes_headers = check_headers_present(notes_content, notes_headers)
    if missing_notes_headers:
        errors.append(f"SME Notes missing headers: {', '.join(missing_notes_headers)}")

    nl = notes_content.lower()
    if "belief" not in nl:
        errors.append("SME Notes must include 'Belief' language.")
    if "behavior" not in nl:
        errors.append("SME Notes must include 'Behavior' language.")
    if "systems" not in nl and "policies" not in nl:
        errors.append("SME Notes must include 'Systems' or 'Policies' language.")

    if errors:
        return False, errors
    return True, []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs-dir", required=True)
    parser.add_argument("--required-keyword", default="Copilot")
    args = parser.parse_args()

    inputs_dir = Path(args.inputs_dir)
    valid, errors = validate_quality(inputs_dir, args.required_keyword)

    if not valid:
        print("❌ INPUT QUALITY VALIDATION FAILED")
        for e in errors:
            print("  - " + e)
        print("\nFix guidance: Please review the errors above and ensure your input documents are specific and complete. Use bullet points for lists and ensure metrics are measurable.")
        sys.exit(1)
    
    print("✅ Input quality validation passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
