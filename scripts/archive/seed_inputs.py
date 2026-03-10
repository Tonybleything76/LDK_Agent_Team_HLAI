#!/usr/bin/env python3
"""
Seed Inputs Helper - Create template input files for the orchestrator.

This script creates template files for business_brief.md and sme_notes.md
to help users get started quickly. It includes safe overwrite protection.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

INPUTS_DIR = PROJECT_ROOT / "inputs"

BUSINESS_BRIEF_TEMPLATE = """# Business Brief

## Business Context

*Describe the business context, organizational goals, and strategic priorities.*

- What is the business need or problem this course addresses?
- What are the organizational goals?
- What is the expected business impact?

## Target Audience

*Define who will take this course.*

- Job roles and responsibilities
- Current skill levels and knowledge gaps
- Learning preferences and constraints
- Estimated number of learners

## Learning Goals

*What should learners be able to do after completing this course?*

1. [Primary learning objective]
2. [Secondary learning objective]
3. [Additional objectives...]

## Constraints and Requirements

*Any constraints or requirements to consider.*

- **Timeline**: When does this need to be delivered?
- **Budget**: Any budget constraints?
- **Technology**: What platforms or tools must be used?
- **Compliance**: Any regulatory or compliance requirements?
- **Accessibility**: Any specific accessibility needs?

## Success Metrics

*How will we measure the success of this course?*

- Completion rates
- Assessment scores
- Behavior change metrics
- Business impact metrics

---

*Replace this template content with your actual business brief.*
"""

SME_NOTES_TEMPLATE = """# Subject Matter Expert (SME) Notes

## Subject Matter Expertise

*Provide domain expertise and subject matter knowledge.*

- What are the core concepts learners must understand?
- What are the key skills they must develop?
- What is the current state of knowledge in this field?

## Key Concepts and Topics

*List the main topics and concepts to cover.*

1. **[Topic 1]**: Brief description
2. **[Topic 2]**: Brief description
3. **[Topic 3]**: Brief description

## Common Misconceptions

*What do learners typically get wrong or misunderstand?*

- [Misconception 1]: Why it's wrong and what's correct
- [Misconception 2]: Why it's wrong and what's correct

## Real-World Applications

*How is this knowledge applied in practice?*

- Use cases and scenarios
- Common challenges and how to overcome them
- Best practices and tips

## Resources and References

*Helpful resources for course development.*

- Industry standards and frameworks
- Research papers or articles
- Example materials or case studies
- Tools and technologies

## Prerequisites

*What should learners know before starting this course?*

- Required prior knowledge
- Recommended background
- Assumed skill levels

---

*Replace this template content with your actual SME notes.*
"""


def create_template_file(filepath: Path, template: str, force: bool = False) -> bool:
    """
    Create a template file if it doesn't exist or is empty.
    
    Args:
        filepath: Path to the file to create
        template: Template content to write
        force: If True, overwrite even if file exists and is non-empty
        
    Returns:
        True if file was created/updated, False if skipped
    """
    # Check if file exists and is non-empty
    if filepath.exists():
        existing_size = filepath.stat().st_size
        
        if existing_size > 10 and not force:
            print(f"⏭️  Skipped {filepath.name} (already exists, {existing_size} bytes)")
            print(f"   Use --force to overwrite")
            return False
    
    # Create parent directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write template
    filepath.write_text(template)
    
    action = "Overwrote" if filepath.exists() and force else "Created"
    print(f"✅ {action} {filepath.name} (template, {len(template)} bytes)")
    print(f"   Location: {filepath}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create template input files for the orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create templates (safe, won't overwrite existing files)
  python3 scripts/seed_inputs.py
  
  # Force overwrite existing files
  python3 scripts/seed_inputs.py --force

Files created:
  - inputs/business_brief.md
  - inputs/sme_notes.md
        """
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files even if they are non-empty"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Seed Inputs Helper")
    print("=" * 60)
    print()
    
    # Create templates
    created_count = 0
    
    business_brief_path = INPUTS_DIR / "business_brief.md"
    if create_template_file(business_brief_path, BUSINESS_BRIEF_TEMPLATE, args.force):
        created_count += 1
    
    print()
    
    sme_notes_path = INPUTS_DIR / "sme_notes.md"
    if create_template_file(sme_notes_path, SME_NOTES_TEMPLATE, args.force):
        created_count += 1
    
    print()
    print("=" * 60)
    
    if created_count > 0:
        print(f"\n✅ Created {created_count} template file(s)")
        print(f"\nNext steps:")
        print(f"  1. Edit the template files with your content:")
        print(f"     - {business_brief_path}")
        print(f"     - {sme_notes_path}")
        print(f"  2. Run a dry run to test: python3 scripts/run_pipeline.py --dry_run")
        print(f"  3. Run for real: python3 scripts/run_pipeline.py --mode openai")
    else:
        print(f"\n⏭️  No files created (all files already exist)")
        print(f"   Use --force to overwrite existing files")
    
    print()


if __name__ == "__main__":
    main()
