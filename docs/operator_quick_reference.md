# Quick Reference: v0.5.1 Team Testing

## Test Inputs Summary

**Scenario:** Customer service training for contact center with high turnover

**Key Risks (Intentional):**
- CRM system being replaced in April 2026 (course may be obsolete)
- De-escalation framework not documented
- 5-week deadline with limited SME availability
- Missing compliance scripts

**Expected Behavior:** Generates 14-20 open questions, triggers risk gates

---

## Three Test Runs

### Run 1: Baseline (Should PASS)

**Config Change:** Set `"enabled": false` in `risk_gate_escalation`

```bash
./scripts/run_dev.sh
echo "Exit: $?"
python3 scripts/run_report.py --latest | grep "end_state"
```

**Expected:** ✅ Completes, exit code 0, 14-20 open questions

---

### Run 2: Risk Gates with Auto-Override (Should PASS with warnings)

**Config Change:**
```json
"risk_gate_escalation": {
  "enabled": true,
  "open_questions_threshold": 8,
  "force_gate_on_qa_critical": true,
  "auto_override": true
}
```

```bash
./scripts/run_dev.sh
grep "risk_gate_forced" governance/run_ledger.jsonl | tail -5
```

**Expected:** ✅ Completes, shows risk gate auto-override messages

---

### Run 3: Strict Enforcement (Should FAIL at risk gate)

**Config Change:** Set `"auto_override": false`

```bash
./scripts/run_dev.sh
# When prompted: Press Enter (do NOT type APPROVE)
echo "Exit: $?"  # Should be 1
```

**Expected:** ❌ Stops at risk gate, exit code 1, status "aborted"

---

## Success Checklist

- [ ] Run 1 completes (exit 0)
- [ ] Run 2 triggers risk gates but completes (exit 0)
- [ ] Run 3 halts at risk gate (exit 1)
- [ ] All runs have audit summaries
- [ ] Ledger shows correct approval modes

---

## Troubleshooting

**Pipeline won't start:**
- Check `config/run_config.json` exists
- Verify inputs exist: `ls inputs/*.md`

**No risk gates trigger:**
- Check `"enabled": true` in config
- Verify threshold is 8 (not higher)

**Can't find latest run:**
```bash
ls -lt outputs/ | head -2
python3 scripts/run_report.py --latest
```
