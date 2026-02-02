# Approval Gates (v0.1)

## Gate rule (global)
- The pipeline must STOP after each agent completes.
- A human must review the agent’s Markdown deliverable and approve.
- Only after approval does the pipeline proceed.

## What counts as approval
- You will type: APPROVE
- Anything else means: NOT approved (stop and ask what to change)

## Gate checklist (use for every agent)
1) Output exists (.md saved)
2) Output matches scope (no invented facts)
3) Output is execution-ready for the next agent
4) Open questions are captured (if needed)
5) State JSON updated correctly and validated