import subprocess
import shlex
from typing import List, Callable, Any

def get_git_status_porcelain() -> str:
    """
    Get the git status in porcelain format.
    Shells out to 'git status --porcelain'.
    """
    try:
        # check=True raises CalledProcessError on non-zero exit code
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get git status: {e.stderr}") from e

def get_tracked_dirty_files(status_output: str) -> List[str]:
    """
    Parse git status porcelain output to find dirty tracked files.
    Ignores untracked files (??).
    Returns a list of filenames that are modified/added/deleted in the index or working tree.
    """
    dirty_files = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        
        # Format is XY PATH
        # X = index status, Y = worktree status
        # ?? = untracked (we ignore)
        if line.startswith("??"):
            continue
            
        # If we are here, it's tracked and dirty in some way (M, A, D, R, C, U)
        # Extract filename (handle potential quoting? git porcelain v1 handles simplistic paths usually)
        # For simple filename extraction:
        parts = line[3:].strip() # Skip first 3 chars (XY )
        if parts:
            dirty_files.append(parts)
            
    return dirty_files

def enforce_preflight(
    allow_dirty: bool,
    profile: str,
    ledger_writer: Callable[[dict], None],
    run_id: str,
    status_provider: Callable[[], str] = get_git_status_porcelain
) -> None:
    """
    Enforce clean worktree before run.
    """
    status_output = status_provider()
    dirty_files = get_tracked_dirty_files(status_output)
    
    if not dirty_files:
        ledger_writer({
            "event_type": "preflight_passed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": [],
            "allow_dirty": allow_dirty
        })
        return

    # Dirty files exist
    if allow_dirty and profile == "dev":
        # Allowed warning
        ledger_writer({
            "event_type": "preflight_passed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": dirty_files,
            "allow_dirty": allow_dirty,
            "warning": "Worktree dirty but allowed in dev profile"
        })
    else:
        # Failure
        ledger_writer({
            "event_type": "preflight_failed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": dirty_files,
            "allow_dirty": allow_dirty
        })
        
        msg = f"Worktree dirty: {dirty_files}. "
        if allow_dirty:
            msg += f"Allowed only in 'dev' profile (current: {profile})."
        else:
            msg += "Clean worktree required (use --allow-dirty-worktree --governance_profile dev to bypass)."
            
        raise RuntimeError(msg)

def enforce_postflight(
    allow_dirty: bool,
    profile: str,
    ledger_writer: Callable[[dict], None],
    run_id: str,
    status_provider: Callable[[], str] = get_git_status_porcelain
) -> None:
    """
    Enforce clean worktree after run (detect scope drift).
    """
    status_output = status_provider()
    dirty_files = get_tracked_dirty_files(status_output)
    
    # If we allowed dirty pre-flight, strictly speaking we might want to check if *new* dirty files appeared.
    # But the requirement says "detects and fails if tracked files changed unexpectedly after the run".
    # Typically postflight expects CLEAN unless we are in a mode that permits drift.
    # If allow_dirty=True (dev mode), we might tolerate dirty postflight too, or we might want to ensure *no additional* drift.
    # For simplicity/strictness based on prompt: "Guard must ... detect and fail if tracked files changed unexpectedly".
    # If allow_dirty=True, we probably shouldn't fail postflight just because files are still dirty (they were dirty before).
    # However, to be "unexpected", maybe we should diff?
    # The prompt says: "if dirty files exist and not allow_dirty: record ... postflight_failed".
    # This implies if allow_dirty=True, we interpret valid drift?
    # Let's follow the logic:
    # "if dirty files exist and not allow_dirty: record preflight_failed/postflight_failed and raise RuntimeError"
    # This implies if allow_dirty is True, we pass.
    
    if not dirty_files:
        ledger_writer({
            "event_type": "postflight_passed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": [],
            "allow_dirty": allow_dirty
        })
        return

    if allow_dirty and profile == "dev":
        ledger_writer({
            "event_type": "postflight_passed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": dirty_files,
            "allow_dirty": allow_dirty,
            "warning": "Worktree dirty post-run but allowed in dev profile"
        })
    else:
        ledger_writer({
            "event_type": "postflight_failed",
            "run_id": run_id,
            "profile": profile,
            "dirty_files": dirty_files,
            "allow_dirty": allow_dirty
        })
        raise RuntimeError(f"Postflight drift detected! Tracked files changed: {dirty_files}")
