# Review GitHub Pull Request

Review a GitHub pull request and print review comments for the user.

## Arguments

Pull request reference: $ARGUMENTS

Accepts any format `gh pr view` supports: PR number, URL, or `owner/repo#number`.

If no arguments provided, ask the user for the PR reference.

## Workflow

### Step 1: Fetch PR Details

```bash
gh pr view <pr_ref> --json number,title,body,author,baseRefName,headRefName,url,state,additions,deletions,changedFiles
```

Parse the JSON output. Extract and display:
- Title, author, base/head branches
- PR description/body

### Step 2: Fetch PR Comments and Review Comments

Run these in parallel:

```bash
gh pr view <pr_ref> --json comments --jq '.comments[].body'
```

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '.[].body'
```

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[] | "\(.path):\(.line // .original_line) — \(.body)"'
```

Read all conversation comments, review summaries, and inline review comments to understand the full discussion context.

### Step 3: Fetch Commit Messages

```bash
gh pr view <pr_ref> --json commits --jq '.commits[].messageHeadline'
```

Read all commit messages to understand the progression of the work.

### Step 4: Fetch the Diff

```bash
gh pr diff <pr_ref>
```

This gives the full unified diff of the PR.

### Step 5: Understand the PR

Before reviewing, build a mental model of the change:
- What is the goal of the PR? (from title, body, and commit messages)
- What feedback has already been given? (from comments and reviews)
- What files are changed and how do they relate?
- Are there any unresolved discussions?

Print a brief summary: "**PR #N: <title>** by <author> — <1-2 sentence summary of the change>"

### Step 6: Review

Analyze the commit messages AND every file in the diff. Only review added or modified lines (lines starting with `+` in the diff). Skip deleted files and binary files.

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

### Step 7: Print Review

Print all findings grouped by file, in this format:

```
### <file_path>

**Line <line_number>:** `[Category]` (severity) Description of the issue.
```

Examples:
- **Line 42:** `[English]` (minor) "informations" should be "information" (uncountable noun).
- **Line 15:** `[Bug]` (critical) Buffer overflow: `strncpy` does not null-terminate when src length >= n.

**For commit message issues:** group under `### Commit Messages`.

### Step 8: Summary

Print a summary table:

| Category | Critical | Major | Minor | Suggestion |
|----------|----------|-------|-------|------------|
| English | | | | |
| Formatting | | | | |
| Style | | | | |
| Bug | | | | |
| Inconsistency | | | | |
| Security | | | | |
| Clarity | | | | |
| **Total** | | | | |

Include the PR link at the end.

If the change looks clean with no issues, say so — no need to force comments.

**Do NOT post comments to GitHub unless the user explicitly asks.** All review output is printed locally for the user to read and act on.

If the user explicitly asks to publish the review, use:
```bash
gh pr review <pr_ref> --comment --body "<review body>"
```

## Guidelines

- Be constructive and helpful, not harsh or pedantic.
- Keep each comment to 1-3 sentences.
- Only comment on new/modified lines in the diff, not pre-existing code.
- Take into account existing review comments — don't repeat feedback already given.
- If a prior reviewer raised a point that was addressed in a later commit, acknowledge that, don't re-raise it.
- If a change looks clean with no issues, note it in the summary — no need to force comments.
