Scenario: Customer Service Onboarding + De-escalation (v0.5.1 test)

# Subject Matter Expert Notes: Customer Service Training

## Subject Matter Expertise

**SME Background:** 8 years in contact center operations, currently Training Manager. Worked with top 10% performers to identify success patterns.

**Core Competencies Needed:**
1. **System Navigation** - ServiceNow CRM (current version 2024.3, but upgrade to 2025.1 planned for April)
2. **Communication Skills** - De-escalation, active listening, empathy statements
3. **Policy Knowledge** - Billing policies, refund authority limits, escalation triggers
4. **Problem-Solving** - Root cause analysis for recurring issues

**Current State:** New hires receive 2 weeks of classroom training followed by 1 week of shadowing. Feedback indicates the classroom portion is too theoretical and doesn't prepare them for real call complexity.

## Key Concepts and Topics

1. **LEAP De-Escalation Framework**: Listen actively, Empathize with customer emotion, Apologize for the inconvenience, Problem-solve collaboratively
   - This is our internal framework, not industry-standard (we developed it last quarter)
   - Top performers use this instinctively, but it's not formally documented yet
   
2. **ServiceNow CRM Navigation**: Account lookup, interaction logging, case creation, escalation routing
   - **CRITICAL ISSUE**: System is being replaced in April, but timeline is uncertain
   - Training on current system may become obsolete within 60 days
   
3. **Common Call Types** (in order of frequency):
   - Billing disputes (35% of calls)
   - Password resets (20%)
   - Service upgrades/downgrades (15%)
   - Technical troubleshooting (15%)
   - Account changes (10%)
   - Cancellations (5%)

4. **Authority Levels**: CSRs can approve refunds up to $50 without supervisor approval. Anything above requires escalation.

5. **Compliance Requirements**: 
   - PCI-DSS: Never store full credit card numbers in notes
   - Data Privacy: Verify customer identity before discussing account details
   - **MISSING**: We don't have formal scripts for identity verification yet

## Common Misconceptions

- **"Faster is better"**: New agents rush calls to meet volume targets, but this increases callbacks. Quality over speed initially.
- **"Apologizing admits fault"**: Agents avoid apologies fearing liability. Actually, empathy statements reduce escalations by 60%.
- **"Escalate difficult customers immediately"**: Agents over-escalate. 70% of "escalated" calls could be resolved at Tier 1 with proper training.

## Real-World Applications

**Scenario: Billing Dispute**
- Customer sees unexpected $25 charge
- Agent must: verify identity, locate charge in billing system, explain charge reason, offer resolution
- Common failure: Agents can't navigate to billing detail screen quickly, customer gets frustrated

**Scenario: Angry Customer**
- Customer has been on hold 20+ minutes, already frustrated before agent picks up
- LEAP framework critical here: acknowledge wait time, empathize, then problem-solve
- Common failure: Agents jump to solutions without acknowledging emotion

**Challenges:**
- High call volume creates pressure to rush
- System has 3-5 second lag times during peak hours
- Customers often don't know what they need ("my internet is broken" could be 10 different issues)

## Resources and References

**Available Resources:**
- ServiceNow training sandbox (limited to 20 concurrent users)
- Call recording library (500+ examples, not categorized or tagged)
- Internal knowledge base (outdated, last updated 18 months ago)

**Missing Resources:**
- No formal de-escalation training materials exist
- No standardized response templates for common scenarios
- No practice exercises or simulations

**Industry Standards:**
- ICMI (International Customer Management Institute) best practices
- HDI (Help Desk Institute) support center standards

## Prerequisites

**Required Prior Knowledge:**
- Basic computer skills (typing 25+ WPM, using web browsers)
- Professional communication skills (phone etiquette)
- High school diploma or equivalent

**Recommended Background:**
- Customer-facing experience (retail, hospitality, etc.)
- Comfort with learning new software systems

**Assumed Skill Levels:**
- No prior contact center experience required
- No technical troubleshooting background needed
- Will need to learn CRM system from scratch

---

**SME Availability:** I can dedicate 5 hours/week for the next 4 weeks to support course development. After that, I'm leading a process improvement project and will have limited availability.

**Open Questions from SME:**
- Should we train on the current CRM knowing it's being replaced soon, or wait for the new system?
- How do we handle the fact that our de-escalation framework isn't formally documented?
- Can we get budget for a practice simulation tool, or do we need to work within Rise's limitations?
