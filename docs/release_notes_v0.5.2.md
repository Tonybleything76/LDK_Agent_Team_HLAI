# Release Notes — v0.5.2

**Date:** 2026-02-12  
**Tag:** `v0.5.2`  
**Head commit:** `f5eb4bda0cf27f67612e4d3182ce00325f85a68a`

---

## Summary of Changes (since v0.5.1)

### Governance & Auditability
- **Preflight/postflight drift guard** — worktree cleanliness is enforced before and after runs; `--allow-dirty-worktree` is available for dev only (`2281a91`)
- **Risk gate ledger events** — risk gates now emit structured ledger entries for full audit traceability (`aa5d1fc`)
- **Audit `run_id` and `gate_manifest`** — audit summaries now include `run_id` and a complete `gate_manifest` (`b5d4d32`)
- **`planned_phase_gates` in audit** — gate manifest exposes the planned phase gate schedule `[3,6,9]` for transparency (`657d533`)
- **Auto-approval attribution fix** — `approval_source` correctly reports `"profile"` when driven by governance profile, `"cli_flag"` only when an explicit CLI flag is used (`685236b`)
- **Approval ledger untracked** — `governance/approval_ledger.jsonl` removed from tracking to prevent secret/PII leaks (`f5eb4bd`)

### Operator Tooling
- **`--max-step` early-stop** — controlled pilots can now limit execution to N steps (`f7d03d6`)
- **`run_config` version bump** — config updated for proposal `ad6b9b45` (`d8b5762`)

### Testing & CI
- **Audit summary regression tests** — enforce `run_id` and `gate_manifest` completeness (`2e4aad4`)
- **Full pytest pass restored** — all 69 tests passing, 2 warnings (`39e4259`)

### Repo Hygiene
- **Safe `.gitignore`** — ignores local/generated artifacts without suppressing source or test files (`f924260`)
- **Bulk tracking of source files** — all source code, tests, docs, schemas, and knowledge base tracked (`f1b653a`)
- **Proof artifact ignoring** — root-level one-off proof JSONs excluded from tracking (`32655a2`)

---

## Governance Proof References

### Dry Run — `20260212_230522`
| Claim | Value |
|---|---|
| `run_id` | `20260212_230522` |
| `governance_profile` | `staging` |
| `providers_called` | **false** (all 9 steps used `dry_run` provider) |
| `audit_valid` | **true** (`end_state: run_completed`) |
| `planned_phase_gates` | `[3, 6, 9]` |
| `phase_gates_encountered` | 3 (steps 3, 6, 9) |
| `risk_gates_encountered` | 2 (step 1: `open_questions_threshold`, step 8: `qa_critical`) |
| `approvals` | manual: 2, auto: 3 |

### Live Run — `20260212_230630`
| Claim | Value |
|---|---|
| `run_id` | `20260212_230630` |
| `governance_profile` | `staging` |
| `providers_used` | `openai` (steps 1–3) |
| `cost_guardrail_displayed` | **true** |
| `approval_source` | **`profile`** (auto-approved via staging profile) |
| `planned_phase_gates` | `[3, 6, 9]` |
| `phase_gates_encountered` | 1 (step 3) |
| `risk_gates_encountered` | 0 |
| `approvals` | manual: 0, auto: 1 |

---

## Known Limitations / Operator Notes

1. **Environment loading** — `dotenv` is not auto-loaded. Before running:
   ```bash
   set -a; source .env; set +a
   ```
2. **Staging worktree requirement** — staging profile enforces a clean (tracked) worktree by default. For development use, pass `--allow-dirty-worktree`.
3. **Cost guardrail** — live provider runs display a cost warning and require explicit `RUN` confirmation unless auto-approved by profile.
