#!/usr/bin/env python3
"""
Pilot Acceptance Harness

One-command pilot acceptance: bootstraps inputs from gold-standard templates,
runs the content-only consistency harness N times, evaluates quality gates,
and packages all evidence into a ZIP.

Usage:
    python3 scripts/run_pilot_acceptance.py --course-slug <slug> [options]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "gold_standard"
EXPORTS_DIR = PROJECT_ROOT / "exports"


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def bootstrap_inputs(inputs_dir: Path) -> bool:
    """
    Creates inputs_dir and copies gold-standard templates into it.
    Returns True if templates were copied (i.e., the directory was freshly created).
    """
    if inputs_dir.exists():
        return False  # directory already existed, skip copy

    inputs_dir.mkdir(parents=True)
    log(f"Created inputs directory: {inputs_dir}")

    brief_src = TEMPLATES_DIR / "business_brief_template.md"
    notes_src = TEMPLATES_DIR / "sme_notes_template.md"

    if not brief_src.exists() or not notes_src.exists():
        raise FileNotFoundError(
            f"Gold-standard templates not found in {TEMPLATES_DIR}. "
            "Expected business_brief_template.md and sme_notes_template.md."
        )

    shutil.copy2(brief_src, inputs_dir / "business_brief.md")
    shutil.copy2(notes_src, inputs_dir / "sme_notes.md")
    log("Copied gold-standard templates to inputs directory.")
    return True


def run_content_consistency(
    inputs_dir: Path,
    provider: str,
    model: str,
    runs: int,
    auto_approve: bool,
    governance_profile: str = "content_only",
) -> None:
    """Runs the content consistency harness as a subprocess."""
    cmd = [
        "python3",
        "scripts/run_content_consistency.py",
        "--inputs-dir",
        str(inputs_dir),
        "--provider",
        provider,
        "--model",
        model,
        "--runs",
        str(runs),
        "--governance_profile",
        governance_profile,
    ]
    if auto_approve:
        cmd.append("--auto-approve")

    log(f"Running content consistency harness (provider={provider}, runs={runs})...")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Content consistency harness failed with exit code {result.returncode}"
        )


def load_report() -> dict:
    """Loads and returns the content consistency report JSON."""
    report_path = EXPORTS_DIR / "content_consistency_report.json"
    if not report_path.exists():
        raise FileNotFoundError(
            f"Expected report not found: {report_path}. "
            "Did the content consistency harness run successfully?"
        )
    with open(report_path) as f:
        return json.load(f)


def evaluate_gates(
    report: dict,
    course_slug: str,
    min_structure_stability: int,
    require_quality: bool,
    min_objectives: int,
    expected_modules: int,
    require_empty_diffs: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """
    Evaluates pass/fail gates against the report.
    Returns (passed: bool, failures: list[str], warnings: list[str]).
    """
    failures = []
    warnings = []

    # Gate 1: report must have required keys
    required_keys = [
        "overall_stability_score",
        "structure_stability_score",
        "objectives_per_run",
        "modules_per_run",
        "storyboard_per_run"
    ]
    for key in required_keys:
        if key not in report:
            print(f"ERROR: Report missing required key: '{key}'")
            sys.exit(1)

    # Gate 2: structure stability threshold
    struct_score = report.get("structure_stability_score", report.get("overall_stability_score", 0))
    if struct_score < min_structure_stability:
        failures.append(
            f"structure_stability_score {struct_score} < required {min_structure_stability}."
        )

    # Gate 3: Objectives Count (>= min_objectives for ALL runs)
    obj_counts = report["objectives_per_run"]
    if any(c < min_objectives for c in obj_counts):
        failures.append(
            f"objectives_count failed: {obj_counts} (min required: {min_objectives})."
        )

    # Gate 4: Module Count (== expected_modules for ALL runs)
    mod_counts = report["modules_per_run"]
    if any(c != expected_modules for c in mod_counts):
        failures.append(
            f"modules_count failed: {mod_counts} (expected: {expected_modules})."
        )

    # Gate 5: Storyboard Module Count (== expected_modules for ALL runs)
    sb_counts = report["storyboard_per_run"]
    if any(c != expected_modules for c in sb_counts):
        failures.append(
            f"storyboard_module_count failed: {sb_counts} (expected: {expected_modules})."
        )

    # Gate 6: Structure Diffs Summary
    diffs = report.get("structure_diffs_summary", [])
    if diffs:
        if require_empty_diffs:
            failures.append(f"structure_diffs detected: {len(diffs)} items.")
            for d in diffs:
                warnings.append(f"Structure drift: {d}")
        else:
            allowed_fields = {"key_concepts_count", "activities_count", "checks_count", "examples_count"}
            has_hard_diff = False
            for d in diffs:
                if isinstance(d, dict):
                    if d.get("field") not in allowed_fields:
                        has_hard_diff = True
                        failures.append(f"Unallowed structure drift: {d}")
                    else:
                        warnings.append(f"Allowed depth drift: {d}")
                else:
                    # fallback for string
                    warnings.append(f"Unstructured drift (treated as allowed depth drift): {d}")
                    
            if has_hard_diff:
                failures.append(f"structure_diffs detected unallowed items.")

    # Check for errors and schema validity
    if report.get("errors_detected", False):
        failures.append("errors_detected is true.")
    if report.get("qa_critical_detected", False):
        failures.append("qa_critical_detected is true.")
    
    # schema validity check
    runs_data = report.get("runs", [])
    for r in runs_data:
        sv = r.get("structure", {}).get("schema_validity", {})
        if sv and not all(sv.values()):
            failures.append("schema_validity < 100%.")
            
    # Soft warning for overall stability
    overall_score = report.get("overall_stability_score", 0)
    struct_score = report.get("structure_stability_score", overall_score)
    if overall_score < min_structure_stability and struct_score >= min_structure_stability:
        warnings.append(f"overall_stability_score {overall_score} is below threshold {min_structure_stability}.")

    # Gate 7: quality rubric (when required)
    if require_quality:
        # Check if "copilot" appears in course slug or brief content (heuristic)
        slug_lower = course_slug.lower()
        copilot_in_slug = "copilot" in slug_lower

        # Read rubric from first successful run
        runs_data = report.get("runs", [])
        successful_runs = [r for r in runs_data if r.get("status") == "success"]

        if successful_runs:
            first_rubric = successful_runs[0].get("quality_rubric", {})
            missing_flags = []
            if not first_rubric.get("belief_clarity_present"):
                missing_flags.append("Belief")
            if not first_rubric.get("behavior_clarity_present"):
                missing_flags.append("Behavior")
            if not first_rubric.get("systems_policies_present"):
                missing_flags.append("Systems")

            if missing_flags:
                failures.append(
                    f"Strategy rubric missing required flags: {', '.join(missing_flags)}."
                )

            if copilot_in_slug:
                copilot_ok = any(
                    r.get("quality_rubric", {}).get("copilot_coverage_score", 0) > 0
                    for r in successful_runs
                )
                if not copilot_ok:
                    failures.append("Copilot coverage missing but 'copilot' appears in course slug.")
        else:
            failures.append("No successful runs to evaluate quality rubric.")

    passed = len(failures) == 0
    return passed, failures, warnings


def build_summary_markdown(
    course_slug: str,
    report: dict,
    passed: bool,
    failures: list[str],
    warnings: list[str],
    min_structure_stability: int,
) -> str:
    """Generates the pilot_acceptance_summary.md content."""
    timestamp = datetime.now().isoformat()
    overall_score = report.get("overall_stability_score", "N/A")
    struct_score = report.get("structure_stability_score", overall_score)
    config = report.get("config", {})

    runs_data = report.get("runs", [])
    run_ids = [r.get("run_id", "UNKNOWN") for r in runs_data]

    status_emoji = "✅ PASS" if passed else "❌ FAIL"

    lines = [
        f"# Pilot Acceptance Summary — {course_slug}",
        "",
        f"**Generated**: {timestamp}",
        f"**Provider**: {config.get('provider', 'N/A')}",
        f"**Profile**: {config.get('profile', 'N/A')}",
        f"**Runs**: {config.get('runs', len(runs_data))}",
        "",
        "## Gate Results",
        "",
        "| Gate | Required | Actual | Result |",
        f"|---|---|---|---|",
        f"| Structure Stability | ≥ {min_structure_stability} | {struct_score} | {'✅' if isinstance(struct_score, (int, float)) and struct_score >= min_structure_stability else '❌'} |",
        f"| Objectives (ALL runs) | ≥ {report.get('min_objectives', 12)} | {report.get('objectives_per_run', [])} | {'✅' if all(c >= report.get('min_objectives', 12) for c in report.get('objectives_per_run', [])) else '❌'} |",
        f"| Modules (ALL runs) | == {report.get('expected_modules', 6)} | {report.get('modules_per_run', [])} | {'✅' if all(c == report.get('expected_modules', 6) for c in report.get('modules_per_run', [])) else '❌'} |",
        f"| Storyboards (ALL runs) | == {report.get('expected_modules', 6)} | {report.get('storyboard_per_run', [])} | {'✅' if all(c == report.get('expected_modules', 6) for c in report.get('storyboard_per_run', [])) else '❌'} |",
        f"| Overall Status | PASS | — | {status_emoji} |",
        "",
        "## Run IDs",
        "",
    ]
    for run_id in run_ids:
        lines.append(f"- `{run_id}`")

    if failures:
        lines += ["", "## Failures", ""]
        for f in failures:
            lines.append(f"- ❌ {f}")

    if warnings:
        lines += ["", "## Warnings", ""]
        for w in warnings:
            lines.append(f"- ⚠️ {w}")

    lines += ["", "Acceptance is spine-stable; depth drift is allowed unless --require-empty-diffs is set.", "", "---", f"*Pilot Acceptance Harness — {course_slug}*"]
    return "\n".join(lines)


def package_evidence(course_slug: str, summary_md: str) -> Path:
    """Packages the evidence into a ZIP file and returns its path."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXPORTS_DIR / f"pilot_acceptance_pack_{course_slug}.zip"

    report_path = EXPORTS_DIR / "content_consistency_report.json"
    consistency_pack = EXPORTS_DIR / "content_consistency_pack.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if report_path.exists():
            zf.write(report_path, arcname="content_consistency_report.json")

        if consistency_pack.exists():
            zf.write(consistency_pack, arcname="content_consistency_pack.zip")
        else:
            log("Warning: content_consistency_pack.zip not found; skipping.")

        zf.writestr("pilot_acceptance_summary.md", summary_md)

    log(f"Evidence pack created: {zip_path}")
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Pilot Acceptance Harness")
    parser.add_argument("--course-slug", required=True, help="Course slug (e.g. copilot_fundamentals_v1)")
    parser.add_argument("--inputs-dir", type=Path, default=None,
                        help="Inputs directory (default: _inputs_<course-slug>)")
    parser.add_argument("--provider", default="openai", help="LLM provider")
    parser.add_argument("--model", default="gpt-4o", help="Model name (for openai provider)")
    parser.add_argument("--runs", type=int, default=3, help="Number of consistency runs")
    parser.add_argument("--auto-approve", action="store_true",
                        help="Auto-approve phase gates (no interactive prompts)")
    parser.add_argument("--min-structure-stability", type=int, default=80,
                        help="Minimum structure_stability_score to pass (0-100)")
    parser.add_argument("--min-objectives", type=int, default=12,
                        help="Minimum objectives_count per run")
    parser.add_argument("--expected-modules", type=int, default=6,
                        help="Expected module count per run (curriculum and storyboard)")
    parser.add_argument("--require-quality", dest="require_quality", action="store_true", default=False,
                        help="Fail if strategy rubric flags are missing (opt-in; off by default)")
    parser.add_argument("--no-require-quality", dest="require_quality", action="store_false",
                        help="Disable quality rubric gate (no-op; default behaviour)")
    parser.add_argument("--require-empty-diffs", action="store_true", default=False,
                        help="Require perfectly empty structure_diffs_summary (strict behavior)")

    args = parser.parse_args()

    # Resolve inputs directory
    inputs_dir = args.inputs_dir or (PROJECT_ROOT / f"_inputs_{args.course_slug}")

    print("=" * 60)
    print("PILOT ACCEPTANCE HARNESS")
    print(f"  Course slug : {args.course_slug}")
    print(f"  Inputs dir  : {inputs_dir}")
    print(f"  Provider    : {args.provider}")
    print(f"  Model       : {args.model}")
    print(f"  Runs        : {args.runs}")
    print(f"  Auto-approve: {args.auto_approve}")
    print("=" * 60)

    # Step 1: Bootstrap inputs if needed
    try:
        templates_copied = bootstrap_inputs(inputs_dir)
    except FileNotFoundError as e:
        log(f"ERROR: {e}")
        sys.exit(1)

    if templates_copied:
        print()
        print("⚠️  TEMPLATES COPIED — please edit before running with real provider:")
        print(f"    {inputs_dir / 'business_brief.md'}  — fill in course context")
        print(f"    {inputs_dir / 'sme_notes.md'}       — fill in SME content & learning goals")
        print()
        if not args.auto_approve and args.provider != "dry_run":
            answer = input("Templates are unpopulated. Continue anyway? [y/N] ").strip().lower()
            if answer != "y":
                log("Aborted by user.")
                sys.exit(0)

    # Step 2: Run content consistency harness
    try:
        run_content_consistency(
            inputs_dir=inputs_dir,
            provider=args.provider,
            model=args.model,
            runs=args.runs,
            auto_approve=args.auto_approve,
        )
    except RuntimeError as e:
        log(f"ERROR: {e}")
        sys.exit(1)

    # Step 3: Load and evaluate report
    try:
        report = load_report()
        # Inject thresholds for summary generation
        report["min_objectives"] = args.min_objectives
        report["expected_modules"] = args.expected_modules
    except FileNotFoundError as e:
        log(f"ERROR: {e}")
        sys.exit(1)

    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug=args.course_slug,
        min_structure_stability=args.min_structure_stability,
        require_quality=args.require_quality,
        min_objectives=args.min_objectives,
        expected_modules=args.expected_modules,
        require_empty_diffs=args.require_empty_diffs,
    )

    # Step 4: Build summary and package evidence
    summary_md = build_summary_markdown(
        course_slug=args.course_slug,
        report=report,
        passed=passed,
        failures=failures,
        warnings=warnings,
        min_structure_stability=args.min_structure_stability,
    )

    zip_path = package_evidence(args.course_slug, summary_md)

    # Step 5: Final report
    print()
    print("=" * 60)
    if passed:
        print("✅  PILOT ACCEPTANCE: PASS")
    else:
        print("❌  PILOT ACCEPTANCE: FAIL")
        for f in failures:
            print(f"   • {f}")
    print(f"   Evidence pack: {zip_path.relative_to(PROJECT_ROOT)}")
    print("=" * 60)

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
