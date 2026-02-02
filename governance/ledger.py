import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


LEDGER_PATH = Path("governance/run_ledger.jsonl")


def write_ledger_entry(entry: Dict[str, Any]) -> None:
    """
    Append a single run entry to the run ledger.
    One JSON object per line.
    """
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

    enriched_entry = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        **entry,
    }

    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(enriched_entry) + "\n")