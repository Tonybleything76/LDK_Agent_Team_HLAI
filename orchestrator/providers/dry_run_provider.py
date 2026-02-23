"""
Dry Run Provider - Returns deterministic valid JSON without making API calls.

This provider is used for testing the orchestration flow without incurring API costs.
It returns valid JSON matching the agent output contract with stub content.
"""

import json
from orchestrator.providers.base import BaseProvider


class DryRunProvider(BaseProvider):
    """
    Provider that returns deterministic valid JSON stubs without making API calls.
    
    Used for testing the full pipeline (prompt rendering, validation, state merging,
    checkpoints, gates) without incurring API costs.
    """
    
    def run(self, prompt: str) -> str:
        """
        Return a deterministic valid JSON stub.
        
        Args:
            prompt: The agent prompt (used to extract agent name if possible)
            
        Returns:
            Valid JSON string matching agent output contract
        """
        # Try to extract agent name from prompt for better stub content
        agent_name = self._extract_agent_name(prompt)
        
        simulated_open_questions = []
        simulated_deliverable_suffix = ""

        if agent_name.lower() == "strategy lead":
            # Simulate Threshold Gate Trigger (simulating > 8 major issues)
            for i in range(10):
                simulated_open_questions.append(f"MAJOR: Simulated specific issue {i}")

        if agent_name.lower() == "quality assurance specialist":
            # Simulate QA Critical Gate Trigger
            simulated_open_questions.append("CRITICAL: Simulated Blocking Issue")
            simulated_deliverable_suffix = "\n\nSeverity: Critical"

        # Detect learning_architect_agent by prompt heading
        is_learning_architect = (
            "# Learning Architect Agent" in prompt
            or "learning_architect_agent" in prompt
        )

        is_quality_review = "Quality Review Agent" in prompt

        if is_quality_review:
            input_data = prompt.split("# Input Data")[-1] if "# Input Data" in prompt else prompt
            has_gov = "governance" in input_data.lower() or "accountability" in input_data.lower()
            has_refl = "reflection" in input_data.lower() or "dialogue" in input_data.lower()
            
            score = 10
            gov_score = 2
            refl_score = 2
            
            if not has_gov:
                score -= 2
                gov_score = 0
            if not has_refl:
                score -= 2
                refl_score = 0
                
            premium = bool(score >= 9)
            
            report = {
                "quality_score": score,
                "premium_flag": premium,
                "domain_scores": {
                    "transformational_trigger": 2,
                    "bloom_depth": 2,
                    "dialogue_density": refl_score,
                    "governance_anchor": gov_score,
                    "level3_behavior": 2
                },
                "observations": ["Dry run realistic scoring applied."],
                "improvement_recommendations": []
            }
            return json.dumps(report, indent=2)

        if is_learning_architect:
            return self._create_learning_architect_stub(prompt)

        # Create deterministic valid JSON response
        deliverable = self._create_stub_deliverable(agent_name) + simulated_deliverable_suffix
        
        response = {
            "deliverable_markdown": deliverable,
            "updated_state": {},
            "open_questions": simulated_open_questions
        }
        
        return json.dumps(response, indent=2)
    
    def _extract_agent_name(self, prompt: str) -> str:
        """
        Attempt to extract agent name from prompt.
        
        Args:
            prompt: The agent prompt
            
        Returns:
            Agent name if found, otherwise "Unknown Agent"
        """
        # Look for common patterns in prompts
        lines = prompt.split('\n')
        
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            
            # Pattern: "# Role: Strategy Lead Agent"
            if line.startswith('# Role:'):
                return line.replace('# Role:', '').strip()
            
            # Pattern: "You are the **Quality Assurance Specialist**"
            if "You are the" in line or "You are a" in line:
                # Remove common prefixes
                cleaned = line.replace('You are the', '').replace('You are a', '').strip()
                # Remove markdown bold/italic
                cleaned = cleaned.replace('**', '').replace('*', '')
                # Take everything before the first comma, period, or newline
                agent_name = cleaned.split(',')[0].split('.')[0].strip()
                if agent_name:
                    return agent_name
        
        return "Unknown Agent"

    def _create_learning_architect_stub(self, prompt: str = "") -> str:
        """
        Return a deterministic, contract-compliant stub for learning_architect_agent.

        Contract enforced by orchestrator/validation.py:
        - updated_state must have: course_title, course_summary, target_audience,
          business_goal_alignment, belief_behavior_systems, curriculum,
          constraints, assumptions
        - curriculum.modules: exactly 6, IDs M1-M6
        - Each module: module_id, title, outcome, key_concepts (4-8),
          activities (2-4), checks (2-3) with valid types
        """
        deliverable = (
            "# DRY RUN: Learning Architect Agent\n\n"
            "This is a **dry run stub**. No API call was made.\n\n"
            "## Course Architecture Blueprint\n\n"
            "This stub provides a deterministic 6-module course architecture "
            "used to validate the orchestration pipeline without live API calls.\n\n"
            "### Module Overview\n\n"
            "| Module | Title | Outcome |\n"
            "|--------|-------|---------|\n"
            "| M1 | Foundations & Mental Models | Apply foundational concepts to real scenarios |\n"
            "| M2 | Core Skills Development | Demonstrate core skill proficiency |\n"
            "| M3 | Applied Practice | Execute key workflows using learned skills |\n"
            "| M4 | Advanced Techniques | Analyze complex situations and adapt approaches |\n"
            "| M5 | Integration & Synthesis | Synthesize skills across multiple contexts |\n"
            "| M6 | Capstone & Accountability | Design and defend an end-to-end solution |\n\n"
            "### Validation Notes\n\n"
            "- All 6 modules present with sequential IDs M1-M6\n"
            "- Each module contains: outcome, 4 key concepts, 2 activities, 2 checks\n"
            "- Check types: mcq and short_answer (both valid per schema)\n\n"
            "*Generated by DryRunProvider — No API calls made*\n"
        )

        def make_module(idx: int, title: str, outcome: str) -> dict:
            mid = f"M{idx}"
            return {
                "module_id": mid,
                "title": title,
                "outcome": outcome,
                "objectives": [
                    f"{mid} Objective 1: Identify and apply core principles from this module",
                    f"{mid} Objective 2: Analyze and evaluate outcomes in realistic scenarios",
                ],
                "key_concepts": [
                    f"{mid} Concept A",
                    f"{mid} Concept B",
                    f"{mid} Concept C",
                    f"{mid} Concept D",
                ],
                "activities": [
                    f"{mid} Activity 1: Guided practice exercise",
                    f"{mid} Activity 2: Scenario-based application",
                ],
                "checks": [
                    {
                        "type": "mcq",
                        "prompt": f"{mid}: Which option best demonstrates the core principle?",
                        "success_criteria": ["Select the option that applies the principle correctly"],
                    },
                    {
                        "type": "short_answer",
                        "prompt": f"{mid}: Describe how you would apply this module's outcome in your role.",
                        "success_criteria": ["Response cites at least one key concept from this module"],
                    },
                ],
            }

        target_modules = 6
        import re
        match = re.search(r"MODULE_COUNT_TARGET:\s*(\d+)", prompt)
        if match:
            target_modules = int(match.group(1))

        titles = [
            "Foundations & Mental Models",
            "Core Skills Development",
            "Applied Practice",
            "Advanced Techniques",
            "Integration & Synthesis",
            "Capstone & Accountability",
        ]

        modules = []
        for i in range(1, target_modules + 1):
            title = titles[i-1] if i <= len(titles) else f"Extra Module {i}"
            outcome = "Demonstrate core concepts" if i > 1 else "Identify and apply foundational concepts to realistic scenarios."
            modules.append(make_module(i, title, outcome))

        response = {
            "deliverable_markdown": deliverable,
            "updated_state": {
                "course_title": "Dry Run Course: Generic Training Program",
                "course_summary": (
                    "This course provides a structured learning journey through six progressive modules. "
                    "Learners develop foundational knowledge, build core skills, and integrate "
                    "capabilities into a capstone project. Content is generic and serves as a "
                    "dry-run stub for pipeline validation purposes."
                ),
                "target_audience": "General professional learners undergoing structured onboarding or upskilling.",
                "business_goal_alignment": [
                    "Improve learner competency in core job functions",
                    "Reduce time-to-proficiency for new team members",
                    "Establish a repeatable and measurable training baseline",
                ],
                "belief_behavior_systems": {
                    "belief": "Learners gain confidence when they see structured, achievable milestones",
                    "behaviors": [
                        "Apply module concepts immediately after each learning session",
                        "Reference course materials when encountering real job challenges",
                    ],
                    "systems_policies_enablers": [
                        "Learning Management System (LMS) for delivery and tracking",
                        "Manager check-in cadence aligned to module completion",
                    ],
                },
                "curriculum": {
                    "modules": modules,
                },
                "constraints": {
                    "length_minutes": 30,
                    "modality": "self-paced digital micro-modules",
                    "do_not_invent_policies": True,
                },
                "assumptions": [
                    "Dry-run stub: content is generic and not derived from real inputs.",
                ],
            },
            "open_questions": [],
        }

        return json.dumps(response, indent=2)

    def _create_stub_deliverable(self, agent_name: str) -> str:
        """
        Create stub deliverable markdown content.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Markdown content for the stub deliverable
        """
        return f"""# DRY RUN: {agent_name}

This is a **dry run stub**. No API call was made.

## Purpose

This output was generated by the DryRunProvider to test the orchestration flow
without incurring API costs. This is sample content for testing purposes only.

## What This Tests

- ✅ Prompt rendering and templating
- ✅ JSON extraction and parsing
- ✅ Validation (min chars, stub marker detection)
- ✅ State merging
- ✅ Checkpoint creation
- ✅ Manifest updates
- ✅ Approval gate triggering

## Sample Content

This section contains enough text to pass the minimum character validation threshold.
The dry run provider generates deterministic, valid JSON responses that match the
agent output contract. This allows you to test the entire pipeline flow including
prompt rendering, state management, checkpoints, and approval gates without making
any actual API calls or incurring costs.

## Next Steps

To run with real providers, use:
- `python3 scripts/run_pipeline.py --mode openai`
- `python3 scripts/run_pipeline.py --mode manual`
- `python3 scripts/run_pipeline.py --mode claude_cli`

---

*Generated by DryRunProvider - No API calls made*
"""
