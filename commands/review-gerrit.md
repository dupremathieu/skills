# Review Gerrit Changes

Review code changes on Gerrit and post draft comments (visible only to you until published).

## Arguments

Gerrit search query: $ARGUMENTS

If no arguments provided, use: `status:open -is:wip`

## Prerequisites

1. Verify the helper script exists: `~/.claude/scripts/gerrit-review.py`
2. Test connectivity by running: `python3 ~/.claude/scripts/gerrit-review.py query "status:open limit:1"`
3. If authentication fails, instruct the user to run: `! python3 ~/.claude/scripts/gerrit-review.py store-password`

## Workflow

### Step 1: Query Changes

```bash
python3 ~/.claude/scripts/gerrit-review.py query "<query>"
```

Parse the JSON array. For each change, extract:
- `_number` (change number)
- `subject` (commit title)
- `project`
- `current_revision` (the SHA)
- The file list from `revisions.<sha>.files`

If no changes found, report that and stop.

### Step 2: For Each Change

Print progress: "Reviewing change N/total: <subject>..."

#### 2a. Fetch commit message
```bash
python3 ~/.claude/scripts/gerrit-review.py commit <change_number> current
```

#### 2b. Fetch the full patch
```bash
python3 ~/.claude/scripts/gerrit-review.py patch <change_number> current
```

### Step 3: Review

Analyze the commit message AND every file in the diff. Only review added or modified lines (lines starting with `+` in the diff). Skip deleted files and binary files.

Look for issues in these categories:

| Tag | What to look for |
|-----|-----------------|
| `[English]` | Grammar, typos, spelling, bad formulations in comments, strings, or commit message |
| `[Formatting]` | Trailing whitespace, wrong indentation, line length, missing blank lines |
| `[Style]` | Naming conventions, code organization, readability, idiomatic patterns |
| `[Bug]` | Logic errors, off-by-one, null/uninitialized use, resource leaks, race conditions |
| `[Inconsistency]` | Inconsistent naming, patterns, or approaches within the change or with surrounding code |
| `[Security]` | Command injection, path traversal, unsafe operations, hardcoded credentials |
| `[Clarity]` | Unclear comments, missing context, vague commit messages, misleading names |

Assign a severity to each finding:
- **critical** — Must fix before merge (bugs, security vulnerabilities)
- **major** — Should fix, significant quality concern
- **minor** — Nice to fix, small improvement
- **suggestion** — Optional, take it or leave it

### Step 4: Post Draft Comments

For each finding, post a draft comment:

```bash
python3 ~/.claude/scripts/gerrit-review.py draft <change_number> current '{"path": "<file_path>", "line": <line_number>, "message": "<comment>"}'
```

**Comment format:** `[Category] (severity) Description of the issue.`

Examples:
- `[English] (minor) "informations" should be "information" (uncountable noun).`
- `[Bug] (critical) Buffer overflow: strncpy does not null-terminate when src length >= n.`
- `[Clarity] (major) Commit subject is vague. Describe what was fixed and why.`

**For commit message issues:** use `"path": "/COMMIT_MSG"`. In the `/COMMIT_MSG` virtual file, the actual subject line starts around line 7 and body around line 9 (after Parent/Author/Date headers). Count the lines from the commit endpoint output to get accurate line numbers.

**For code issues:** use the actual file path and the line number from the diff context (the line number in the new version of the file, visible after `@@` markers in the unified diff).

### Step 5: Summary

After processing all changes, print a summary table:

| Change | Subject | Critical | Major | Minor | Suggestion | Link |
|--------|---------|----------|-------|-------|------------|------|

Use Gerrit links in the format: `https://g1.sfl.io/c/<project>/+/<number>`

Remind the user: **Draft comments must be published manually** in the Gerrit web UI (open the change, click Reply/Review, then publish the drafts).

## Guidelines

- Be constructive and helpful, not harsh or pedantic.
- Keep each comment to 1-3 sentences.
- Only comment on new/modified lines in the diff, not pre-existing code.
- If a change looks clean with no issues, note it in the summary — no need to force comments.
- Process changes sequentially, printing progress as you go.
- If a query returns more than 10 changes, process the first 10 and tell the user to narrow the query or re-run for the rest.
