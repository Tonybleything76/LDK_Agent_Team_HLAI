# Assessment Plan — AI Adoption for Operations Managers

## Assessment Strategy Overview

| Element | Detail |
|---|---|
| **Program** | AI Adoption for Operations Managers |
| **Assessment Model** | Formative scenario checks per module + summative capstone scenario |
| **Success Threshold** | 80% accuracy on scenario-based assessments |
| **Total Formative Questions** | 8 (2 per module) |
| **Summative Assessment** | 4-question capstone scenario (Module 4) |
| **Total Assessment Items** | 12 |

---

## Formative Assessments by Module

### Module 1 — Understanding Your AI Dashboard (LO1)

**Question F1.1 — Misconception Check**

- **Stem:** A colleague says: "I don't trust the AI dashboard — the numbers are just the computer's best guess." Which response is most accurate?
- **Options:**
  - A) "You're right — the AI generates estimates based on historical averages."
  - B) "The dashboard displays sensor data collected directly from production line equipment and refreshed every 5 minutes."
  - C) "The data is entered manually by the night shift supervisor."
  - D) "The AI uses industry benchmarks, not our actual production data."
- **Correct Answer:** B
- **Feedback (Correct):** Correct. The AI dashboard pulls data directly from production line sensors and updates every 5 minutes. The numbers reflect actual machine conditions, not estimates or guesses.
- **Feedback (Incorrect):** Not quite. The dashboard data is not guessed, manually entered, or based on external benchmarks. It comes directly from production line sensors and refreshes every 5 minutes, reflecting actual machine conditions.
- **LO Alignment:** LO1

**Question F1.2 — Data Source Identification**

- **Stem:** How frequently does the AI dashboard update, and where does its data come from?
- **Options:**
  - A) Every hour, from manually entered shift reports
  - B) Every 5 minutes, from production line sensors
  - C) Once per shift, from quality control inspections
  - D) In real-time, from external industry databases
- **Correct Answer:** B
- **Feedback (Correct):** Correct. The dashboard refreshes every 5 minutes using data pulled directly from production line sensors — temperature, vibration, pressure, and speed.
- **Feedback (Incorrect):** Incorrect. The AI dashboard updates every 5 minutes and pulls its data directly from production line sensors. It is not manually entered, not drawn from external databases, and not limited to once-per-shift updates.
- **LO Alignment:** LO1

---

### Module 2 — Reading the Signals (LO2)

**Question F2.1 — Signal Differentiation**

- **Stem:** You see three items on the dashboard: a line graph showing output over the past 8 hours, a yellow box stating "Conveyor jam predicted within 1 hour," and a number reading "91%" in yellow. Which correctly identifies all three?
- **Options:**
  - A) Predictive alert, throughput indicator, performance trend
  - B) Performance trend, predictive alert, throughput indicator
  - C) Throughput indicator, performance trend, predictive alert
  - D) Performance trend, throughput indicator, predictive alert
- **Correct Answer:** B
- **Feedback (Correct):** Correct. The line graph over time is a performance trend (what happened), the yellow prediction box is a predictive alert (what's coming), and the percentage against target is a throughput indicator (where you are right now).
- **Feedback (Incorrect):** Review the three dashboard elements: Performance trends show output over time (graphs/lines). Predictive alerts are forward-looking warnings with action windows. Throughput indicators show current output rate against target (percentage with color coding).
- **LO Alignment:** LO2

**Question F2.2 — Throughput Indicator Interpretation**

- **Stem:** Line 3 shows a throughput indicator of 78% in red. What does this tell you?
- **Options:**
  - A) Line 3 is operating above target
  - B) Line 3 is approaching its target threshold
  - C) Line 3 is currently operating below its production target
  - D) Line 3 has been shut down for maintenance
- **Correct Answer:** C
- **Feedback (Correct):** Correct. Red indicates the line is below its production target. Green means at or above target, yellow means approaching the threshold, and red means below target.
- **Feedback (Incorrect):** A red throughput indicator means the line is currently operating below its production target. Color coding: green = at/above target, yellow = approaching threshold, red = below target.
- **LO Alignment:** LO2

---

### Module 3 — Interpreting Predictive Alerts (LO3)

**Question F3.1 — Alert Component Identification**

- **Stem:** The dashboard displays: "Line 2 — Declining throughput and elevated motor vibration detected. Predicted machine fault within 2 hours." Which correctly identifies the three components of this predictive alert?
- **Options:**
  - A) Prediction: elevated motor vibration; Basis: machine fault; Window: 2 hours
  - B) Prediction: machine fault on Line 2; Basis: declining throughput + elevated motor vibration; Window: 2 hours
  - C) Prediction: declining throughput; Basis: 2-hour timeline; Window: motor vibration
  - D) Prediction: Line 2 shutdown; Basis: production schedule; Window: end of shift
- **Correct Answer:** B
- **Feedback (Correct):** Correct. The prediction is the expected event (machine fault), the confidence basis is the sensor data pattern that triggered it (declining throughput + elevated motor vibration), and the action window is the time available to respond (2 hours).
- **Feedback (Incorrect):** Every predictive alert has three parts: (1) Prediction — what the system expects to happen (machine fault on Line 2); (2) Confidence Basis — the sensor data pattern triggering the alert (declining throughput + elevated motor vibration); (3) Action Window — time to respond (2 hours).
- **LO Alignment:** LO3

**Question F3.2 — Urgency Triage**

- **Stem:** Three alerts appear simultaneously: Alert A — coolant flow anomaly, overheating predicted within 45 minutes. Alert B — belt wear detected, slippage predicted within 6 hours. Alert C — motor vibration increase, bearing issue predicted within 3 hours. Which alert requires the most immediate attention?
- **Options:**
  - A) Alert A — 45-minute window (immediate attention required)
  - B) Alert B — 6-hour window (longest lead time)
  - C) Alert C — 3-hour window (medium urgency)
  - D) All three should be addressed equally at the same time
- **Correct Answer:** A
- **Feedback (Correct):** Correct. Alert A has the shortest action window (45 minutes — under 1 hour), placing it in the "immediate attention" urgency tier. Alert C (3 hours) can be planned within the shift, and Alert B (6 hours) can be monitored and handed off.
- **Feedback (Incorrect):** Action window determines urgency. Under 1 hour = immediate attention, 1–4 hours = plan within shift, over 4 hours = monitor and handoff. Alert A (45 minutes) demands immediate response.
- **LO Alignment:** LO3

---

### Module 4 — Making Data-Driven Decisions (LO4, LO5)

**Question F4.1 — Evaluate a Recommendation**

- **Stem:** The dashboard recommends halting Line 5 due to predicted seal failure within 90 minutes. However, Line 5 is the only active packaging line, and a backup unit can be online in 20 minutes. Using the three-step evaluation framework, what is the most appropriate decision?
- **Options:**
  - A) Act — halt Line 5 immediately as the dashboard recommends
  - B) Modify — switch to backup unit before halting Line 5 to minimize downtime, then address the seal issue
  - C) Escalate — pass the decision to a supervisor because the dashboard might be wrong
  - D) Ignore — continue running Line 5 since the prediction might not come true
- **Correct Answer:** B
- **Feedback (Correct):** Correct. Modifying the recommendation accounts for the operational context: Line 5 is the only active packaging line, but a backup is available in 20 minutes. This avoids stopping all outbound while still addressing the predicted failure within the 90-minute window.
- **Feedback (Incorrect):** The three-step evaluation: (1) Assess data — seal failure predicted in 90 min; (2) Consider context — only packaging line, but backup available in 20 min; (3) Decide — Modify is best because it addresses the alert while minimizing operational disruption. Acting without context stops all outbound unnecessarily. Ignoring the alert risks equipment failure.
- **LO Alignment:** LO4

**Question F4.2 — Escalation Judgment**

- **Stem:** Two alerts fire simultaneously: Line 1 predicts a conveyor fault within 1 hour and Line 3 predicts a bearing failure within 45 minutes. You have one available technician. What is the appropriate action?
- **Options:**
  - A) Send the technician to Line 1 because it appeared first on the dashboard
  - B) Send the technician to Line 3 (shortest window) and escalate Line 1 to your supervisor with alert details, your assessment, and time remaining
  - C) Ignore both alerts and wait for actual failures to confirm the predictions
  - D) Send the technician to whichever line has higher output
- **Correct Answer:** B
- **Feedback (Correct):** Correct. Line 3 has the shorter action window (45 minutes) and gets the available technician. With insufficient resources for both, escalation is the professional response — include alert details, your assessment, your recommendation, and time remaining.
- **Feedback (Incorrect):** When converging alerts exceed your available resources, address the most urgent first (Line 3, 45 minutes) and escalate the other with full details. Escalation criteria include converging alerts and insufficient resources. Ignoring alerts or prioritizing by appearance order are not sound approaches.
- **LO Alignment:** LO4, LO5

---

## Summative Assessment — Capstone Scenario: "Your Shift, Your Call"

**Scenario Context:** It is the start of your shift. The Line 4 dashboard shows: throughput has been declining for 4 hours, a predictive alert warns of motor overheating with predicted failure within 90 minutes, and the throughput indicator reads 78% (red). A priority order is due in 3 hours and a technician is available.

**Question S1 — Identify the Critical Signal**

- **Stem:** Looking at the Line 4 dashboard, which signal requires your most immediate attention?
- **Options:**
  - A) The performance trend showing 4 hours of decline
  - B) The predictive alert for motor overheating with a 90-minute window
  - C) The throughput indicator at 78% (red)
  - D) All three are equally urgent
- **Correct Answer:** B
- **Feedback (Correct):** Correct. The predictive alert has the shortest action window (90 minutes) and the highest potential consequence (motor failure). The trend and throughput indicator provide supporting context, but the alert demands the most immediate response.
- **Feedback (Incorrect):** While all three signals are important, the predictive alert has the most time-sensitive action window (90 minutes) and the highest consequence if ignored (motor failure). Trends show history; throughput shows current state; the alert tells you what's about to happen.
- **LO Alignment:** LO2, LO3

**Question S2 — Interpret the Alert**

- **Stem:** Break down the predictive alert: "Motor overheating detected on Line 4. Temperature and vibration patterns consistent with imminent motor failure. Respond within 90 minutes." What are the prediction, confidence basis, and action window?
- **Options:**
  - A) Prediction: temperature increase; Basis: motor overheating; Window: 90 minutes
  - B) Prediction: imminent motor failure on Line 4; Basis: temperature and vibration sensor patterns; Window: 90 minutes
  - C) Prediction: Line 4 shutdown; Basis: throughput at 78%; Window: 3 hours
  - D) Prediction: vibration patterns; Basis: imminent failure; Window: end of shift
- **Correct Answer:** B
- **Feedback (Correct):** Correct. Prediction = the expected event (motor failure); Confidence basis = the sensor data patterns triggering the alert (temperature and vibration); Action window = available response time (90 minutes).
- **Feedback (Incorrect):** The three components: (1) Prediction — what will happen: imminent motor failure on Line 4; (2) Confidence basis — what sensor data triggered it: temperature and vibration patterns; (3) Action window — how long you have: 90 minutes. The throughput figure and shift end are not part of this alert's components.
- **LO Alignment:** LO3

**Question S3 — Evaluate and Decide**

- **Stem:** Apply the three-step evaluation. The alert predicts motor failure in 90 minutes. Context: a priority order is due in 3 hours and a technician is available now. What is the best course of action?
- **Options:**
  - A) Ignore the alert and focus on the priority order — the motor might not actually fail
  - B) Escalate immediately — this is too complex to handle independently
  - C) Modify — dispatch the technician now for inspection and planned brief stoppage within the 90-minute window while communicating the priority order status to your supervisor
  - D) Act — shut down Line 4 immediately and wait for the motor to be fully replaced
- **Correct Answer:** C
- **Feedback (Correct):** Correct. Step 1 — Data: motor failure predicted in 90 minutes. Step 2 — Context: priority order (3 hrs), technician available. Step 3 — Decision: Modify. You have resources and time to address the alert without a full shutdown. Dispatching the technician now for inspection uses the action window effectively while managing the priority order.
- **Feedback (Incorrect):** Three-step evaluation: (1) Data — motor failure in 90 min is credible and time-sensitive; (2) Context — technician is available, priority order gives urgency but also 3-hour buffer; (3) Decision — Modify is optimal because you can dispatch the technician immediately, plan a controlled intervention within the window, and manage the order. Ignoring risks failure; immediate full shutdown is premature; escalation isn't needed when you have available resources.
- **LO Alignment:** LO4, LO5

**Question S4 — Document Rationale**

- **Stem:** After making your decision, what should you include in your shift documentation? Select the most complete answer.
- **Options:**
  - A) The alert details only
  - B) The alert details, the decision made, and the rationale for your decision
  - C) The alert details, your decision, your rationale, and any escalation or communication actions taken
  - D) A copy of all raw sensor log data from Line 4
- **Correct Answer:** C
- **Feedback (Correct):** Correct. Complete documentation includes: what the alert said, what you decided, why you decided it, and what communication or escalation actions you took. This protects you, informs the next shift, and creates an auditable decision trail.
- **Feedback (Incorrect):** Documentation should include: alert details (what you saw), the decision you made, the rationale behind it, and any escalation or communication actions. Raw sensor logs are not required at the manager level. Omitting the rationale or communications leaves gaps for the next shift.
- **LO Alignment:** LO5

---

## Assessment Alignment Matrix

| Learning Outcome | Formative Questions | Summative Questions | Total Coverage |
|---|---|---|---|
| LO1 — Describe dashboard and data origins | F1.1, F1.2 | — | 2 |
| LO2 — Identify and differentiate dashboard elements | F2.1, F2.2 | S1 | 3 |
| LO3 — Interpret predictive alerts | F3.1, F3.2 | S1, S2 | 4 |
| LO4 — Evaluate AI recommendations | F4.1, F4.2 | S3 | 3 |
| LO5 — Demonstrate complete decision workflow | F4.2 | S3, S4 | 3 |

## Scoring

- **Formative questions:** Not scored toward final grade; provide immediate feedback for learning reinforcement.
- **Summative capstone:** 4 questions, each worth 25%. Passing threshold: 80% (minimum 3 of 4 correct).
- **Remediation:** Learners scoring below 80% are directed to review relevant module content and retake the capstone.