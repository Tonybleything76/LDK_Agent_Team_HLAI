# Release Process

This document describes how to create a new release for the LDK Agent Team HLAI project.

## Automated Release Creation

The repository now includes a GitHub Actions workflow (`.github/workflows/release.yml`) that automates the release creation process.

### Option 1: Automatic Release on Tag Push

When you push a new tag matching the pattern `v*`, the workflow will automatically:
1. Extract release notes from `docs/release_notes_<tag>.md`
2. Create a GitHub release with the tag name as the title
3. Include the release notes as the release description

**Steps:**
```bash
# Create and push a new tag
git tag -a v0.5.2 -m "v0.5.2 release: governance auditability + media delivery + bundling fixes"
git push origin v0.5.2
```

### Option 2: Manual Workflow Trigger

If the tag already exists (like v0.5.2), you can manually trigger the workflow:

1. Go to the GitHub repository in your browser
2. Navigate to **Actions** tab
3. Select the **"Create Release"** workflow
4. Click **"Run workflow"**
5. Enter the tag name (e.g., `v0.5.2`)
6. Click **"Run workflow"** button

### Option 3: Manual Release Creation (Original Process)

If you prefer to create the release manually through the GitHub UI:

1. Open the GitHub repo in browser
2. Go to **Releases**, then **"Draft a new release"**
3. **Tag**: Select or enter `v0.5.2`
4. **Title**: Enter `v0.5.2`
5. **Description**: Copy content from `docs/release_notes_v0.5.2.md`
6. Click **"Publish release"**

## For v0.5.2 Release

The v0.5.2 tag already exists and points to commit `c4f6c88`. The release notes are available in `docs/release_notes_v0.5.2.md`.

To create the release for v0.5.2:
- **Easiest**: Use Option 2 (Manual Workflow Trigger) above
- **Alternative**: Use Option 3 (Manual Release Creation) above

## Release Notes Format

Release notes should be placed in `docs/release_notes_<tag>.md` and follow this format:

```markdown
# Release Notes — <version>

**Date:** YYYY-MM-DD
**Tag:** `<tag>`
**Head commit:** `<commit-hash>`

---

## Summary of Changes

### Category 1
- Change description

### Category 2
- Change description

---

## Additional Sections (optional)

Any additional information...
```

## Checklist for New Releases

- [ ] Update VERSION file if needed
- [ ] Create release notes in `docs/release_notes_<tag>.md`
- [ ] Create and push the git tag
- [ ] Verify CI passes
- [ ] Create GitHub release (automatic or manual)
- [ ] Announce the release to stakeholders
