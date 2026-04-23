---
name: fix-gerrit-reviews
description: "Respond to and fix Gerrit review comments. Use when: fixing Gerrit remarks, addressing Gerrit feedback, resolving Gerrit review comments, handling code review on a Gerrit change. Reads comments via the gerrit-review.py helper, applies fixes locally, builds, tests, and produces a recap for replying to each unresolved comment."
argument-hint: "Gerrit change number or URL (e.g. 49957 or https://g1.sfl.io/c/sfl/seapath/training/+/49957)"
---

# Fix Gerrit Reviews

Respond to Gerrit review comments locally: apply fixes, build, test, and produce a recap of draft responses ready to post. **Does NOT amend, push, or post replies to Gerrit.**

## When to Use

- A Gerrit change has unresolved review comments that need to be addressed
- You want to process all unresolved comments on a change in one pass
- You need a draft recap of all responses before posting them manually

## Prerequisites

1. Verify the helper script `gerrit-review.py` exists (in the PATH or in AI directory like `~/.claude/scripts/gerrit-review.py`)
2. Test connectivity by running: `gerrit-review.py query "status:open limit:1"`
3. If authentication fails, instruct the user to run: `! gerrit-review.py store-password` with the corect script path if needed
3. If authentication fails, instruct the user to run: `! python3 ~/.claude/scripts/gerrit-review.py store-password`

## Procedure

### 1. Identify the Change

- If the user provides a change number or URL, parse the change number out of it.
- If not provided, detect from the current git branch's latest commit `Change-Id:` trailer and query it:
  ```bash
  CID=$(git log -1 --format=%B | sed -n 's/^Change-Id: //p')
  python3 ~/.claude/scripts/gerrit-review.py query "change:$CID status:open"
  ```
  Extract `_number` from the first result.

### 2. Fetch Change Context

Run in parallel:

```bash
gerrit-review.py query "change:<NUMBER>"
gerrit-review.py commit <NUMBER> current
gerrit-review.py patch <NUMBER> current
gerrit-review.py comments <NUMBER>
```

From these extract: `subject`, `project`, `current_revision`, changed files, and all published comments.

### 3. Filter and Group Comments

The `comments` output is a JSON object keyed by file path (plus `/COMMIT_MSG` for commit-message comments). Each entry is an array of comment objects with fields: `id`, `line`, `range`, `message`, `author`, `unresolved`, `in_reply_to`, `patch_set`.

- **Keep only unresolved comments** (`"unresolved": true`).
- For threaded comments, display only the latest message in the chain but treat the thread as one unit.
- Group by file path, then sort by line number.
- Skip comments on `/PATCHSET_LEVEL` unless they are actionable.

### 4. Process Each Unresolved Comment

For **each** unresolved comment, do the following **in order**:

#### 4a. Display the Remark

```
---
### Comment #N — @<author.username>
**File:** `<path>` (line <line>)
**Patchset:** <patch_set>
**Comment:** <message>
---
```

For `/COMMIT_MSG` comments, note the commit-message line number and map it back to the actual commit message body (lines after the headers).

#### 4b. Analyze and Decide

Evaluate whether the comment:
- **Requires a code change** (bug fix, style fix, logic improvement)
- **Is a question** that needs an explanation only
- **Is not relevant** (outdated, already addressed, or disagree with reason)

#### 4c. Apply Fix or Draft Response

- **If a code fix is needed:** Read the file, understand the context, apply the fix, and print:
  ```
  **Action:** Fixed — <brief description of what was changed>
  **Response draft:** <suggested reply to the reviewer>
  ```

- **If only a response is needed (no code change):** Print:
  ```
  **Action:** No code change needed
  **Response draft:** <explanation or clarification to post>
  ```

- **If not relevant:** Print:
  ```
  **Action:** Skipped — <reason>
  **Response draft:** <polite explanation of why it was skipped or declined>
  ```

**Note:** The local working tree must already contain the change's patchset. If the user hasn't checked it out, tell them how:
```
git fetch https://<host>/a/<project> refs/changes/<last2>/<number>/<patchset> && git checkout FETCH_HEAD
```
(The fetch ref is available in the query output under `revisions.<sha>.ref`.)

### 5. Build and Test

After all comments are processed:

1. Build the project using the workspace build tooling (e.g., `dev-tools build`, or `make` in the build directory).
2. Run the tests using the workspace test tooling (e.g., `dev-tools test`, or `ctest`).
3. If build or test failures occur:
   - Diagnose and fix the issue
   - Re-run until green
   - Note any additional changes made in the recap

### 6. Final Recap

Once build and tests pass, print a recap formatted for easy copy-paste into the Gerrit Reply dialog:

```
============================================================
Change <NUMBER> — REVIEW RESPONSE RECAP
<subject>
https://g1.sfl.io/c/<project>/+/<NUMBER>
============================================================

## Comment 1: <file>:<line> — @<author>
**Comment:** <original>
**Action:** <Fixed / Responded / Skipped>
**Response:**
> <reply to post on Gerrit>

## Comment 2: ...
(repeat for all unresolved comments)

============================================================
SUMMARY
============================================================
- Comments addressed: N
- Code changes made: N
- Responses only: N
- Skipped: N
- Build: PASS
- Tests: PASS

Next steps:
1. Review the local edits.
2. Amend the change and push:
     git add -u && git commit --amend --no-edit
     git push origin HEAD:refs/for/<branch>
3. In the Gerrit Reply dialog, paste the per-comment responses above
   and mark the threads resolved.
============================================================
```

## Important Rules

- **NEVER** run `gerrit-review.py draft` or any command that posts to Gerrit.
- **NEVER** run `git commit`, `git commit --amend`, `git push`, or modify the remote.
- All responses are **drafts** printed in the chat for the user to review and post manually.
- If the helper script is not authenticated or unavailable, inform the user and stop.
- Only consider **unresolved** comments; skip resolved threads entirely.
- Process comments grouped by file, then by line number, for logical grouping.
- The default Gerrit server is `https://g1.sfl.io`; pass `--server` to the helper if the user works with a different instance.
