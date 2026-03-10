import os
import json
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.getcwd())

from utils import hashing

def bootstrap():
    project_root = os.getcwd()
    pack_version = "genesis_v1"
    pack_dir = os.path.join(project_root, "knowledge", "packs", pack_version)
    included_dir = os.path.join(pack_dir, "included")
    
    # 1. Ensure Directories
    if os.path.exists(pack_dir):
        print(f"Pack {pack_version} already exists. Skipping.")
        return

    os.makedirs(included_dir, exist_ok=True)
    
    # 2. Create Content
    readme_path = os.path.join(included_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Genesis Knowledge Pack\n\nBootstrapping the system for first pilot execution.\n")
    
    # 3. Calculate Hashes
    readme_hash = hashing.compute_file_sha256(readme_path)
    
    # Note: path in manifest is relative to pack root
    files = [
        {"path": "included/README.md", "sha256": readme_hash}
    ]
    
    # 4. Generate Manifest
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    manifest_data = {
        "pack_version": pack_version,
        "generated_at_utc": timestamp,
        "git_commit_hash": "genesis_bootstrap",
        "proposal_id": "genesis_bootstrap",
        "files": files
    }
    
    # 5. Manifest Hash
    # We must exclude the hash field itself
    manifest_canonical = hashing.canonical_json_dumps(manifest_data)
    manifest_hash = hashing.compute_string_sha256(manifest_canonical)
    
    manifest_data["manifest_hash"] = manifest_hash
    
    # 6. Write Manifest
    manifest_path = os.path.join(pack_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=4, sort_keys=True)
        
    print(f"SUCCESS: Bootstrapped {pack_version} at {pack_dir}")
    print(f"Manifest Hash: {manifest_hash}")

if __name__ == "__main__":
    bootstrap()
