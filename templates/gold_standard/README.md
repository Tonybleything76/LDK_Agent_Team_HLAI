# Gold Standard Pilot Templates

## Purpose
These templates represent the "gold standard" for input documentation used in pilot course runs. They are designed to ensure maximum content quality, minimize downstream open questions, and provide a deterministic structure for stable pipeline execution.

## How to Use
1. Create a new pilot input folder:
   ```bash
   python3 scripts/pilot_inputs.py <pilot_name>
   ```
2. Copy these templates into the newly created folder:
   - `templates/gold_standard/business_brief_template.md` -> `inputs/<pilot_name>/business_brief.md`
   - `templates/gold_standard/sme_notes_template.md` -> `inputs/<pilot_name>/sme_notes.md`
3. Fill out the content in the destination files.

> [!IMPORTANT]
> **Filenames must not be changed in the input folders.** The orchestrator expects exactly `business_brief.md` and `sme_notes.md`.

## Quality Checklist
To ensure stable pilot runs and reduce ambiguity, ensure your inputs meet the following criteria:
- [ ] **Measurable Goals**: Define clear success thresholds and metrics.
- [ ] **Scope Boundaries**: Explicitly state what is out of scope (non-goals).
- [ ] **Required Constraints**: Specify audience, modality, length, and any compliance constraints.
- [ ] **Workflow Examples**: Include at least 2 detailed workflow examples.
- [ ] **Explicit Unknowns**: Use a dedicated "Unknowns" section with "assume X unless confirmed" patterns.

## Governance
These templates are the **Gold Standard**. To protect pilot run determinism, any changes to these templates must be made via **Pull Request (PR)** only.
