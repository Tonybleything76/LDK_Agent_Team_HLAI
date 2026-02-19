import argparse
import sys
import shutil
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Create new course inputs from a template")
    parser.add_argument("course_slug", help="Slug for the course (e.g., copilot_pr_firm_v2)")
    parser.add_argument("--template", default="gold_standard", help="Template name to use")
    parser.add_argument("--force", action="store_true", help="Overwrite existing directory if present")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    template_dir = project_root / "templates" / args.template
    target_dir = project_root / f"_inputs_{args.course_slug}"

    if not template_dir.exists():
        print(f"❌ Template directory not found: {template_dir}")
        sys.exit(1)

    if target_dir.exists():
        if not args.force:
            print(f"❌ Target directory already exists: {target_dir}")
            print("   Use --force to overwrite it.")
            sys.exit(1)
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True)

    src_brief = template_dir / "business_brief_template.md"
    src_notes = template_dir / "sme_notes_template.md"
    
    dest_brief = target_dir / "business_brief.md"
    dest_notes = target_dir / "sme_notes.md"

    if not src_brief.exists() or not src_notes.exists():
        print("❌ Core template files missing in template directory.")
        sys.exit(1)

    shutil.copy2(src_brief, dest_brief)
    shutil.copy2(src_notes, dest_notes)

    print(f"✅ Successfully created new inputs in: {target_dir.name}/")
    print("\nNext steps:")
    print(f"  1) Edit the two files in {target_dir.name}/")
    print(f"  2) Run: python3 scripts/run_pipeline.py --dry_run --governance_profile content_only --inputs-dir {target_dir.name}")
    print(f"  3) Run: python3 scripts/run_pipeline.py --mode openai --governance_profile content_only --inputs-dir {target_dir.name}")

if __name__ == "__main__":
    main()
