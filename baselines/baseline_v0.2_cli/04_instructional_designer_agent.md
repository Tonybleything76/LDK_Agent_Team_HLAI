# Instructional Design Content Script
## AI Adoption for Operations Managers

---

## Module 1: Understanding Your AI Dashboard
**Duration:** ~10 minutes | **Outcome:** LO1

**Module Hook (on-screen text or voiceover):**
> It's 6:02 AM. You walk onto the floor, coffee in hand. Before you check in with your team, there's a screen showing you exactly what happened overnight — and what's about to happen next. But only if you know how to read it.

---

### Lesson m1.1 — What You're Looking At
**Type:** Interactive annotated screenshot

**Screen 1: Introduction**
- **Voiceover/Text:** "This is your AI dashboard. It pulls together everything happening across your production lines into one screen. Instead of checking three different reports or walking the floor to get a status update, you get it here — updated, organized, and current."
- **Visual:** Full AI dashboard screenshot with all panels visible but not yet labeled. Dashboard appears slightly blurred, then sharpens as narration begins.
- **Interaction:** None (passive viewing).

**Screen 2: Three Panels Overview**
- **Voiceover/Text:** "The dashboard has three main areas, and each one answers a different question you ask every shift:
  1. **Performance Trends Panel** — 'How has production been running?'
  2. **Predictive Alerts Panel** — 'What might happen next?'
  3. **Throughput Indicators Panel** — 'Where are we right now against target?'
  
  Think of it this way: trends look back, alerts look forward, and throughput tells you right now."
- **Visual:** Dashboard screenshot with three panels highlighted sequentially (color-coded borders: blue for trends, amber for alerts, green for throughput). Each panel highlights as the corresponding text appears.
- **Interaction:** None (guided reveal).

**Screen 3: Practice Activity — Label the Dashboard**
- **Voiceover/Text:** "Let's see if you can identify them. Drag each label to the correct panel."
- **Visual:** Same dashboard screenshot, unlabeled. Three draggable labels: "Performance Trends," "Predictive Alerts," "Throughput Indicators."
- **Interaction:** Drag-and-drop. Learner places each label on the correct panel.
- **Feedback (correct):** "That's right. You've identified all three panels. Each one gives you a different piece of the operational picture."
- **Feedback (incorrect):** "Not quite. Remember: trends show direction over time (the graph), alerts flag what may happen next (the notification boxes), and throughput shows current output against target (the numbers)." Panels re-highlight with labels.

---

### Lesson m1.2 — Where the Data Comes From
**Type:** Short animated explainer + text summary

**Screen 1: The Source**
- **Voiceover/Text:** "One of the first questions experienced managers ask is: 'Where does this data actually come from?' Fair question. The answer: directly from production line sensors. Temperature, vibration, pressure, speed — your equipment is already generating this data. The dashboard collects it, organizes it, and refreshes every 5 minutes."
- **Visual:** Simple animation showing sensors on a production line transmitting data points upward into a dashboard interface. Visual flow: Sensor → Data stream → Dashboard panel. Timestamp shows '5-minute refresh' cycling.
- **Interaction:** None (animated explainer).

**Screen 2: Not a Guess**
- **Voiceover/Text:** "This is important: the numbers you see are not estimates. They are not someone's opinion. They are sensor readings from your actual machines, collected automatically. When the dashboard says throughput dropped on Line 3 at 02:14 AM, that's because the sensors on Line 3 recorded a drop at 02:14 AM."
- **Visual:** Text summary card:
  - ✓ Data from production line sensors
  - ✓ Updated every 5 minutes
  - ✓ Reflects actual machine conditions
  - ✗ Not manually entered
  - ✗ Not estimated or guessed
- **Interaction:** None.

**Screen 3: Practice Activity — Misconception Check**
- **Voiceover/Text:** "A colleague says: 'I don't trust that dashboard. The AI is just making things up.' Based on what you've learned, which response is most accurate?"
- **Visual:** Scenario card with colleague avatar and speech bubble.
- **Interaction:** Multiple choice.
  - A) "You're right — it's best to stick with manual reports." *(Incorrect)*
  - B) "Actually, the dashboard pulls directly from production line sensors and updates every 5 minutes. It's showing real machine data, not predictions." *(Correct)*
  - C) "The AI is very advanced, so we should trust everything it says without question." *(Incorrect — addresses over-trust)*
  - D) "I'm not sure — I think it might be a mix of sensor data and estimates." *(Incorrect)*
- **Feedback (B — correct):** "Exactly. The dashboard displays sensor data — not opinions, not guesses. That's what makes it a reliable starting point for your decisions."
- **Feedback (A — incorrect):** "Manual reports have their place, but the dashboard isn't making things up. It's pulling directly from production line sensors every 5 minutes."
- **Feedback (C — incorrect):** "The data is sensor-based and reliable, but that doesn't mean you should skip your own judgment. The dashboard informs your decisions — it doesn't make them for you."
- **Feedback (D — incorrect):** "There's no guesswork in the base data. The dashboard reads directly from sensors on your lines. It's actual machine data."

---

### Lesson m1.3 — Why This Matters to Your Shift
**Type:** Text + brief scenario vignette

**Screen 1: Before and After**
- **Voiceover/Text:** "Before the dashboard, getting a picture of overnight production meant reading handwritten logs, waiting for emailed reports, or walking every line. That takes time you don't always have at 6 AM.

  With the dashboard, you open one screen and see every line's status — what ran smoothly, what dipped, and whether anything needs your attention right now. Your judgment still drives every decision. The dashboard just gives that judgment better inputs, faster."
- **Visual:** Split screen. Left: 'Before' — manager holding clipboard, stack of papers, clock showing time passing. Right: 'After' — manager viewing dashboard on tablet, clock showing faster status check. No AI jargon. Clean, practical visual.
- **Interaction:** None.

**Screen 2: Quick Win Example**
- **Voiceover/Text:** "Here's one way it helps immediately: checking the overnight throughput trend at shift start. Instead of waiting for the morning report or asking the outgoing team, you pull up the dashboard and see whether throughput was stable, dropped, or climbed. That takes 30 seconds and tells you whether your shift is starting from a strong position or a deficit."
- **Visual:** Dashboard snippet showing an overnight throughput trend line with a clear downward slope in the last 2 hours of the previous shift. Annotation: 'Throughput declined 12% between 03:00 and 06:00.'
- **Interaction:** None.

**Screen 3: Reflection Prompt**
- **Voiceover/Text:** "Think about the first decision you typically make at the start of your shift. What's one data point from the dashboard that could inform that decision?"
- **Visual:** Open text box (optional response, not graded). Below: "Examples other managers have mentioned: overnight throughput trend, any active predictive alerts, current line status."
- **Interaction:** Optional free-text reflection (not scored). Learner can type or skip.
- **Transition text:** "Now that you know what the dashboard shows and where its data comes from, let's learn to read its three types of signals."

---

## Module 2: Reading the Signals
**Duration:** ~10 minutes | **Outcome:** LO2

**Module Hook (on-screen text or voiceover):**
> You check the dashboard. There's a green line trending upward, a yellow alert box, and a throughput number in red. Are any of these urgent? All of them? None? Let's make sure you know.

---

### Lesson m2.1 — Performance Trends: The Big Picture
**Type:** Interactive visual with annotated trend graph

**Screen 1: What Trends Show**
- **Voiceover/Text:** "Performance trends show production output over time. You can view the last 8 hours, last shift, or last 24 hours. The line tells you the direction: going up means output is increasing. Going down means it's declining. Flat means it's stable. The key skill here is recognizing what's normal for your line — and spotting when the trend moves outside that range."
- **Visual:** Annotated trend graph with three example lines: one upward, one downward, one flat. Each labeled with plain-language description. Normal range shown as a shaded band.
- **Interaction:** None (guided visual).

**Screen 2: Practice — Read the Graph**
- **Voiceover/Text:** "Look at each trend line below and classify it."
- **Visual:** Three separate mini-graphs shown side by side.
  - Graph A: Steady upward slope → "Improving"
  - Graph B: Sharp downward slope in last 2 hours → "Declining"
  - Graph C: Flat within normal range → "Stable"
- **Interaction:** Multiple choice per graph (Improving / Declining / Stable).
- **Feedback (all correct):** "Good reading. Trends give you the direction — the 'story so far.' Next, we'll look at what the dashboard says about what comes next."
- **Feedback (any incorrect):** Specific correction per graph with visual annotation.

---

### Lesson m2.2 — Predictive Alerts: What's Coming
**Type:** Text + side-by-side comparison visual

**Screen 1: Trends vs. Alerts**
- **Voiceover/Text:** "Performance trends tell you what has happened. Predictive alerts tell you what the data suggests will happen. That's the key difference. A trend says 'throughput dropped 10% over the last 4 hours.' An alert says 'based on sensor patterns, throughput is likely to drop further — potential machine fault within 2 hours.'

  Every predictive alert includes three elements:
  1. The **prediction** — what the system expects will happen
  2. The **basis** — the sensor data pattern that triggered it
  3. The **action window** — the time available for you to respond"
- **Visual:** Side-by-side comparison. Left column: 'Performance Trend' showing a graph with a downward line, labeled 'What happened.' Right column: 'Predictive Alert' showing an alert box with prediction, basis, and window, labeled 'What's coming.' Clear visual separation.
- **Interaction:** None.

**Screen 2: Terminology Reinforcement**
- **Voiceover/Text:** "Let's reinforce the language. A 'predictive alert' is a forward-looking, sensor-based signal. It's not a notification that something broke — it's a notification that sensor data patterns match conditions that typically precede a specific event. You'll see these alerts on your dashboard alongside trends and throughput data."
- **Visual:** Glossary-style card: **Predictive Alert** = A forward-looking signal generated from sensor data patterns that indicates a probable future event and a recommended response window.
- **Interaction:** None.

**Screen 3: Practice — Sort Exercise**
- **Voiceover/Text:** "Read each dashboard message below and sort it into the correct category: Performance Trend or Predictive Alert."
- **Visual:** Five dashboard messages as cards:
  1. "Line 1 output increased 8% over the last shift" → Trend
  2. "Sensor pattern on Line 3 suggests motor overheating within 90 minutes" → Alert
  3. "Throughput on Line 2 has been stable for 12 hours" → Trend
  4. "Vibration data on Line 4 indicates bearing wear — maintenance recommended within 4 hours" → Alert
  5. "Line 5 output dropped 15% between 01:00 and 05:00" → Trend
- **Interaction:** Drag each card into 'Trend' or 'Alert' column.
- **Feedback (all correct):** "Well sorted. You can clearly distinguish what's already happened from what the data says may happen next."
- **Feedback (incorrect):** Specific correction: "This message [quote] is a [correct type] because [it describes past output / it predicts a future event based on sensor patterns]."

---

### Lesson m2.3 — Throughput Indicators: The Numbers Right Now
**Type:** Interactive dashboard snippet with guided walkthrough

**Screen 1: Reading Throughput**
- **Voiceover/Text:** "Throughput indicators show you real-time output rates compared to target. They answer: 'Are we hitting our numbers right now?' Color coding makes this quick:
  - **Green** = at or above target
  - **Yellow** = approaching threshold — output is slipping
  - **Red** = below target

  These update every 5 minutes with the sensor refresh. Throughput tells you the current state. Combined with trends (direction) and alerts (future), you get the full picture."
- **Visual:** Dashboard snippet showing three lines with throughput indicators: Line 1 (Green, 102%), Line 2 (Yellow, 91%), Line 3 (Red, 78%). Target threshold labeled.
- **Interaction:** Guided — learner clicks each indicator to see explanation.

**Screen 2: Practice — Integrated Reading**
- **Voiceover/Text:** "You check the dashboard and see the following. Answer the questions below."
- **Visual:** Combined dashboard view showing:
  - Line 2 performance trend: declining over last 3 hours
  - Line 2 predictive alert: "Potential conveyor jam within 1 hour based on vibration sensor data"
  - Line 2 throughput: Yellow, 89%
- **Interaction:** Three questions:
  1. "What does the trend tell you?" → "Line 2 output has been declining for 3 hours" (select from options)
  2. "What does the alert predict?" → "A potential conveyor jam within 1 hour" (select from options)
  3. "What does the throughput indicator show?" → "Output is approaching the threshold — not yet critical but slipping" (select from options)
- **Feedback:** Per-question correction and reinforcement. Summary: "When trend, alert, and throughput all point in the same direction for the same line, that's a strong signal worth your attention."
- **Transition text:** "You can now read all three signal types. Next, we'll go deeper into predictive alerts — the signals managers most often misunderstand."

---

## Module 3: Interpreting Predictive Alerts
**Duration:** ~10 minutes | **Outcome:** LO3

**Module Hook (on-screen text or voiceover):**
> The dashboard just flagged a predictive alert: 'Throughput drop detected on Line 2. Predicted machine fault within 2 hours.' Your first instinct might be to dismiss it. Before you do — let's look at what's actually behind that alert.

---

### Lesson m3.1 — Anatomy of a Predictive Alert
**Type:** Annotated alert example with interactive callouts

**Screen 1: The Three Components**
- **Voiceover/Text:** "Every predictive alert on your dashboard has three parts. Once you know what to look for, you can read any alert in seconds.

  1. **The Prediction** — What the system expects to happen. Example: 'Machine fault on Line 2.'
  2. **The Confidence Basis** — The sensor data pattern that triggered the alert. Example: 'Vibration frequency on Line 2 motor matches pattern preceding bearing failure.'
  3. **The Action Window** — How long you have to respond. Example: 'Predicted within 2 hours.'"
- **Visual:** A large, realistic alert box from the dashboard with three sections color-highlighted and labeled. Callout arrows pointing to each section.
- **Interaction:** Learner clicks each highlighted area to expand the explanation.

**Screen 2: Worked Example**
- **Voiceover/Text:** "Let's walk through the SME scenario. The dashboard shows:

  *'Throughput drop detected on Line 2. Sensor pattern: declining throughput combined with elevated motor vibration. Predicted machine fault within 2 hours.'*

  - **Prediction:** Machine fault on Line 2
  - **Confidence Basis:** Declining throughput + elevated motor vibration (sensor data, not a guess)
  - **Action Window:** 2 hours

  This tells you: something is likely going wrong with Line 2 equipment, the sensors are showing a specific pattern that matches previous faults, and you have roughly 2 hours before the predicted failure."
- **Visual:** The alert deconstructed into three labeled rows matching the explanation. Original alert shown above, decomposition below.
- **Interaction:** None (worked example).

**Screen 3: Practice — Deconstruct a New Alert**
- **Voiceover/Text:** "Here's a new alert. Identify the three components."
- **Visual:** Alert: *"Line 4 — Pressure sensor readings trending abnormally. Pattern consistent with valve degradation. Maintenance recommended within 4 hours."*
- **Interaction:** Three dropdown/fill-in fields:
  1. Prediction: [Valve degradation on Line 4]
  2. Confidence Basis: [Abnormal pressure sensor readings matching valve degradation pattern]
  3. Action Window: [4 hours]
- **Feedback (correct):** "You've correctly broken down the alert. This structure is the same for every alert — prediction, basis, window."
- **Feedback (incorrect):** Specific correction pointing to the relevant part of the alert text.

---

### Lesson m3.2 — Why This Isn't a Guess
**Type:** Short explainer text + comparison table

**Screen 1: Addressing the Misconception**
- **Voiceover/Text:** "This is something we hear often: 'The AI is just guessing.' It's a reasonable concern if you don't know how the alerts work. So let's be direct about it.

  A guess has no evidence behind it. A predictive alert is triggered by a specific sensor data pattern — vibration, temperature, pressure, speed — that matches a pattern previously associated with a known event.

  Think of it like a check-engine light in your car. The light comes on because a sensor detected a specific reading. It's not guessing your engine might have a problem — it measured something. The dashboard works the same way."
- **Visual:** Comparison table:

  | | A Guess | A Sensor-Based Prediction |
  |---|---|---|
  | Based on | Intuition or random chance | Specific sensor data pattern |
  | Evidence | None | Measurable readings (vibration, temperature, pressure) |
  | Trigger | Nothing specific | Sensor pattern matching known fault conditions |
  | Track record | Unknown | Based on historical sensor-event correlations |
  | Analogy | "I have a feeling it might rain" | Check-engine light |

- **Interaction:** None.

**Screen 2: Setting Expectations**
- **Voiceover/Text:** "Does this mean every alert is correct? No. Sensor-based predictions are probabilistic — they're based on what sensor patterns have indicated in the past. But they are evidence-based and they give you a head start that waiting for a breakdown does not. The professional move is to evaluate them, not ignore them."
- **Visual:** Key takeaway card: "Predictive alerts are evidence-based, not infallible. Evaluate them — don't dismiss them, and don't follow them blindly."
- **Interaction:** None.

**Screen 3: Practice — Respond to a Skeptic**
- **Voiceover/Text:** "You're reviewing the dashboard with a colleague. They see a predictive alert and say: 'I've been running this floor for 20 years. I'm not going to change my plan because of some AI guess.' How would you respond?"
- **Visual:** Scenario card with colleague avatar.
- **Interaction:** Multiple choice:
  - A) "You're right, experience is more important than what the dashboard says." *(Incorrect — dismisses valid tool)*
  - B) "The alert is based on sensor readings — vibration and temperature data — not a guess. It doesn't replace your judgment, but it gives you a data point worth checking before it becomes a problem." *(Correct)*
  - C) "The AI is always right, so we should follow the alert." *(Incorrect — over-trust)*
  - D) "I ignore those alerts too — they're usually wrong." *(Incorrect — reinforces dismissal)*
- **Feedback (B — correct):** "Well put. You acknowledged the data basis without dismissing your colleague's experience. That's how trust in the tool gets built — through evidence, not arguments."
- **Feedback (others):** Specific correction explaining why the response undermines effective dashboard use.

---

### Lesson m3.3 — Acting Within the Window
**Type:** Decision scenario (branching)

**Screen 1: Window = Urgency**
- **Voiceover/Text:** "The action window in a predictive alert tells you how urgent your response needs to be. Here's a practical framework:

  - **Short window (under 1 hour):** This needs your attention now. Assess and act or escalate immediately.
  - **Medium window (1–4 hours):** You have time to plan a response within your shift. Don't ignore it — schedule the action.
  - **Long window (over 4 hours):** Monitor the situation and include it in your shift handoff notes if it extends beyond your shift.

  The key point: every window closes eventually. Ignoring an alert doesn't stop the clock — it just reduces your options."
- **Visual:** Three-tier urgency framework as a visual timeline/ladder. Red (< 1 hr), Yellow (1–4 hrs), Blue (> 4 hrs). Each with action keyword: Immediate / Plan / Monitor & Handoff.
- **Interaction:** None.

**Screen 2: Practice — Triage Three Alerts**
- **Voiceover/Text:** "You have three active alerts on your dashboard. Rank them by response urgency."
- **Visual:** Three alert cards:
  - Alert A: "Line 1 — Coolant flow anomaly detected. Predicted overheating within 45 minutes." → **Immediate**
  - Alert B: "Line 3 — Belt tension sensor pattern suggests slippage. Maintenance recommended within 6 hours." → **Monitor & Handoff**
  - Alert C: "Line 2 — Motor vibration elevated. Predicted bearing issue within 3 hours." → **Plan within shift**
- **Interaction:** Drag-and-rank or priority assignment.
- **Feedback (correct):** "Correct. Alert A demands immediate attention (45-minute window). Alert C should be planned for this shift (3-hour window). Alert B can be monitored and handed off (6-hour window). Prioritizing by action window ensures you address the most time-sensitive issues first."
- **Feedback (incorrect):** Per-item correction with window-based rationale.
- **Transition text:** "You can now read alerts, understand their evidence basis, and prioritize by urgency. In the final module, you'll put it all together into a decision workflow."

---

## Module 4: Making Data-Driven Decisions
**Duration:** ~15 minutes | **Outcomes:** LO4, LO5

**Module Hook (on-screen text or voiceover):**
> You've learned to read the dashboard and interpret its alerts. Now the question that matters most: What do you actually do with this information? This module puts you in the driver's seat.

---

### Lesson m4.1 — Evaluating AI Recommendations
**Type:** Text + guided framework + worked example

**Screen 1: You Decide — The Dashboard Informs**
- **Voiceover/Text:** "The dashboard may surface a recommendation alongside an alert — for example, 'Schedule maintenance on Line 2 motor.' That recommendation is based on data. But you make the decision. Here's a three-step evaluation you can use every time:

  **Step 1 — Assess the Data:** What is the alert telling you? What sensor pattern triggered it? How much time do you have?
  **Step 2 — Consider the Context:** What else is happening on the floor? Is Line 2 running a critical order? Are maintenance resources available? Does the recommendation fit your operational reality?
  **Step 3 — Decide: Act, Modify, or Escalate.**
  - **Act** = follow the recommendation as-is
  - **Modify** = adjust the recommendation based on your context (e.g., schedule maintenance for next break instead of immediately)
  - **Escalate** = pass the decision to someone with more authority or information"
- **Visual:** Three-step framework as a numbered flow diagram. Step 1 (Data) → Step 2 (Context) → Step 3 (Decision: Act / Modify / Escalate).
- **Interaction:** None.

**Screen 2: Worked Example**
- **Voiceover/Text:** "Let's apply the framework.

  *Alert: 'Throughput drop on Line 2. Elevated motor vibration. Predicted bearing fault within 2 hours. Recommendation: Schedule maintenance.'*

  **Step 1 — Data:** Motor vibration sensor triggered the alert. 2-hour window. Throughput already declining.
  **Step 2 — Context:** Line 2 is running a priority order due at end of shift. Pulling the line now means missing the deadline. A maintenance technician is available in 30 minutes.
  **Step 3 — Decision:** **Modify.** Don't pull the line immediately — schedule the technician to inspect in 30 minutes during a planned break window. Monitor throughput closely in the interim. Document the decision and rationale.

  Notice: the manager didn't blindly follow the recommendation, and didn't ignore it either. They used judgment informed by data."
- **Visual:** The three steps filled in with the worked example. Decision highlighted: 'Modify.' Rationale annotated.
- **Interaction:** None (guided example).

**Screen 3: Practice — Your Turn**
- **Voiceover/Text:** "Apply the three-step evaluation to this scenario."
- **Visual:** Alert: *"Line 5 — Temperature sensor readings elevated on packaging unit. Predicted seal failure within 90 minutes. Recommendation: Halt packaging line and inspect."*
  Context provided: Line 5 is the only active packaging line. Halting it stops all outbound shipments. A backup unit can be brought online in 20 minutes.
- **Interaction:** Three-part structured response:
  1. Step 1 — What does the data say? (select from options)
  2. Step 2 — What context matters? (select from options)
  3. Step 3 — Your decision: Act / Modify / Escalate? (select + brief rationale from options)
- **Feedback:** Step-by-step evaluation. Model answer: **Modify** — begin bringing backup unit online immediately; halt Line 5 for inspection once backup is operational (within 20 minutes, well inside 90-minute window). Document rationale.

---

### Lesson m4.2 — When to Escalate
**Type:** Decision table + scenario

**Screen 1: Escalation Criteria**
- **Voiceover/Text:** "Escalation is a professional decision, not a failure. You escalate when the situation exceeds your authority, information, or the risk level is too high to act alone. Here are the conditions:

  - **Safety risk** — any alert suggesting personnel safety concern
  - **Exceeds your authority** — decision requires capital expenditure or production shutdown beyond your approval level
  - **Converging alerts** — multiple alerts on the same line or across lines suggesting a systemic issue
  - **Insufficient time** — the window is too short to evaluate properly and act safely

  When escalating, include: the alert details, your initial assessment, what you recommend, and the time remaining in the action window."
- **Visual:** Decision table with four escalation criteria in rows. Columns: Condition | Example | What to Include When Escalating.
- **Interaction:** None.

**Screen 2: Practice — Act or Escalate?**
- **Voiceover/Text:** "For each scenario, decide: act on your own or escalate?"
- **Visual:** Two scenario cards:
  - **Scenario A:** "Line 3 — Predictive alert: bearing fault within 3 hours. You have a maintenance technician available. Line 3 is running a standard (non-priority) order."
  - **Scenario B:** "Lines 1 and 3 both show predictive alerts within the same hour. Line 1: motor overheating (45-minute window). Line 3: conveyor jam (60-minute window). You don't have two available technicians."
- **Interaction:** Per scenario: select Act or Escalate + select rationale.
- **Feedback:**
  - Scenario A: **Act.** You have the resources, time, and authority. Standard protocol.
  - Scenario B: **Escalate.** Converging alerts with insufficient resources. Escalate to get a second technician or prioritization guidance. Include both alert details and time windows.

---

### Lesson m4.3 — The Complete Decision Workflow
**Type:** Interactive walkthrough + workflow summary graphic

**Screen 1: Four Steps**
- **Voiceover/Text:** "Let's bring everything together into a repeatable workflow you can use every shift:

  1. **Consult** — Open the dashboard. Review trends, alerts, and throughput for your lines.
  2. **Interpret** — Read the signals. What's the direction? Any alerts? What do they predict and how much time do you have?
  3. **Decide** — Assess the data, consider your context, and choose: act, modify, or escalate.
  4. **Document** — Record what you saw, what you decided, and why. This protects you and helps the next shift.

  This isn't extra work — it replaces the time you'd spend gathering information manually. And it becomes faster every time you do it."
- **Visual:** Four-step horizontal workflow graphic: Consult → Interpret → Decide → Document. Each step has an icon and one-line description. Below: 'When to use this workflow: shift start, before production adjustments, when alerts appear, post-incident review.'
- **Interaction:** Learner clicks each step to review a one-sentence recap.

**Screen 2: Habit Formation**
- **Voiceover/Text:** "The goal isn't to memorize steps — it's to build a habit. The more you consult the dashboard and work through this process, the faster and more natural it becomes. Within a few shifts, it won't feel like extra work. It'll feel like having better information."
- **Visual:** Summary card: "Consult. Interpret. Decide. Document. — Every shift, every alert, every adjustment."
- **Interaction:** None.
- **Transition text:** "Now let's put everything to the test. The next screen is your capstone scenario — a realistic shift situation where you'll demonstrate the full workflow."

---

### Lesson m4.4 — Capstone: Your Shift, Your Call
**Type:** Summative scenario-based assessment (interactive simulation)

**Screen 1: Scenario Setup**
- **Voiceover/Text:** "It's the start of your shift. You open the AI dashboard and see the following for Line 4:

  - **Performance Trend:** Throughput declining steadily over the last 4 hours
  - **Predictive Alert:** 'Motor overheating detected. Sensor data: elevated temperature and vibration. Predicted motor failure within 90 minutes.'
  - **Throughput Indicator:** 78% of target (Red)

  Your line supervisor tells you Line 4 is running a priority order due in 3 hours. A maintenance technician is available."
- **Visual:** Simulated dashboard view for Line 4 with all three panels populated. Context box: 'Priority order — due in 3 hours. Technician available.'
- **Interaction:** None (setup).

**Screen 2: Question 1 — Identify the Most Critical Signal**
- **Voiceover/Text:** "Which dashboard signal requires your most immediate attention?"
- **Interaction:** Multiple choice:
  - A) Performance trend (declining throughput) *(Incorrect — trend is important context but not the most urgent)*
  - B) Predictive alert (motor failure within 90 minutes) *(Correct — shortest action window, highest consequence)*
  - C) Throughput indicator (78%, red) *(Incorrect — current status, but the alert explains why and what's coming)*
- **Feedback (B — correct):** "Right. The predictive alert has the shortest action window and the highest potential consequence. The trend and throughput provide context, but the alert drives urgency."

**Screen 3: Question 2 — Interpret the Alert**
- **Voiceover/Text:** "Break down the predictive alert into its three components."
- **Interaction:** Three fields (select from options):
  1. Prediction: [Motor failure on Line 4]
  2. Confidence Basis: [Elevated temperature and vibration sensor data]
  3. Action Window: [90 minutes]
- **Feedback:** Per-component correction if needed.

**Screen 4: Question 3 — Evaluate the Recommendation**
- **Voiceover/Text:** "Using the three-step evaluation: what is your decision?"
- **Visual:** Reminder of framework: Assess Data → Consider Context → Decide.
- **Interaction:** Structured:
  - Context consideration (select key factors): Priority order due in 3 hours / Technician available / 90-minute window
  - Decision: Act / Modify / Escalate
  - Rationale selection (choose best rationale from options)
- **Model answer:** **Modify.** Dispatch the available technician to inspect Line 4 motor immediately. If inspection confirms risk, schedule maintenance during a brief planned stoppage rather than full line halt — balancing the priority order against the 90-minute failure window. Document decision and rationale. If motor condition is worse than expected, escalate for potential order reassignment.

**Screen 5: Question 4 — Document Your Rationale**
- **Voiceover/Text:** "What would you include in your shift documentation?"
- **Interaction:** Select all that apply:
  - ✓ Alert details (motor overheating, 90-minute window)
  - ✓ Decision made (modify — dispatch technician, monitor, planned stoppage if needed)
  - ✓ Rationale (priority order constraint, technician availability, 90-minute window allows planned response)
  - ✓ Escalation plan if condition worsens
  - ✗ Detailed sensor data logs (not required at manager level)
- **Feedback:** "Complete documentation includes the alert, your decision, your rationale, and your contingency. This protects your decision trail and gives the next shift the information they need."

**Screen 6: Results & Course Completion**
- **Voiceover/Text:** "Here are your results. [Score displayed.]

  You've completed *AI Adoption for Operations Managers.* Here's what you can now do:
  - Read and navigate the AI dashboard
  - Distinguish trends, alerts, and throughput indicators
  - Interpret predictive alerts using their three components
  - Evaluate AI recommendations with a structured framework
  - Execute a complete decision workflow: consult, interpret, decide, document

  The dashboard is a tool. Your judgment is what makes it valuable. Use both — every shift."
- **Visual:** Score card + summary of outcomes achieved. Course completion badge/confirmation.
- **Interaction:** None. Link to retake if below 80%.

---

## Design Notes

- **Tone:** Professional, respectful of operational expertise, direct. No jargon beyond defined terms. No condescension.
- **Persona calibration:** Content addresses Veteran (trust-building, experience-respecting language), Pragmatist (concise, immediate value), and Adopter (evaluation cautions against over-trust).
- **Compliance:** No export of sensitive data referenced; all scenarios use generalized production data.
- **Device:** All interactions designed for desktop and tablet. Drag-and-drop interactions include tap-and-select fallback for tablet.
- **Duration budget:** M1 ~10 min, M2 ~10 min, M3 ~10 min, M4 ~15 min = ~45 min total.