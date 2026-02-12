import hashlib
import json

def canonical_json_dumps(data):
    """
    Returns a canonical JSON string for hashing:
    - Sorted keys
    - No whitespace (separators=(',', ':'))
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def compute_string_sha256(content_str: str) -> str:
    """
    Returns SHA256 hex digest of a string.
    """
    return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

def compute_file_sha256(file_path: str) -> str:
    """
    Returns SHA256 hex digest of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
