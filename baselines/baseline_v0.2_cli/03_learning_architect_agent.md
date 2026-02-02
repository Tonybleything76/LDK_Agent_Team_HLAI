# Curriculum Design Document
## AI Adoption for Operations Managers

---

### Program Overview

| Attribute | Detail |
|---|---|
| Program Name | AI Adoption for Operations Managers |
| Format | Self-paced eLearning (desktop and tablet) |
| Total Duration | ~43 minutes (within 45-minute constraint) |
| Modules | 4 |
| Total Lessons | 12 |
| Assessment Model | Formative scenario checks per module + summative capstone scenario |
| Audience | Plant operations managers with no prior AI knowledge |

---

## Module 1: Understanding Your AI Dashboard

**Module Goal:** Establish what the AI dashboard is, where its data comes from, and why it is a reliable source of production information.

**Introduction/Hook:** *"It's 6:02 AM. You walk onto the floor, coffee in hand. Before you check in with your team, there's a screen showing you exactly what happened overnight — and what's about to happen next. But only if you know how to read it."* This hook grounds the learning in a recognizable shift-start moment (addressing Persona A's need for relevance and Persona B's need for immediate value).

**Duration:** ~10 minutes

**Outcomes Addressed:** LO1

### Lesson 1.1: What You're Looking At
- **Lesson Title:** What You're Looking At
- **Learning Objective:** Identify the main components visible on the AI dashboard home screen.
- **Format:** Interactive annotated screenshot (guided exploration)
- **Key Content Points:**
  - The AI dashboard is the single view that consolidates production line data.
  - Three primary areas: performance trends panel, predictive alerts panel, throughput indicators panel.
  - Each area answers a different operational question.
- **Practice Activity:** Label-the-dashboard drag-and-drop exercise — learner matches panel names to regions on a sample dashboard screenshot.

### Lesson 1.2: Where the Data Comes From
- **Lesson Title:** Where the Data Comes From
- **Learning Objective:** Explain that dashboard data originates from production line sensors and updates every 5 minutes.
- **Format:** Short animated explainer (60–90 seconds) + text summary
- **Key Content Points:**
  - Data is pulled directly from production line sensors — not manually entered, not estimated.
  - Dashboard refreshes every 5 minutes with the latest sensor readings.
  - This means the numbers reflect actual machine and line conditions, not projections or opinions.
  - Explicitly address misconception: "This is sensor data, not a guess."
- **Practice Activity:** Scenario check question — *"A colleague says the dashboard numbers are just the system's best guess. Based on what you've learned, how would you respond?"* (Multiple choice targeting the sensor-data fact.)

### Lesson 1.3: Why This Matters to Your Shift
- **Lesson Title:** Why This Matters to Your Shift
- **Learning Objective:** Describe one specific way dashboard data can inform a shift-start decision.
- **Format:** Text + brief scenario vignette
- **Key Content Points:**
  - Before the dashboard: you relied on overnight reports, verbal handoffs, or walking the floor.
  - With the dashboard: you see the current state of every line in one view before you make your first call.
  - Frame: The dashboard does not replace your judgment — it gives your judgment better inputs.
  - Quick-win example: checking overnight throughput trend at shift start to prioritize the first hour.
- **Practice Activity:** Reflection prompt — *"Think about the first decision you make each shift. What dashboard data point would be most useful?"* (Free-text or selection from provided options.)

---

## Module 2: Reading the Signals

**Module Goal:** Enable learners to identify and differentiate the three key dashboard elements — performance trends, predictive alerts, and throughput indicators — so they can read the dashboard without confusion.

**Introduction/Hook:** *"You check the dashboard. There's a green line trending upward, a yellow alert box, and a throughput number in red. Are any of these urgent? All of them? None? Let's make sure you know."* This hook speaks directly to the interpretation-overload barrier identified in research.

**Duration:** ~10 minutes

**Outcomes Addressed:** LO2

### Lesson 2.1: Performance Trends — The Big Picture
- **Lesson Title:** Performance Trends — The Big Picture
- **Learning Objective:** Interpret a performance trend line to determine whether production output is stable, improving, or declining.
- **Format:** Interactive visual (annotated trend graph with tooltips)
- **Key Content Points:**
  - Performance trends show output over time (e.g., last 8 hours, last shift, last 24 hours).
  - Upward trend = output increasing; downward trend = output declining; flat = stable.
  - Trends represent what has happened and what is currently happening — historical and real-time combined.
  - Key skill: recognizing whether a trend is within normal operating range or deviating.
- **Practice Activity:** Read-the-graph exercise — learner views three trend lines and classifies each as stable, improving, or declining.

### Lesson 2.2: Predictive Alerts — What's Coming
- **Lesson Title:** Predictive Alerts — What's Coming
- **Learning Objective:** Distinguish a predictive alert from a performance trend by identifying its forward-looking nature and action window.
- **Format:** Text + side-by-side comparison visual
- **Key Content Points:**
  - Predictive alerts are different from trends — they tell you what the data suggests will happen.
  - Each alert includes: what is predicted, the basis (sensor pattern), and a recommended action window.
  - Alerts are generated from sensor data patterns — they are evidence-based, not speculative.
  - Terminology: "predictive alert" = forward-looking, sensor-based signal.
- **Practice Activity:** Sort exercise — learner is given a set of dashboard messages and sorts them into "performance trend" or "predictive alert."

### Lesson 2.3: Throughput Indicators — The Numbers Right Now
- **Lesson Title:** Throughput Indicators — The Numbers Right Now
- **Learning Objective:** Read a throughput indicator and state whether current output is above, at, or below target.
- **Format:** Interactive dashboard snippet with guided walkthrough
- **Key Content Points:**
  - Throughput indicators show real-time output rates against target.
  - Color coding: green = at or above target; yellow = approaching threshold; red = below target.
  - These numbers update every 5 minutes with the sensor refresh.
  - Throughput indicators tell you the current state — they complement trends (past/direction) and alerts (future).
- **Practice Activity:** Scenario check — *"The throughput indicator for Line 3 shows red at 82% of target. The trend line has been declining for 2 hours. A predictive alert says potential stoppage in 90 minutes. Which element tells you what's happening right now? Which tells you what might happen next?"* (Multiple-select question.)

---

## Module 3: Interpreting Predictive Alerts

**Module Goal:** Build the skill and confidence to interpret a predictive alert accurately — understanding what it predicts, why it should be trusted, and when to act.

**Introduction/Hook:** *"The dashboard just flagged a predictive alert: 'Throughput drop detected on Line 2. Predicted machine fault within 2 hours.' Your first instinct might be to dismiss it. Before you do — let's look at what's actually behind that alert."* This directly uses the SME-provided real scenario and confronts the dismissal behavior head-on.

**Duration:** ~10 minutes

**Outcomes Addressed:** LO3

### Lesson 3.1: Anatomy of a Predictive Alert
- **Lesson Title:** Anatomy of a Predictive Alert
- **Learning Objective:** Identify the three components of a predictive alert: prediction, confidence basis, and recommended action window.
- **Format:** Annotated alert example (interactive callouts)
- **Key Content Points:**
  - Every predictive alert contains three parts:
    1. **The Prediction:** What the system expects to happen (e.g., machine fault, throughput drop).
    2. **The Confidence Basis:** What sensor data pattern triggered the alert (e.g., vibration pattern, temperature deviation).
    3. **The Action Window:** How much time you have to respond before the predicted event is likely.
  - Walk through the SME example: throughput drop → predicted machine failure → 2-hour action window.
- **Practice Activity:** Deconstruct-the-alert exercise — learner reads a new alert and identifies the prediction, confidence basis, and action window.

### Lesson 3.2: Why This Isn't a Guess
- **Lesson Title:** Why This Isn't a Guess
- **Learning Objective:** Explain why a predictive alert is based on sensor evidence rather than speculation.
- **Format:** Short explainer text + comparison table
- **Key Content Points:**
  - Common misconception: "The AI is just guessing." (Directly from SME notes.)
  - Reality: Alerts are triggered by specific sensor data patterns — vibration, temperature, pressure, throughput rate.
  - Analogy: Like a check-engine light in a car — it's not a guess, it's a sensor reading triggering a known pattern.
  - Comparison table: Guess vs. Sensor-Based Prediction (columns: basis, reliability, action value).
  - Frame: Not perfect, but evidence-based and faster than waiting for visible breakdown.
- **Practice Activity:** Scenario check — *"A colleague says, 'I don't trust these alerts — the computer is just guessing.' Using what you've learned, select the best response."* (Multiple choice with rationale feedback.)

### Lesson 3.3: Acting Within the Window
- **Lesson Title:** Acting Within the Window
- **Learning Objective:** Determine the appropriate urgency of response based on an alert's action window.
- **Format:** Decision scenario (branching)
- **Key Content Points:**
  - The action window tells you how long you have — this determines urgency.
  - Short window (< 1 hour): Immediate attention required — assess, decide, act or escalate.
  - Medium window (1–4 hours): Plan response within current shift.
  - Long window (> 4 hours): Monitor, include in shift handoff notes.
  - Key point: Ignoring the window doesn't make the prediction go away — it reduces your response options.
- **Practice Activity:** Triage exercise — learner receives three alerts with different action windows and ranks them by response urgency.

---

## Module 4: Making Data-Driven Decisions

**Module Goal:** Integrate all prior skills into a complete decision workflow — consult, interpret, decide, document — so dashboard-informed decision-making becomes a repeatable practice.

**Introduction/Hook:** *"You've learned to read the dashboard and interpret its alerts. Now the question that matters most: What do you actually do with this information? This module puts you in the driver's seat."* This sets up the capstone experience and frames the manager as the decision-maker — the dashboard is an input, not a replacement (addressing identity threat for Persona A).

**Duration:** ~13 minutes (+ 2-minute capstone = 15 minutes total)

**Outcomes Addressed:** LO4, LO5

### Lesson 4.1: Evaluating AI Recommendations
- **Lesson Title:** Evaluating AI Recommendations
- **Learning Objective:** Apply a three-step evaluation to an AI recommendation: assess the data, consider the operational context, and choose to act, modify, or escalate.
- **Format:** Text + guided framework + worked example
- **Key Content Points:**
  - The AI gives recommendations — you make decisions. The dashboard is an input to your judgment, not a replacement.
  - Three-step evaluation framework:
    1. **Assess the data:** What is the alert telling me? What is the confidence basis?
    2. **Consider the context:** What else do I know about current operations? (Staffing, schedule, known issues.)
    3. **Decide:** Act on the recommendation as-is, modify it based on context, or escalate to a specialist/supervisor.
  - Worked example using the SME scenario: throughput drop alert → evaluate sensor basis → consider current shift status → decide to schedule preventive check.
  - Caution for early-career managers (Persona C): AI recommendations are valuable inputs but must be evaluated, not followed blindly.
- **Practice Activity:** Evaluation exercise — learner receives an AI recommendation and walks through the three-step framework, selecting their decision with rationale.

### Lesson 4.2: When to Escalate
- **Lesson Title:** When to Escalate
- **Learning Objective:** Identify conditions under which an AI alert should be escalated rather than acted on independently.
- **Format:** Decision table + scenario
- **Key Content Points:**
  - Escalation criteria:
    - Alert involves safety risk.
    - Alert severity exceeds your authority or expertise.
    - Multiple alerts converging on the same line or system.
    - Action window is too short for independent response.
  - Escalation is a valid, professional decision — not a failure.
  - Who to escalate to and what information to include (alert details, your assessment, time remaining).
- **Practice Activity:** Escalation judgment call — learner reads two scenarios and decides whether to act independently or escalate, selecting rationale.

### Lesson 4.3: The Complete Decision Workflow
- **Lesson Title:** The Complete Decision Workflow
- **Learning Objective:** Execute a four-step dashboard-informed decision workflow: consult, interpret, decide, document.
- **Format:** Interactive walkthrough + workflow summary graphic
- **Key Content Points:**
  - Four-step workflow:
    1. **Consult:** Open the dashboard. Review trends, alerts, and throughput indicators.
    2. **Interpret:** Identify anything that requires attention. Read alert details.
    3. **Decide:** Use the three-step evaluation. Act, modify, or escalate.
    4. **Document:** Record what you saw, what you decided, and why.
  - When to use: Shift start, before production adjustments, when alerts appear, post-incident review.
  - Documentation protects you and helps the next shift — it builds an evidence trail.
  - Habit formation: The more you use this workflow, the faster and more natural it becomes.
- **Practice Activity:** None (flows directly into capstone).

### Lesson 4.4: Capstone Scenario
- **Lesson Title:** Capstone — Your Shift, Your Call
- **Learning Objective:** Demonstrate the complete decision workflow by consulting a simulated dashboard, interpreting signals, making a decision, and documenting rationale.
- **Format:** Summative scenario-based assessment (interactive simulation)
- **Key Content Points:**
  - Scenario: Learner arrives at shift start. The simulated dashboard shows:
    - A declining throughput trend on Line 4.
    - A predictive alert: motor overheating predicted within 90 minutes.
    - Throughput indicator showing Line 4 at 78% of target (red).
  - Learner must:
    1. Identify the most critical signal.
    2. Interpret the predictive alert (state the prediction, basis, and action window).
    3. Evaluate the recommendation against context provided (staffing level, production schedule).
    4. Choose to act, modify, or escalate — and justify the decision.
  - Passing threshold: 80% accuracy across scenario questions.
- **Practice Activity:** This IS the assessment. Scored with feedback on each step.

---

## Curriculum Summary

| Module | Title | Duration | Lessons | Outcomes |
|--------|-------|----------|---------|----------|
| 1 | Understanding Your AI Dashboard | 10 min | 3 | LO1 |
| 2 | Reading the Signals | 10 min | 3 | LO2 |
| 3 | Interpreting Predictive Alerts | 10 min | 3 | LO3 |
| 4 | Making Data-Driven Decisions | 15 min | 4 (incl. capstone) | LO4, LO5 |
| **Total** | | **~45 min** | **13** | **LO1–LO5** |

## Design Decisions

1. **Scenario-first approach:** Every module opens with a recognizable production scenario to maintain engagement and establish relevance immediately (dropout risk mitigation).
2. **Trust-building arc:** Module 1 establishes data credibility (sensors, not guesses), Module 3 deepens it with the anatomy of alerts, and Module 4 positions the manager as the ultimate decision-maker.
3. **Persona differentiation handled through framing:** Content addresses over-trust (Persona C — evaluate, don't blindly follow) and under-trust (Persona A — sensor evidence, not speculation) within the same lessons rather than branching paths, keeping the course within time constraints.
4. **Modular and interruptible:** Each module is self-contained (~10–15 minutes) to accommodate shift-based completion and interruption-prone environments.
5. **Capstone as integration:** Lesson 4.4 requires the learner to execute the entire workflow, ensuring all five learning outcomes are assessed in context.
6. **Compliance:** No sensitive data export. All scenarios use simulated data. Dashboard simulations do not connect to live systems.
