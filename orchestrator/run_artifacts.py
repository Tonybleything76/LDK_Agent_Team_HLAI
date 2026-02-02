"""
Run artifacts management for checkpoint and resume functionality.

This module provides utilities for:
- Creating run directories with checkpoint subdirectories
- Writing and reading step checkpoints
- Managing run manifests (metadata about run progress)
- Computing hashes for config and input files
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple


def ensure_run_dirs(run_dir: Path) -> Path:
    """
    Ensure run directory and checkpoints subdirectory exist.
    
    Args:
        run_dir: Path to the run output directory
        
    Returns:
        Path to the checkpoints directory
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoints_dir = run_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    
    return checkpoints_dir


def write_checkpoint(checkpoints_dir: Path, step_idx: int, state: Dict[str, Any]) -> None:
    """
    Write a checkpoint file for a completed step.
    
    Args:
        checkpoints_dir: Path to the checkpoints directory
        step_idx: Step index (1-based)
        state: System state dictionary to save
    """
    checkpoint_file = checkpoints_dir / f"step_{step_idx:02d}_state.json"
    
    with open(checkpoint_file, "w") as f:
        json.dump(state, f, indent=2)


def read_latest_checkpoint(checkpoints_dir: Path) -> Tuple[int, Dict[str, Any]]:
    """
    Read the latest checkpoint from the checkpoints directory.
    
    Args:
        checkpoints_dir: Path to the checkpoints directory
        
    Returns:
        Tuple of (last_step_idx, state_dict)
        Returns (0, {}) if no checkpoints found
    """
    checkpoints_dir = Path(checkpoints_dir)
    
    if not checkpoints_dir.exists():
        return (0, {})
    
    # Find all checkpoint files
    checkpoint_files = sorted(checkpoints_dir.glob("step_*_state.json"))
    
    if not checkpoint_files:
        return (0, {})
    
    # Get the latest checkpoint
    latest_checkpoint = checkpoint_files[-1]
    
    # Extract step index from filename (step_NN_state.json)
    step_idx = int(latest_checkpoint.stem.split("_")[1])
    
    # Load state
    with open(latest_checkpoint, "r") as f:
        state = json.load(f)
    
    return (step_idx, state)


def read_checkpoint(checkpoints_dir: Path, step_idx: int) -> Dict[str, Any]:
    """
    Read a specific checkpoint by step index.
    
    Args:
        checkpoints_dir: Path to the checkpoints directory
        step_idx: Step index to load
        
    Returns:
        State dictionary
        
    Raises:
        FileNotFoundError: If checkpoint doesn't exist
    """
    checkpoint_file = Path(checkpoints_dir) / f"step_{step_idx:02d}_state.json"
    
    if not checkpoint_file.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_file}")
    
    with open(checkpoint_file, "r") as f:
        return json.load(f)


def write_manifest(run_dir: Path, manifest: Dict[str, Any]) -> None:
    """
    Write the run manifest file.
    
    Args:
        run_dir: Path to the run output directory
        manifest: Manifest dictionary to save
    """
    manifest_file = Path(run_dir) / "run_manifest.json"
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)


def read_manifest(run_dir: Path) -> Dict[str, Any]:
    """
    Read the run manifest file.
    
    Args:
        run_dir: Path to the run output directory
        
    Returns:
        Manifest dictionary
        
    Raises:
        FileNotFoundError: If manifest doesn't exist
    """
    manifest_file = Path(run_dir) / "run_manifest.json"
    
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_file}")
    
    with open(manifest_file, "r") as f:
        return json.load(f)


def compute_config_hash(config_path: Path) -> str:
    """
    Compute SHA256 hash of the config file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Hex string of SHA256 hash
    """
    with open(config_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_inputs_hash(business_brief_path: Path, sme_notes_path: Path) -> str:
    """
    Compute SHA256 hash of concatenated input files.
    
    Args:
        business_brief_path: Path to business_brief.md
        sme_notes_path: Path to sme_notes.md
        
    Returns:
        Hex string of SHA256 hash
    """
    hasher = hashlib.sha256()
    
    # Hash business brief
    with open(business_brief_path, "rb") as f:
        hasher.update(f.read())
    
    # Hash SME notes
    with open(sme_notes_path, "rb") as f:
        hasher.update(f.read())
    
    return hasher.hexdigest()
