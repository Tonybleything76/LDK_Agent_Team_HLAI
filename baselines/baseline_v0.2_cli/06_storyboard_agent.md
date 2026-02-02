# Visual Storyboard — AI Adoption for Operations Managers

## Design System

| Element | Specification |
|---|---|
| Color Palette | Blue (#1565C0) — Performance Trends; Amber (#F9A825) — Predictive Alerts; Green (#2E7D32) — Throughput; Red (#C62828) — Below Target; Dark Gray (#263238) — Text; White (#FFFFFF) — Background |
| Typography | Headings: 20px semi-bold sans-serif; Body: 16px regular sans-serif; Dashboard labels: 14px medium monospace |
| Layout Grid | 12-column responsive; desktop 1280px max-width; tablet 768px min-width |
| Iconography | Material Design icon set; line-weight 2px; 24px default size |
| Interaction States | Default, Hover (#E3F2FD), Active (#1565C0), Correct (#2E7D32), Incorrect (#C62828) |

---

## Module 1 — Understanding Your AI Dashboard

### Screen m1.1.s1 — Introduction to the AI Dashboard

| Attribute | Specification |
|---|---|
| **Layout** | Full-width single panel. Dashboard screenshot centered at 90% container width. Text overlay fades in at bottom-left. |
| **Media Asset** | `img/m1/dashboard_full_blur.png` — Full AI dashboard screenshot. Initial state: Gaussian blur (radius 8px). Transition: blur dissolves to sharp over 1.5s on screen entry. |
| **Alt Text** | "Full view of the AI production dashboard showing performance trends, predictive alerts, and throughput indicators panels before labels are applied." |
| **Dev Notes** | Apply CSS blur filter on load; animate to `filter: blur(0)` over 1.5s ease-out on viewport entry. Text content fades in (opacity 0→1, 0.8s) after blur clears. Ensure dashboard image is responsive — use `object-fit: contain` for tablet. |

### Screen m1.1.s2 — Three Panels Overview

| Attribute | Specification |
|---|---|
| **Layout** | Full-width dashboard screenshot with sequential highlight overlays. Three color-coded border overlays appear one at a time (blue, amber, green). Corresponding text block appears below each highlighted panel. |
| **Media Asset** | `img/m1/dashboard_three_panels.png` — Same dashboard screenshot. Three SVG overlay borders: `overlay_trends_blue.svg`, `overlay_alerts_amber.svg`, `overlay_throughput_green.svg`. |
| **Alt Text** | "AI dashboard with three panels highlighted sequentially: Performance Trends panel outlined in blue, Predictive Alerts panel outlined in amber, and Throughput Indicators panel outlined in green." |
| **Dev Notes** | Guided reveal: each panel border + text block appears on user scroll or click/tap of 'Next' button. Sequence: (1) Blue border + trends text, (2) Amber border + alerts text, (3) Green border + throughput text. All three remain visible after reveal. Tablet: stack text blocks below image. Transition: border stroke-dashoffset animation 0.6s. |

### Screen m1.1.s3 — Label the Dashboard

| Attribute | Specification |
|---|---|
| **Layout** | Two-zone layout. Left (60%): unlabeled dashboard screenshot with three drop-target hotspots. Right (40%): three draggable label chips stacked vertically. |
| **Media Asset** | `img/m1/dashboard_unlabeled.png` — Dashboard with panels visible but no text labels. Three label chips as styled `<div>` elements: "Performance Trends", "Predictive Alerts", "Throughput Indicators". |
| **Alt Text** | "Interactive drag-and-drop exercise. Three labels — Performance Trends, Predictive Alerts, and Throughput Indicators — must be placed on the correct dashboard panel." |
| **Dev Notes** | Use HTML5 Drag and Drop API with touch fallback (e.g., SortableJS). Drop zones: defined as percentage-based regions over the image. Correct placement: green check animation + label locks in place. Incorrect: red shake animation (0.3s) + label returns to origin. Tablet: larger touch targets (min 48x48px). Show 'Try Again' on incorrect. After all three correct, show summary feedback below. |

### Screen m1.2.s1 — The Source of Dashboard Data

| Attribute | Specification |
|---|---|
| **Layout** | Full-width animated explainer panel. Three-stage horizontal flow: Sensor → Data Stream → Dashboard. Text content below animation area. |
| **Media Asset** | `anim/m1/sensor_to_dashboard.json` (Lottie animation) — Simplified production line with sensor icons (thermometer, vibration wave, pressure gauge, speedometer) emitting data particles that flow upward into a dashboard wireframe. Timestamp counter cycles through "Last updated: XX:XX" every 5 seconds in the animation. |
| **Alt Text** | "Animation showing production line sensors collecting temperature, vibration, pressure, and speed data, which flows into the AI dashboard and refreshes every 5 minutes." |
| **Dev Notes** | Use Lottie-web for animation playback. Autoplay on viewport entry; loop the 5-minute refresh cycle indicator. Fallback for reduced-motion preference: static three-panel infographic (`img/m1/sensor_flow_static.png`). Tablet: scale animation to 100% width, reduce particle count for performance. |

### Screen m1.2.s2 — Not a Guess — Sensor Data

| Attribute | Specification |
|---|---|
| **Layout** | Centered card (max-width 680px). Checklist format with check (✓) and cross (✗) items. |
| **Media Asset** | Icon: `icon/check_circle_green.svg` for ✓ items; `icon/cancel_red.svg` for ✗ items. Card background: light gray (#F5F5F5), rounded corners 8px, subtle drop shadow. |
| **Alt Text** | "Summary card showing five facts about dashboard data: three confirmed true (sensor-sourced, 5-minute updates, reflects actual conditions) and two confirmed false (not manually entered, not estimated or guessed)." |
| **Dev Notes** | Stagger item entrance: each line fades in sequentially (0.3s delay per item) on viewport entry. Green check items first, then red cross items. Static on tablet — no animation if `prefers-reduced-motion`. |

### Screen m1.2.s3 — Misconception Check

| Attribute | Specification |
|---|---|
| **Layout** | Scenario card layout. Top: colleague avatar (left) with speech bubble (right). Below: four radio-button multiple-choice options. Bottom: feedback panel (hidden until answer submitted). |
| **Media Asset** | `img/m1/avatar_colleague_a.svg` — Neutral factory-floor colleague avatar (hardhat, high-vis vest). Speech bubble styled with gray background and left-pointing triangle. |
| **Alt Text** | "A colleague in factory safety gear says: 'I don't trust that dashboard. The AI is just making things up.' Four response options are displayed below." |
| **Dev Notes** | Radio button selection + 'Submit' button. Disable options after submit. Correct answer (B): green highlight + feedback panel slides in from bottom. Incorrect: red highlight on selected + correct answer highlighted green + corrective feedback. Tablet: full-width card, options stack vertically with 48px min touch targets. |

### Screen m1.3.s1 — Before and After the Dashboard

| Attribute | Specification |
|---|---|
| **Layout** | Split screen — 50/50 horizontal. Left: "Before" panel (muted/desaturated palette). Right: "After" panel (full-color palette). Divider line with label "Before | After". |
| **Media Asset** | Left: `img/m1/before_clipboard.svg` — Illustrated manager with clipboard, paper stack, analog clock showing extended time. Right: `img/m1/after_tablet.svg` — Same manager viewing dashboard on tablet, clock showing quick check. |
| **Alt Text** | "Split-screen comparison. Left side labeled 'Before': manager holding clipboard with stack of papers and a clock indicating time-consuming manual checks. Right side labeled 'After': same manager viewing AI dashboard on a tablet with a clock indicating a faster status check." |
| **Dev Notes** | On scroll/entry: left panel slides in from left, right panel slides in from right (0.6s ease-out). Divider line draws vertically (0.4s). Tablet: stack vertically — Before on top, After below, with horizontal divider. |

### Screen m1.3.s2 — Quick Win — Overnight Throughput

| Attribute | Specification |
|---|---|
| **Layout** | Dashboard snippet (60% width centered) with annotation callout. Text content below. |
| **Media Asset** | `img/m1/overnight_throughput_snippet.png` — Dashboard trend line showing clear downward slope in last 2 hours. Annotation arrow pointing to slope with label: "Throughput declined 12% between 03:00 and 06:00". |
| **Alt Text** | "Dashboard snippet showing an overnight throughput trend line with a downward slope in the final two hours. An annotation reads: Throughput declined 12 percent between 03:00 and 06:00." |
| **Dev Notes** | Annotation appears after 1s delay (fade in + arrow draws). Static on reduced-motion. Image responsive — `max-width: 100%` on tablet. |

### Screen m1.3.s3 — Reflection — Your First Shift Decision

| Attribute | Specification |
|---|---|
| **Layout** | Reflection prompt card (centered, max-width 640px). Open text area (optional, not graded). Below: expandable "Examples from other managers" section. |
| **Media Asset** | Icon: `icon/lightbulb_outline.svg` — Reflection prompt indicator. Text area with placeholder text. Expandable section with chevron toggle. |
| **Alt Text** | "Reflection prompt asking: Think about the first decision you typically make at the start of your shift. What is one data point from the dashboard that could inform that decision? An optional text box is provided. Examples from other managers are available below." |
| **Dev Notes** | Text area: 4-row minimum height, autogrow. No validation — purely reflective. 'Examples' section: collapsed by default, click/tap chevron to expand. Response stored locally (sessionStorage) but not submitted to server. Tablet: full-width card. |

---

## Module 2 — Reading the Signals

### Screen m2.1.s1 — What Performance Trends Show

| Attribute | Specification |
|---|---|
| **Layout** | Top: annotated trend graph (70% width). Right sidebar: legend with three line types. Bottom: text content. Shaded normal-range band on graph. |
| **Media Asset** | `img/m2/trend_graph_annotated.svg` — Trend graph with three example lines: upward (green), downward (red), flat (gray). Normal range shown as semi-transparent blue band. Annotations: "Increasing", "Declining", "Stable" with arrows. |
| **Alt Text** | "Annotated performance trend graph showing three example lines: an upward green line labeled Increasing, a downward red line labeled Declining, and a flat gray line labeled Stable. A shaded band indicates the normal output range." |
| **Dev Notes** | Graph rendered as SVG for scalability. Lines draw sequentially (stroke-dashoffset animation, 1s per line). Annotations fade in after corresponding line completes. Normal range band fades in last. Tablet: legend moves below graph, full-width. |

### Screen m2.1.s2 — Read the Graph Exercise

| Attribute | Specification |
|---|---|
| **Layout** | Three mini-graphs side by side (33% each on desktop). Below each graph: three-option radio group (Improving / Declining / Stable). Submit button at bottom. |
| **Media Asset** | `img/m2/mini_graph_a.svg` — Steady upward slope. `img/m2/mini_graph_b.svg` — Sharp downward slope in last 2 hours. `img/m2/mini_graph_c.svg` — Flat line within normal range band. |
| **Alt Text** | "Three mini trend graphs for classification exercise. Graph A shows a steady upward slope. Graph B shows a sharp decline in the last two hours. Graph C shows a flat line within the normal range." |
| **Dev Notes** | Independent scoring per graph. Correct: graph border turns green, checkmark appears. Incorrect: graph border turns red, correct answer revealed below. All three must be answered before submit is active. Tablet: stack graphs vertically, full-width each. |

### Screen m2.2.s1 — Trends vs. Alerts Comparison

| Attribute | Specification |
|---|---|
| **Layout** | Side-by-side comparison (50/50). Left panel: "What happened" — trend graph with blue header bar. Right panel: "What's coming" — alert box with amber header bar. Divider between panels. |
| **Media Asset** | Left: `img/m2/trend_example.svg` — Performance trend graph with historical data. Label: "Performance Trend — What happened." Right: `img/m2/alert_example.svg` — Alert box with prediction, basis, and action window fields. Label: "Predictive Alert — What's coming." |
| **Alt Text** | "Side-by-side comparison. Left panel labeled 'What happened' shows a performance trend graph. Right panel labeled 'What's coming' shows a predictive alert box with prediction, basis, and action window." |
| **Dev Notes** | Panels slide in from respective sides (left from left, right from right) 0.5s ease-out. Tablet: stack vertically with horizontal divider. |

### Screen m2.2.s2 — Terminology — Predictive Alert

| Attribute | Specification |
|---|---|
| **Layout** | Glossary card centered (max-width 600px). Term in large bold text at top. Definition in body text. Amber left border accent (4px). |
| **Media Asset** | Icon: `icon/alert_amber.svg` — Amber alert icon at top-left of card. Card background: warm gray (#FFF8E1). |
| **Alt Text** | "Glossary card defining Predictive Alert: A forward-looking signal generated from sensor data patterns indicating a probable future event and recommended response window." |
| **Dev Notes** | Static content — no interaction. Card entrance: fade in + slight upward slide (translateY 10px → 0). Tablet: full-width with 16px horizontal margin. |

### Screen m2.2.s3 — Sort — Trend or Alert?

| Attribute | Specification |
|---|---|
| **Layout** | Two-column sort area at top ("Performance Trend" column left, "Predictive Alert" column right). Five draggable message cards in a stack below. |
| **Media Asset** | Five message card `<div>` elements with dashboard-style text. Column headers with blue (Trend) and amber (Alert) backgrounds. Drop zones highlighted on drag hover. |
| **Alt Text** | "Interactive sorting exercise with five dashboard message cards. Each card must be dragged into either the Performance Trend column or the Predictive Alert column." |
| **Dev Notes** | Drag-and-drop with touch support (SortableJS). Cards snap into column on drop. Per-card feedback on placement: correct = green border + rationale tooltip; incorrect = red border + shake + rationale. 'Reset' button available. Tablet: columns stack as top/bottom drop zones; cards as horizontal scrollable list. Min touch target 48px. |

### Screen m2.3.s1 — Reading Throughput Indicators

| Attribute | Specification |
|---|---|
| **Layout** | Dashboard snippet centered showing three production lines. Each line is a clickable/tappable card with color-coded throughput indicator. Expanded explanation panel appears on click. |
| **Media Asset** | `img/m2/throughput_three_lines.svg` — Three line cards: Line 1 (Green, 102%), Line 2 (Yellow, 91%), Line 3 (Red, 78%). Target threshold line at 90%. |
| **Alt Text** | "Dashboard snippet showing three production line throughput indicators. Line 1: green at 102 percent (above target). Line 2: yellow at 91 percent (approaching threshold). Line 3: red at 78 percent (below target). A target threshold line is marked at 90 percent." |
| **Dev Notes** | Click-to-reveal: each card expands to show explanation text below it. Only one expanded at a time (accordion behavior). Tablet: cards stack vertically, full-width. Hover state on desktop (slight elevation change). |

### Screen m2.3.s2 — Integrated Dashboard Reading

| Attribute | Specification |
|---|---|
| **Layout** | Top: combined dashboard view for Line 2 (trend + alert + throughput). Below: three sequential multiple-choice questions with per-question feedback. |
| **Media Asset** | `img/m2/line2_combined_dashboard.png` — Line 2 dashboard with declining 3-hour trend, conveyor jam alert (1-hour window), throughput 89% yellow. |
| **Alt Text** | "Combined dashboard view for Line 2 showing a declining performance trend over 3 hours, a predictive alert for conveyor jam within 1 hour, and throughput at 89 percent in yellow. Three questions follow." |
| **Dev Notes** | Progressive disclosure: Question 2 appears after Question 1 answered. Question 3 after Question 2. Dashboard image remains pinned/sticky at top during scroll on desktop. Tablet: image scrolls with content, questions full-width. Per-question submit + feedback before next question appears. |

---

## Module 3 — Interpreting Predictive Alerts

### Screen m3.1.s1 — Three Components of an Alert

| Attribute | Specification |
|---|---|
| **Layout** | Large alert box centered (max-width 720px). Three sections within the alert highlighted with color-coded backgrounds. Callout arrows to each section. Click each to expand explanation. |
| **Media Asset** | `img/m3/alert_anatomy.svg` — Realistic alert box with: Prediction section (red-tinted background), Confidence Basis section (blue-tinted background), Action Window section (amber-tinted background). Three callout arrow SVGs. |
| **Alt Text** | "Large predictive alert box with three highlighted sections: Prediction highlighted in red, Confidence Basis highlighted in blue, and Action Window highlighted in amber. Each section can be clicked to reveal a detailed explanation." |
| **Dev Notes** | Click-to-reveal on each section: expand inline explanation below the section. Callout arrows animate (draw) on section hover/focus. All three must be opened before 'Continue' button activates (gating). Tablet: callout arrows replaced with numbered badges; tap to expand. |

### Screen m3.1.s2 — Worked Example — SME Scenario

| Attribute | Specification |
|---|---|
| **Layout** | Two-tier. Top: original alert text in styled alert box. Bottom: three-row decomposition table mapping alert text to components. Connecting lines between alert text and table rows. |
| **Media Asset** | `img/m3/sme_alert_decomposition.svg` — Alert box top, decomposition table below. Connecting dotted lines from alert phrases to corresponding component rows. Row colors match component coding (red, blue, amber). |
| **Alt Text** | "Worked example showing the SME scenario alert — throughput drop on Line 2 with predicted machine fault within 2 hours — decomposed into three labeled components: Prediction (machine fault), Confidence Basis (declining throughput and elevated motor vibration), and Action Window (2 hours)." |
| **Dev Notes** | Connecting lines draw sequentially (0.5s each) on viewport entry. Table rows highlight as corresponding line draws. Static fallback for reduced-motion. Tablet: hide connecting lines; use numbered badges matching alert text highlights to table rows. |

### Screen m3.1.s3 — Deconstruct a New Alert

| Attribute | Specification |
|---|---|
| **Layout** | Top: new alert card. Below: three labeled input fields (Prediction, Confidence Basis, Action Window) as dropdown selects or short text fills. Submit button. Feedback panel. |
| **Media Asset** | Alert card styled consistently with previous screens. Three input fields with labels matching component colors. |
| **Alt Text** | "Interactive exercise. A new alert reads: Line 4, pressure sensor readings trending abnormally, pattern consistent with valve degradation, maintenance recommended within 4 hours. Three fields ask the learner to identify the prediction, confidence basis, and action window." |
| **Dev Notes** | Dropdown select with predefined options for each field (reduces free-text validation complexity). Submit triggers per-field feedback: correct = green border, incorrect = red border + correct answer shown. All three must be correct or reviewed before Continue. Tablet: fields stack vertically, full-width dropdowns. |

### Screen m3.2.s1 — Addressing the 'AI Is Guessing' Misconception

| Attribute | Specification |
|---|---|
| **Layout** | Centered comparison table (max-width 700px). Two columns: "A Guess" vs. "A Sensor-Based Prediction". Five rows comparing dimensions. Check-engine light analogy callout below table. |
| **Media Asset** | `img/m3/guess_vs_prediction_table.svg` — Styled comparison table. Left column (gray/muted). Right column (green/confident). Below: `icon/car_engine_light.svg` — check-engine light icon with analogy text. |
| **Alt Text** | "Comparison table with five rows contrasting a guess (no evidence basis, no trigger, no track record) versus a sensor-based prediction (specific sensor patterns, data trigger, historical pattern matching). Below the table, a check-engine light analogy explains how sensor readings trigger known patterns." |
| **Dev Notes** | Table rows fade in sequentially (0.2s stagger). Analogy callout appears after table completes. Tablet: table scrolls horizontally if needed; analogy card full-width below. |

### Screen m3.2.s2 — Setting Expectations

| Attribute | Specification |
|---|---|
| **Layout** | Centered key-takeaway card (max-width 600px). Bold statement with amber accent border (left 4px). |
| **Media Asset** | Icon: `icon/info_amber.svg`. Card background: light amber (#FFF8E1). |
| **Alt Text** | "Key takeaway card reading: Predictive alerts are evidence-based, not infallible. Evaluate them — do not dismiss them, and do not follow them blindly." |
| **Dev Notes** | Static card. Entrance: fade-in + subtle scale (0.98→1.0, 0.4s). Tablet: full-width with 16px margin. |

### Screen m3.2.s3 — Respond to a Skeptical Colleague

| Attribute | Specification |
|---|---|
| **Layout** | Scenario card. Top: colleague avatar (left) + speech bubble (right). Below: four radio-button options. Bottom: feedback panel. |
| **Media Asset** | `img/m3/avatar_veteran_manager.svg` — Experienced manager avatar (hardhat, crossed arms, skeptical expression). Speech bubble with gray background. |
| **Alt Text** | "A veteran manager with crossed arms says: 'I've been running this floor for 20 years. I'm not going to change my plan because of some AI guess.' Four response options are displayed below." |
| **Dev Notes** | Same interaction pattern as m1.2.s3. Correct answer acknowledges experience AND explains sensor basis. Tablet: full-width, stacked options, 48px touch targets. |

### Screen m3.3.s1 — Action Window Urgency Framework

| Attribute | Specification |
|---|---|
| **Layout** | Horizontal timeline graphic (full width). Three color-coded zones along timeline. Labels above each zone. Summary text below. |
| **Media Asset** | `img/m3/urgency_timeline.svg` — Horizontal timeline bar: Red zone (< 1 hr, "Immediate Attention"), Yellow zone (1–4 hrs, "Plan Within Shift"), Blue zone (> 4 hrs, "Monitor & Handoff"). Clock icons at zone boundaries. |
| **Alt Text** | "Urgency framework timeline with three zones. Red zone (under 1 hour): Immediate Attention. Yellow zone (1 to 4 hours): Plan Within Shift. Blue zone (over 4 hours): Monitor and Handoff." |
| **Dev Notes** | Timeline draws left to right (1.2s total). Zone labels fade in after corresponding zone draws. Tablet: timeline stacks vertically as three cards (Red → Yellow → Blue) instead of horizontal bar. |

### Screen m3.3.s2 — Triage Three Alerts

| Attribute | Specification |
|---|---|
| **Layout** | Three alert cards in a draggable stack. Ranking area with three numbered slots (1 = Most Urgent, 3 = Least Urgent). |
| **Media Asset** | Three alert cards styled with respective urgency colors: Alert A (Red — 45 min), Alert B (Blue — 6 hrs), Alert C (Yellow — 3 hrs). Numbered ranking slots with drop zones. |
| **Alt Text** | "Three alert cards to rank by urgency. Alert A: coolant flow anomaly, overheating within 45 minutes. Alert B: belt tension, slippage within 6 hours. Alert C: motor vibration, bearing issue within 3 hours. Drag cards to rank from most urgent (1) to least urgent (3)." |
| **Dev Notes** | Drag-and-rank interaction (SortableJS). Cards snap into numbered slots. Submit button. Correct order: A→C→B. Feedback: correct order highlighted with checkmarks; incorrect items shown with correct position. Tablet: tap-to-select numbered priority (1/2/3) on each card instead of drag. |

---

## Module 4 — Making Data-Driven Decisions

### Screen m4.1.s1 — Three-Step Evaluation Framework

| Attribute | Specification |
|---|---|
| **Layout** | Horizontal three-step flow diagram centered. Each step is a rounded-rectangle node connected by arrows. Step labels above, one-line descriptions below. |
| **Media Asset** | `img/m4/three_step_framework.svg` — Flow: Step 1 (Blue, "Assess the Data", data icon) → Step 2 (Amber, "Consider the Context", context icon) → Step 3 (Green, "Decide", with three sub-options: Act / Modify / Escalate). |
| **Alt Text** | "Three-step evaluation framework flow diagram. Step 1: Assess the Data. Step 2: Consider the Context. Step 3: Decide — with three options: Act, Modify, or Escalate." |
| **Dev Notes** | Nodes draw sequentially (0.4s each, 0.2s gap). Arrows animate between nodes. Step 3 sub-options fan out from the Decide node. Tablet: vertical flow (top-to-bottom) instead of horizontal. |

### Screen m4.1.s2 — Worked Example — Evaluate and Decide

| Attribute | Specification |
|---|---|
| **Layout** | Three-row framework populated with worked example. Step 3 "Modify" highlighted with green border. Rationale annotation on the right. |
| **Media Asset** | `img/m4/worked_example_framework.svg` — Three-step framework with content filled in. Manager silhouette using data to inform judgment (right side). |
| **Alt Text** | "Worked example filling in the three-step framework. Step 1: Alert data shows bearing fault within 2 hours. Step 2: Context includes priority order and technician available in 30 minutes. Step 3: Decision is Modify — schedule technician during break window, monitor throughput, document rationale." |
| **Dev Notes** | Steps reveal sequentially on scroll/click. Each step content fades in (0.5s). Modify option pulses briefly (0.3s) when revealed to draw attention. Tablet: full-width vertical layout. |

### Screen m4.1.s3 — Practice — Apply the Framework

| Attribute | Specification |
|---|---|
| **Layout** | Top: alert card + context card side by side. Below: three-part structured response form (Step 1 assessment, Step 2 context factors, Step 3 decision + rationale). Submit button. Step-by-step feedback. |
| **Media Asset** | Alert card (amber border) with Line 5 seal failure alert. Context card (gray border) with operational details. Three form sections with dropdown/radio inputs. |
| **Alt Text** | "Practice exercise. Alert: Line 5 seal failure predicted within 90 minutes. Context: only active packaging line, backup available in 20 minutes. Three-part response form asks learner to assess data, identify context factors, and choose Act, Modify, or Escalate with rationale." |
| **Dev Notes** | Multi-step form: Step 1 must be completed before Step 2 unlocks, Step 2 before Step 3. Per-step feedback after submission. Incorrect steps show corrective guidance + allow retry. Tablet: full-width stacked layout, sticky alert/context cards at top during scroll. |

### Screen m4.2.s1 — Escalation Criteria

| Attribute | Specification |
|---|---|
| **Layout** | Decision table centered (max-width 760px). Four rows (criteria). Three columns: Condition, Example, What to Include. Callout box below: "Escalation is a professional decision, not a failure." |
| **Media Asset** | `img/m4/escalation_table.svg` — Styled decision table with icons per row (safety shield, authority badge, converging arrows, clock). Callout box with green check icon. |
| **Alt Text** | "Escalation criteria table with four rows. Row 1: Safety risk. Row 2: Exceeds authority. Row 3: Converging alerts. Row 4: Insufficient time. Each row includes a condition, example, and what to include when escalating. A callout states: Escalation is a professional decision, not a failure." |
| **Dev Notes** | Table rows fade in staggered (0.15s per row). Callout box appears after table complete with subtle bounce-in. Tablet: table may require horizontal scroll — add scroll indicator. |

### Screen m4.2.s2 — Act or Escalate? Two Scenarios

| Attribute | Specification |
|---|---|
| **Layout** | Two scenario cards side by side (50/50). Each card has: scenario description, Act/Escalate radio buttons, rationale selection dropdown. Submit per card. Feedback per card. |
| **Media Asset** | Two scenario cards with distinct borders. Scenario A: standard (gray border). Scenario B: converging alerts (amber border). |
| **Alt Text** | "Two side-by-side scenarios. Scenario A: Line 3 bearing fault in 3 hours, technician available, standard order. Scenario B: Lines 1 and 3 both alerting within one hour, insufficient technicians. For each, choose Act or Escalate." |
| **Dev Notes** | Independent submission per card. Correct: green checkmark + feedback. Incorrect: red highlight + correct answer + corrective feedback. Both cards must be completed before Continue. Tablet: stack vertically, full-width. |

### Screen m4.3.s1 — Four-Step Decision Workflow

| Attribute | Specification |
|---|---|
| **Layout** | Horizontal four-step workflow graphic (full width). Each step: icon + label + one-line description. Click-to-reveal recap panel below each step. |
| **Media Asset** | `img/m4/four_step_workflow.svg` — Four connected nodes: Consult (eye icon, blue) → Interpret (magnifier icon, amber) → Decide (scale icon, green) → Document (pencil icon, gray). Connecting arrows between nodes. |
| **Alt Text** | "Four-step decision workflow diagram. Step 1: Consult — open the dashboard, review signals. Step 2: Interpret — read trends, alerts, throughput. Step 3: Decide — assess data, consider context, choose action. Step 4: Document — record what you saw, decided, and why." |
| **Dev Notes** | Click-to-reveal: clicking a step expands a recap panel below the workflow bar. One panel open at a time (accordion). Workflow bar remains visible. Gating: all four must be clicked before Continue. Tablet: vertical stacked steps, tap to expand. |

### Screen m4.3.s2 — Habit Formation

| Attribute | Specification |
|---|---|
| **Layout** | Centered summary card (max-width 600px). Workflow mantra in large text. Clean visual with subtle repetition motif. |
| **Media Asset** | `img/m4/habit_summary_card.svg` — Clean card with workflow mantra: "Consult. Interpret. Decide. Document." Subtle repeating pattern of the four icons in background at low opacity. |
| **Alt Text** | "Summary card with the workflow mantra: Consult, Interpret, Decide, Document — every shift, every alert, every adjustment." |
| **Dev Notes** | Mantra text uses CSS animation — each word fades in sequentially (0.4s per word). Background icons have subtle parallax on scroll. Tablet: same layout, disable parallax. |

### Screen m4.4.s1 — Capstone — Scenario Setup

| Attribute | Specification |
|---|---|
| **Layout** | Full simulated dashboard view for Line 4 (70% width). Context panel on right sidebar (30%). Dashboard shows all three signal types populated with capstone data. |
| **Media Asset** | `img/m4/capstone_dashboard_line4.png` — Simulated Line 4 dashboard: declining 4-hour trend, motor overheating alert (90-min window), throughput 78% (red). `img/m4/capstone_context_panel.svg` — Context box: priority order in 3 hours, technician available. |
| **Alt Text** | "Simulated Line 4 dashboard showing a declining performance trend over 4 hours, a predictive alert for motor overheating with failure predicted within 90 minutes, and throughput at 78 percent in red. A context panel shows a priority order due in 3 hours and a technician currently available." |
| **Dev Notes** | Dashboard and context panel load simultaneously. No interaction — setup screen only. 'Begin Assessment' button at bottom. Tablet: dashboard full-width top, context panel as collapsible card below. Ensure dashboard image scales clearly to tablet resolution. |

### Screen m4.4.s2 — Capstone Q1 — Identify Critical Signal

| Attribute | Specification |
|---|---|
| **Layout** | Dashboard image pinned at top (sticky). Three-option multiple-choice below. Feedback panel. |
| **Media Asset** | Same capstone dashboard image. Three radio options with signal-type labels. |
| **Alt Text** | "Capstone question 1. The Line 4 dashboard is displayed. Question: Which signal requires your most immediate attention? Options: A) Performance trend, B) Predictive alert, C) Throughput indicator." |
| **Dev Notes** | Sticky dashboard on desktop (top 0, z-index 10). Submit + feedback. Correct (B): green highlight + feedback explaining shortest window and highest consequence. Incorrect: corrective feedback. Tablet: dashboard scrolls with content (not sticky). |

### Screen m4.4.s3 — Capstone Q2 — Interpret the Alert

| Attribute | Specification |
|---|---|
| **Layout** | Alert text highlighted from dashboard. Three dropdown fields (Prediction, Confidence Basis, Action Window). Per-component feedback. |
| **Media Asset** | Alert excerpt card with amber border. Three labeled dropdown fields matching component color scheme. |
| **Alt Text** | "Capstone question 2. The alert reads: Motor overheating detected on Line 4, temperature and vibration patterns consistent with imminent motor failure, respond within 90 minutes. Three dropdown fields ask the learner to identify the prediction, confidence basis, and action window." |
| **Dev Notes** | Three dropdown selects with 4–5 options each. Submit all three together. Per-field feedback (green/red border). Incorrect fields show correct answer inline. Tablet: full-width dropdowns, stacked vertically. |

### Screen m4.4.s4 — Capstone Q3 — Evaluate and Decide

| Attribute | Specification |
|---|---|
| **Layout** | Framework reminder graphic (compact, top). Three-part structured response: context factor checkboxes, Act/Modify/Escalate radio, rationale dropdown. Step-by-step feedback. |
| **Media Asset** | Compact three-step framework reminder bar. Checkbox group for context factors. Radio group for decision. Dropdown for rationale. |
| **Alt Text** | "Capstone question 3. The three-step evaluation framework is shown as a reminder. The learner must select relevant context factors, choose Act, Modify, or Escalate, and select a rationale from a dropdown. The correct answer is Modify: dispatch technician, plan brief stoppage within the 90-minute window, and document the decision." |
| **Dev Notes** | Multi-part form. Context factors: checkboxes (multiple select). Decision: radio group. Rationale: dropdown. Submit triggers per-section feedback. Step-by-step feedback reveals after submit. Tablet: stacked full-width, large touch targets. |

### Screen m4.4.s5 — Capstone Q4 — Document Rationale

| Attribute | Specification |
|---|---|
| **Layout** | Checklist card centered (max-width 640px). Five checkbox items. Submit button. Feedback panel with correct/incorrect item highlighting. |
| **Media Asset** | Checklist card with five items. Four correct items (green check on feedback), one incorrect (red X on feedback — detailed sensor logs). |
| **Alt Text** | "Capstone question 4. A checklist asks: What would you include in shift documentation? Five options: alert details, decision made, rationale, escalation or communication actions taken, and detailed sensor logs. Select all that apply." |
| **Dev Notes** | Select-all interaction with checkboxes. Submit triggers per-item feedback. Correct items (4): green checkmark. Incorrect item (sensor logs): red X + explanation. Score shown (e.g., 4/4 correct selections, or partial). Tablet: full-width card. |

### Screen m4.4.s6 — Results and Course Completion

| Attribute | Specification |
|---|---|
| **Layout** | Score card centered top. Below: five outcome summary items with checkmarks. Bottom: completion badge and conditional retake link. |
| **Media Asset** | `img/m4/completion_badge.svg` — Circular completion badge with "AI Dashboard Certified" text. Score display as large percentage. Five outcome summary items with green check icons. Conditional retake button (visible if < 80%). |
| **Alt Text** | "Course completion screen showing the learner's capstone score, a summary of five learning outcomes achieved, and a completion badge reading AI Dashboard Certified. A retake option is available if the score is below 80 percent." |
| **Dev Notes** | Score calculates from capstone Q1–Q4 responses. Score animates counting up (0 → final, 1.5s). Outcomes list fades in sequentially. Badge scales in (0 → 1, 0.4s bounce). If score < 80%: show amber 'Retake Capstone' button. If ≥ 80%: show green 'Complete' state + optional certificate download. Tablet: same layout, full-width. |

---

## Asset Inventory Summary

| Category | Count | Naming Convention |
|---|---|---|
| Static Images (PNG) | 4 | `img/{module}/descriptive_name.png` |
| SVG Illustrations | 18 | `img/{module}/descriptive_name.svg` |
| SVG Icons | 8 | `icon/descriptive_name.svg` |
| Lottie Animations | 1 | `anim/{module}/descriptive_name.json` |
| Avatar Illustrations | 2 | `img/{module}/avatar_descriptive.svg` |
| **Total unique assets** | **33** | |

## Responsive Design Notes

| Breakpoint | Behavior |
|---|---|
| Desktop (≥ 1024px) | Side-by-side layouts, sticky dashboards, horizontal flows, hover states |
| Tablet (768–1023px) | Stacked layouts, full-width cards, tap interactions, no hover dependency |
| Touch targets | Minimum 48×48px on all interactive elements |
| Reduced motion | All animations have `prefers-reduced-motion` fallbacks (static states) |
| Image scaling | All images use `max-width: 100%; height: auto` with `object-fit: contain` |

## Accessibility Requirements

- All images and interactive elements have descriptive alt text provided above
- Color is never the sole indicator — all color-coded elements also have text labels
- Interactive exercises support keyboard navigation (Tab, Enter, Space, Arrow keys)
- Drag-and-drop interactions have keyboard alternative (select + arrow keys to reorder)
- Focus indicators visible on all interactive elements
- Minimum contrast ratio: 4.5:1 for body text, 3:1 for large text
- Screen reader announcements for interaction feedback (correct/incorrect)