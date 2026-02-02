import json
from pathlib import Path

from orchestrator.validation import ValidationConfig, validate_agent_output


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_CONFIG_PATH = PROJECT_ROOT / "orchestrator" / "config" / "run_config.json"


def main() -> None:
    if not RUN_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing: {RUN_CONFIG_PATH}")

    cfg = json.loads(RUN_CONFIG_PATH.read_text(encoding="utf-8"))

    v = cfg.get("validation", {})
    vcfg = ValidationConfig(
        min_deliverable_chars=int(v.get("min_deliverable_chars", 300)),
        placeholder_markers=list(v.get("placeholder_markers", [])),
    )

    agents = cfg.get("agents", [])
    if not agents:
        print("No agents in run_config.json. Nothing to validate.")
        return

    failures = 0

    for a in sorted(agents, key=lambda x: int(x["step_idx"])):
        agent_name = a["agent_name"]
        tmp_path = PROJECT_ROOT / a["tmp_json_relpath"]

        print(f"\nValidating {agent_name} from {tmp_path}...")
        if not tmp_path.exists():
            print(f"⚠️ Missing tmp JSON file: {tmp_path}")
            failures += 1
            continue

        try:
            result = json.loads(tmp_path.read_text(encoding="utf-8"))
            validate_agent_output(agent_name, result, vcfg)
            print(f"✅ {agent_name}: Validated successfully")
        except Exception as e:
            print(f"❌ {agent_name}: Validation failed\n{e}")
            failures += 1

    if failures:
        raise SystemExit(f"\nValidation finished with {failures} failure(s).")
    print("\n✅ All tmp outputs validated successfully.")


if __name__ == "__main__":
    main()