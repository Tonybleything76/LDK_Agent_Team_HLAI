import hashlib
import json
from pathlib import Path
from typing import Any, Union


def canonical_json_dumps(data: Any) -> str:
    """Return a canonical JSON string for hashing (sorted keys, no whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_string_sha256(content: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 encoded string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Return the SHA-256 hex digest of a file (buffered, 4 KiB blocks)."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for block in iter(lambda: fh.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()
