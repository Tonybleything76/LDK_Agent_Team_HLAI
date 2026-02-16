#!/usr/bin/env python3
"""
Pilot Inputs Helper - Create a new _inputs_* folder from templates.
"""

import sys
import argparse
from pathlib import Path
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BUSINESS_BRIEF_TEMPLATE = """# Business Brief (Template)

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

SME_NOTES_TEMPLATE = """# Subject Matter Expert (SME) Notes (Template)

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

def main():
    parser = argparse.ArgumentParser(
        description="Create a new _inputs_* folder from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "name",
        help="Name for the new input folder (will be prefixed with _inputs_)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing folder if it exists"
    )
    
    args = parser.parse_args()
    
    folder_name = args.name
    if not folder_name.startswith("_inputs_"):
        folder_name = f"_inputs_{folder_name}"
        
    target_dir = PROJECT_ROOT / folder_name
    
    print("=" * 60)
    print(f"🚀 Pilot Inputs Helper")
    print("=" * 60)
    
    if target_dir.exists() and not args.force:
        print(f"❌ Error: Folder {folder_name} already exists.")
        print(f"   Use --force to overwrite or choose a different name.")
        sys.exit(1)
        
    if target_dir.exists() and args.force:
        print(f"⚠️  Overwriting existing folder: {folder_name}")
        shutil.rmtree(target_dir)
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create template files
    (target_dir / "business_brief.md").write_text(BUSINESS_BRIEF_TEMPLATE)
    (target_dir / "sme_notes.md").write_text(SME_NOTES_TEMPLATE)
    
    print(f"✅ Created new input folder: {folder_name}")
    print(f"   Location: {target_dir}")
    print(f"   Files created:")
    print(f"     - business_brief.md")
    print(f"     - sme_notes.md")
    print()
    print(f"Next steps:")
    print(f"  1. Edit the files in {folder_name}/")
    print(f"  2. Run the pipeline with:")
    print(f"     python3 scripts/run_pipeline.py --inputs-dir {folder_name} --dry_run")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
