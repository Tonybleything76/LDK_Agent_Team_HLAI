import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_pipeline import load_and_validate_config, apply_profile_transformations

class TestContentOnlyMode(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        # Create a sample config for testing
        self.sample_config = {
            "agents": [
                {"name": "strategy_lead_agent", "gate": False},          # 1
                {"name": "learner_research_agent", "gate": False},       # 2
                {"name": "learning_architect_agent", "gate": False},     # 3
                {"name": "instructional_designer_agent", "gate": False}, # 4
                {"name": "assessment_designer_agent", "gate": False},    # 5
                {"name": "storyboard_agent", "gate": False},             # 6
                {"name": "media_producer_agent", "gate": False},         # 7 (TO BE REMOVED)
                {"name": "qa_agent", "gate": False},                     # 8 -> 7
                {"name": "change_management_agent", "gate": False},      # 9 -> 8
                {"name": "operations_librarian_agent", "gate": False}    # 10 -> 9
            ],
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [3, 6, 9]
            }
        }

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_content_only_profile_filtering(self):
        """Test that content_only profile filters media_producer_agent and adjusts gates."""
        
        # Apply transformation
        new_config = apply_profile_transformations(self.sample_config, "content_only")
        
        # Check agents
        agent_names = [a["name"] for a in new_config["agents"]]
        self.assertNotIn("media_producer_agent", agent_names)
        self.assertEqual(len(agent_names), 9)
        self.assertEqual(agent_names[6], "qa_agent") # Step 7 should now be QA
        
        # Check gates
        self.assertEqual(new_config["approval"]["phase_gates"], [3, 6, 8])

    def test_other_profile_no_change(self):
        """Test that other profiles do not change the config."""
        new_config = apply_profile_transformations(self.sample_config, "pilot")
        self.assertEqual(len(new_config["agents"]), 10)
        self.assertEqual(new_config["approval"]["phase_gates"], [3, 6, 9])
        
    def test_integration_dry_run_execution(self):
        """
        Run the pipeline script in dry_run mode with content_only profile and verify output.
        We create a valid temporary inputs directory that satisfies the quality gate,
        rather than relying on _inputs_demo (which may fail quality validation).
        """
        import subprocess
        import tempfile

        # Build deterministic, gold-standard-like inputs that pass validate_inputs_quality.py
        business_brief_content = """\
# Copilot Adoption Enablement — Business Brief

## Business Context

This program addresses the organizational need to adopt Microsoft Copilot effectively
across all business units, accelerating productivity and reducing manual overhead.

## Organizational Goals

- Increase individual contributor productivity by 25% within the first quarter post-training.
- Reduce time spent on repetitive drafting and summarization tasks by 40% annually.
- Achieve 80% active Copilot utilization rate across all licensed users within 6 months.

## Target Audience

Knowledge workers, team leads, and managers across Sales, Marketing, HR, and Operations
who hold Microsoft 365 licenses and interact with Copilot daily.

## Learning Objectives

- Identify the core capabilities of Microsoft Copilot and how they map to daily workflows.
- Apply Copilot prompting strategies to generate high-quality first drafts and summaries.
- Evaluate Copilot outputs critically to ensure accuracy before sharing with stakeholders.
- Integrate Copilot into team collaboration rituals including meetings and document reviews.
- Demonstrate responsible AI behavior by recognizing limitations and escalating appropriately.

## Success Metrics

- At least 75% of participants pass the final knowledge check with a score >= 80% within 30 days.
- Average time-to-first-draft reduced by 30% monthly as measured in pilot team retrospectives.
- 90% of participants complete the course within 2 weeks of enrollment, tracked in LMS.

## Delivery Modality

Asynchronous self-paced eLearning with optional live Q&A sessions hosted weekly.

## Strategic Framing

This initiative is part of the broader AI-Ready Workforce program. Content must reflect
Conducted Intelligence principles: Belief (why Copilot matters), Behavior (how to act
differently with Copilot), and Systems (what policies and enablers are in place).
"""

        sme_notes_content = """\
# SME Notes: Microsoft Copilot Enablement

## Core Instructional Philosophy

Belief drives behavior. Learners must first believe that Copilot is trustworthy and useful
before they will change their daily habits. We embed Belief shifts, Behavior changes, and
Systems alignment into every module.

## Essential Concept Coverage

- What Copilot is and is not (AI assistant, not a decision-maker)
- How to write effective prompts using the CRAFT framework
- Copilot in Teams, Word, Outlook, and Excel — practical use cases
- Reviewing and validating Copilot outputs before acting on them

## Gotchas

- Learners often over-trust Copilot output without reviewing for accuracy — stress the
  human-in-the-loop principle.
- Some users conflate Copilot with search engines; clarify the generation vs. retrieval distinction.
- Policy boundaries: Copilot may surface confidential documents — remind learners of data
  governance responsibilities.

## Responsible AI Behavior Model

Copilot operates within ethical guardrails. Learners must understand:
- Belief: AI is a tool, not an authority. Human judgment is always final.
- Behavior: Always review, annotate, and cite AI-generated content before sharing.
- Systems: Adhere to the company's AI Acceptable Use Policy.

## Systems & Policy Alignment

All Copilot-generated content must be processed through the standard compliance review
workflow. Data classification policies apply. Usage logs are auditable.

## Tone & Human Experience

Conversational, practical, and confidence-building. Avoid jargon. Acknowledge anxiety
around job displacement honestly and redirect toward empowerment.

## Non-Negotiable Learning Outcomes

- Every learner must be able to write a functional Copilot prompt after Module 1.
- Every learner must identify at least one responsible AI safeguard before course completion.
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            inputs_dir = Path(tmp_dir)
            (inputs_dir / "business_brief.md").write_text(business_brief_content, encoding="utf-8")
            (inputs_dir / "sme_notes.md").write_text(sme_notes_content, encoding="utf-8")

            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "run_pipeline.py"),
                "--governance_profile", "content_only",
                "--dry_run",
                "--max-step", "9",
                "--inputs-dir", str(inputs_dir),
                "--allow-dirty-worktree"
            ]

            # Enough APPROVEs to handle all phase/risk gates
            input_str = ("APPROVE\n" * 10)

            result = subprocess.run(
                cmd,
                input=input_str,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )

        # Check return code
        if result.returncode != 0:
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")

        self.assertEqual(result.returncode, 0, f"Script failed with code {result.returncode}")

        stdout = result.stdout

        # Verify Run Plan
        self.assertIn("Agents (9 steps)", stdout)
        self.assertIn("Updated phase gates to: [3, 6, 8]", stdout)

        # Verify Execution
        self.assertIn("STARTING PIPELINE EXECUTION", stdout)
        self.assertIn("Running Step 1: strategy_lead_agent", stdout)
        self.assertIn("Running Step 9: operations_librarian_agent", stdout)
        self.assertIn("✅ RUN COMPLETE", stdout)

        # Verify Risk Gate Handling
        self.assertIn("RISK GATE: open_questions_threshold", stdout)
        self.assertIn("OVERRIDE and continue", stdout)  # Prompt was shown

        # Verify Step 7 is QA (since media producer removed)
        self.assertIn("Running Step 7: qa_agent", stdout)
