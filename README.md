# LD Course Factory ADK

**Version:** 1.0.0-pilot

An automated Learning & Development course creation system using a 10-step multi-agent pipeline. Transforms a business brief and SME notes into a full course deliverable — including strategy, learner research, curriculum, storyboards, assessments, media specs, QA review, and operations catalog.

---

## Setup

### 1. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai
```

### 2. API keys

```bash
cp .env.example .env
# Edit .env and add your real API keys
source .env
```

Required keys:
- `OPENAI_API_KEY` — for all OpenAI-backed agents
- `PERPLEXITY_API_KEY` — for the learner research agent
- `ANTHROPIC_API_KEY` — for claude_cli provider (optional)

### 3. Course inputs

Edit the two input files before running:

```
inputs/business_brief.md   # What the course needs to achieve
inputs/sme_notes.md        # Subject matter expert content
```

---

## Running the Pipeline

### Full run (recommended)

```bash
source .env
.venv/bin/python scripts/run_pipeline.py
```

### Dry run (no API calls, for testing)

```bash
PROVIDER=dry_run .venv/bin/python scripts/run_pipeline.py
```

### Skip approval gates

```bash
AUTO_APPROVE=true .venv/bin/python scripts/run_pipeline.py
```

### Resume an interrupted run

```bash
.venv/bin/python scripts/resume_run.py outputs/<run_id>/
```

### Package entry point (equivalent to run_pipeline)

```bash
.venv/bin/python -m adk
```

---

## Pipeline Overview

10 agents run sequentially. Each receives pruned system state and returns structured output merged into the master state.

```
1.  strategy_lead          → Course title, summary, target audience, modules
2.  learner_research       → Learner personas, pain points (Perplexity)
3.  learning_architect     → Curriculum structure, objectives  ← GATE
4.  instructional_designer → Lesson plans, module designs
5.  assessment_designer    → Question bank aligned to objectives
6.  storyboard             → Visual/interaction storyboards      ← GATE
7.  media_producer         → Media asset specifications
8.  qa                     → QA findings with severity ratings
9.  change_management      → Rollout and stakeholder plan        ← GATE
10. operations_librarian   → Asset catalog and registry
```

Gates at steps 3, 6, 9 require approval before proceeding (auto-approved by default via `AUTO_APPROVE=true`).

---

## Outputs

Each run creates a timestamped directory:

```
outputs/<YYYYMMDD_HHMMSS>/
├── 01_strategy_lead_agent.md          # Deliverable markdown
├── 01_strategy_lead_agent_state.json  # Full parsed output
├── ...
├── 99_final_state.json                # Master state after all steps
├── run_manifest.json                  # Run metadata and hashes
├── audit_summary.json                 # Approval/event summary
└── checkpoints/                       # Per-step state snapshots
```

---

## Provider Options

Set via `PROVIDER` environment variable or per-agent in `config/run_config.json`.

| Provider | Description |
|----------|-------------|
| `openai` | OpenAI Chat Completions (default) |
| `perplexity` | Perplexity API (used by learner_research) |
| `claude_cli` | Local Claude CLI binary |
| `dry_run` | Stub provider — no API calls, for testing |
| `manual` | STDIN/STDOUT — paste JSON responses manually |

Model and temperature override:
```bash
OPENAI_MODEL=gpt-4o OPENAI_TEMPERATURE=0.3
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/run_pipeline.py` | **Primary entry point** — full pipeline run |
| `scripts/resume_run.py` | Resume from a checkpoint |
| `scripts/run_pilot.py` | Pilot validation mode |
| `scripts/run_quality_review.py` | Run QA agent only on existing state |
| `scripts/preflight_check.py` | Validate environment before running |
| `scripts/bundle_export.py` | Package deliverables for handoff |

Archived scripts (CI, verification, one-offs): `scripts/archive/`

---

## Configuration

`config/run_config.json` controls the pipeline:
- Agent sequence and provider assignments
- Approval gate strategy (`per_phase` or `per_agent`)
- Phase gate positions (default: steps 3, 6, 9)
- Risk gate escalation thresholds
- Output validation rules (min length, placeholder detection)

---

## Governance

- **Approval ledger:** `governance/run_ledger.jsonl` — append-only event log
- **Locked decisions:** `governance/locked_decisions.md`
- **Approvers:** `governance/approvers.json`

---

## Project Structure

```
ld-course-factory-adk/
├── adk/                  # Package entry point (python -m adk)
├── orchestrator/         # Core pipeline engine
│   ├── root_agent.py     # Main orchestration loop
│   ├── validation.py     # Output contract enforcement
│   ├── providers/        # LLM provider abstraction (OpenAI, Perplexity, etc.)
│   └── quality/          # QA scoring and validation
├── cli/                  # CLI module (adk.py entry point)
├── schemas/              # JSON state contracts
├── prompts/              # Agent prompt templates (one dir per agent)
├── config/               # run_config.json
├── inputs/               # business_brief.md, sme_notes.md
├── outputs/              # Generated run outputs (gitignored)
├── scripts/              # Runnable scripts
├── tests/                # Test suite
├── governance/           # Approval ledger and policy docs
└── archive/              # Historical patches, evidence, stale files
```
