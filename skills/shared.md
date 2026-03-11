# Shared Pipeline Standards
## Applied to every agent in every run.

---

## Conducted Intelligence Framework (HuminLoop AI)

All course content must operationalize the **Conducted Intelligence** belief:
> AI creates value only when guided by human judgment, responsibility, and purpose.

Every deliverable must reinforce three layers:
- **Belief** — humans remain accountable for outcomes created with AI
- **Behavior** — professionals use AI deliberately, with verification
- **Systems** — organisational policies and governance enable safe usage

Never position AI as magic, infallible, or a replacement for professional judgment.
Always position AI as a **cognitive amplifier requiring human direction**.

---

## Instructional Design Standards

### Bloom's Taxonomy Alignment
Apply the correct cognitive level for each learning objective:

| Level | Verb Examples | Use For |
|-------|--------------|---------|
| Remember | define, list, identify | foundational literacy |
| Understand | explain, describe, summarise | concept comprehension |
| Apply | use, demonstrate, execute | workflow integration |
| Analyse | compare, differentiate, examine | critical evaluation |
| Evaluate | assess, judge, justify | responsible AI judgment |
| Create | design, construct, produce | advanced application |

For a foundational AI literacy course: favour **Understand**, **Apply**, and **Evaluate** levels.

### Adult Learning Principles (Andragogy)
- Adults learn best when content is immediately applicable to real work
- Connect every concept to a concrete PR/communications scenario
- Respect prior professional experience — do not infantilise learners
- Self-direction: give learners decision points, not just information
- Problem-centred: organise around real tasks, not abstract topics

### Scenario-Anchored Design
All content should be grounded in realistic PR and communications scenarios:
- Writing press releases and media statements
- Researching policy, stakeholders, and narratives
- Preparing presentations for executives and clients
- Managing confidential client information
- Handling reputational risk and ethical dilemmas

---

## Quality Standards

### Writing Quality
- Senior professional register — not academic, not casual
- Active voice, present tense where possible
- Concrete over abstract: show examples, not just principles
- Measurable and specific: avoid vague language like "understand" or "appreciate"

### Deliverable Completeness
- Every module/section must be fully written — no placeholders, no stubs
- If content is uncertain, raise an `open_question` but still write the best-available version
- Length: enough to be execution-ready, not exhaustively long

### PR-Specific Ethical Framing
Always include explicit treatment of:
- Hallucination risk and fact verification
- Client confidentiality and data governance
- Bias and tone in AI-generated content
- Human accountability before publication
- Reputational liability when AI output is used without review

---

## JSON Output Discipline
- Return ONLY a valid JSON object — no markdown fences, no commentary
- All string values must use double quotes and proper JSON escaping
- `deliverable_markdown` must be substantive, professional Markdown
- `updated_state` must be consistent with `deliverable_markdown`
- `open_questions` must be a JSON array of strings
