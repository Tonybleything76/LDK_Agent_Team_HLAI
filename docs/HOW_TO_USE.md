# LD Course Factory ADK — Team How-To Guide

A practical guide for course designers, L&D leads, and developers using the agent pipeline to build courses.

---

## What This System Does

You provide two input files. The system runs them through 10 AI agents in sequence and produces a complete course package — strategy, learner research, curriculum, lesson plans, assessments, storyboards, media specs, QA report, change management plan, and an asset catalog.

**You do not need to touch any code to run a course.**

---

## Before You Start (One-Time Setup)

### 1. Install Python dependencies

```bash
cd /path/to/ld-course-factory-adk
python3 -m venv .venv
source .venv/bin/activate
pip install openai
```

### 2. Set up your API keys

```bash
cp .env.example .env
```

Open `.env` and paste in your real keys:

```bash
export OPENAI_API_KEY=sk-proj-...
export PERPLEXITY_API_KEY=pplx-...
export ANTHROPIC_API_KEY=sk-ant-...   # Only needed if using Claude CLI mode
```

Then load them into your shell:

```bash
source .env
```

> Keys are never committed to git. Never share `.env` — only share `.env.example`.

---

## Running a Course

### Step 1 — Write your inputs

Edit the two files in the `inputs/` folder:

**`inputs/business_brief.md`**
Answer these questions:
- What business problem does this course solve?
- Who are the learners? What's their role / experience level?
- What should they be able to DO after completing the course?
- What's the delivery format (self-paced, ILT, blended)?
- Any constraints (length, tools, compliance requirements)?

**`inputs/sme_notes.md`**
Paste in your subject matter expert content:
- Key concepts, frameworks, terminology
- Real examples or scenarios from the workplace
- Common mistakes or misconceptions learners make
- Any existing materials (policies, process docs, talking points)

The richer these files, the better the output.

---

### Step 2 — Run the pipeline

```bash
source .env
.venv/bin/python scripts/run_pipeline.py
```

The system will show you a **Run Plan** before starting — review it and confirm.

Each agent step prints as it runs:
```
▶ Running Step 1: strategy_lead_agent
▶ Running Step 2: learner_research_agent
...
```

**Approval gates** pause at steps 3, 6, and 9. Type `APPROVE` to continue or anything else to stop.

---

### Step 3 — Review outputs

Outputs land in a timestamped folder:

```
outputs/20250310_143022/
├── 01_strategy_lead_agent.md
├── 02_learner_research_agent.md
├── 03_learning_architect_agent.md
├── 04_instructional_designer_agent.md
├── 05_assessment_designer_agent.md
├── 06_storyboard_agent.md
├── 07_media_producer_agent.md
├── 08_qa_agent.md
├── 09_change_management_agent.md
├── 10_operations_librarian_agent.md
├── 99_final_state.json
└── run_manifest.json
```

Each `.md` file is a deliverable you can review, edit, and hand off.

---

## Provider Modes

By default the pipeline uses OpenAI. You can switch providers:

| Mode | When to use | Command |
|------|-------------|---------|
| `openai` | Standard production run | `source .env && .venv/bin/python scripts/run_pipeline.py` |
| `dry_run` | Test the pipeline without API calls (no cost) | `PROVIDER=dry_run .venv/bin/python scripts/run_pipeline.py` |
| `manual` | Paste your own JSON responses | `PROVIDER=manual .venv/bin/python scripts/run_pipeline.py` |
| `perplexity` | Override all agents to Perplexity | `PROVIDER=perplexity .venv/bin/python scripts/run_pipeline.py` |

**Always test with `dry_run` first** when setting up a new environment.

---

## Common Options

### Skip approval gates (automated runs)

```bash
AUTO_APPROVE=true .venv/bin/python scripts/run_pipeline.py
```

### Use a more powerful model

```bash
OPENAI_MODEL=gpt-4o .venv/bin/python scripts/run_pipeline.py
```

### Stop after a specific step (preview mode)

Edit `run_pipeline.py` or pass `max_step` programmatically. Useful for reviewing the strategy before committing to the full run.

---

## Resuming an Interrupted Run

If a run fails or you stopped it mid-way, resume from the last checkpoint:

```bash
.venv/bin/python scripts/resume_run.py outputs/20250310_143022/
```

The pipeline picks up from the last completed step.

---

## Pre-flight Check

Before a production run, verify your environment is ready:

```bash
.venv/bin/python scripts/preflight_check.py
```

Checks: API keys set, input files non-empty, config valid, provider reachable.

---

## What Each Agent Produces

| Step | Agent | Output |
|------|-------|--------|
| 1 | **Strategy Lead** | Course title, summary, business goal alignment, module list |
| 2 | **Learner Research** | Learner personas, pain points, workplace context (uses Perplexity for live research) |
| 3 | **Learning Architect** | Full curriculum — 6 modules with objectives, key concepts, activities, assessments ← *Gate* |
| 4 | **Instructional Designer** | Detailed lesson plans per module |
| 5 | **Assessment Designer** | Question bank aligned to every learning objective |
| 6 | **Storyboard Agent** | Visual and interaction storyboards per module ← *Gate* |
| 7 | **Media Producer** | Media asset specs (images, video, animation requirements) |
| 8 | **QA Agent** | Quality review with severity ratings (CRITICAL / BLOCKER / MAJOR / MINOR) |
| 9 | **Change Management** | Rollout plan, stakeholder communication, adoption strategy ← *Gate* |
| 10 | **Operations Librarian** | Asset catalog, metadata registry, LMS-ready index |

---

## Approval Gates

Gates pause the pipeline at steps 3, 6, and 9.

At each gate you'll see:
```
⛔ APPROVAL GATE
Step 3: learning_architect_agent
Type APPROVE to continue, anything else to stop:
```

**Use gates to:**
- Review the curriculum before content is built (Gate 3)
- Check storyboards before media specs are written (Gate 6)
- Review QA findings before change management planning (Gate 9)

**Risk gates** trigger automatically if:
- An agent returns 8+ high-severity open questions
- The QA agent flags a CRITICAL or BLOCKER issue

Risk gates display a `⚠️ RISK GATE` warning with the reason before prompting.

---

## Interpreting Open Questions

Each agent outputs `open_questions` — things it flagged as needing human review. They use severity prefixes:

| Prefix | Meaning | Action Required |
|--------|---------|-----------------|
| `CRITICAL:` | Blocks course launch | Must resolve before proceeding |
| `BLOCKER:` | Blocks this deliverable | Must resolve before sign-off |
| `MAJOR:` | Significant quality risk | Should resolve before handoff |
| `MINOR:` | Small improvement suggestion | Address if time allows |

These appear in the output `.md` files. The QA agent (Step 8) consolidates them.

---

## After the Run

### Export deliverables

Package outputs for client or stakeholder handoff:

```bash
.venv/bin/python scripts/bundle_export.py outputs/20250310_143022/
```

Creates a zip in `exports/` with all deliverables and the audit summary.

### Run QA only (on existing output)

If you want to re-run just the QA agent on a completed run:

```bash
.venv/bin/python scripts/run_quality_review.py outputs/20250310_143022/
```

---

## Governance and Audit Trail

Every run creates an audit trail automatically:

- **`outputs/<run_id>/run_manifest.json`** — config hash, inputs hash, provider routing, approval events
- **`outputs/<run_id>/audit_summary.json`** — human-readable summary of all approval events
- **`governance/run_ledger.jsonl`** — append-only log of every approval, gate, and failure event

These are required for client sign-off and compliance reviews.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENAI_API_KEY not set` | Run `source .env` before running the pipeline |
| `Missing input file: inputs/business_brief.md` | Create the file with your course brief |
| Pipeline fails at Step N with parse error | Re-run from checkpoint: `resume_run.py outputs/<run_id>/` |
| Output too short or contains placeholders | Input files are too sparse — add more detail to `sme_notes.md` |
| Risk gate triggered unexpectedly | Review `open_questions` in the previous step's output `.md` file |
| `python -m adk` does nothing | Use `.venv/bin/python scripts/run_pipeline.py` instead |

---

## Quick Reference Card

```bash
# Standard run
source .env && .venv/bin/python scripts/run_pipeline.py

# Test run (no API cost)
PROVIDER=dry_run .venv/bin/python scripts/run_pipeline.py

# Skip gates (CI / automated)
AUTO_APPROVE=true .venv/bin/python scripts/run_pipeline.py

# Resume interrupted run
.venv/bin/python scripts/resume_run.py outputs/<run_id>/

# Pre-flight check
.venv/bin/python scripts/preflight_check.py

# Export deliverables
.venv/bin/python scripts/bundle_export.py outputs/<run_id>/

# QA review only
.venv/bin/python scripts/run_quality_review.py outputs/<run_id>/
```
