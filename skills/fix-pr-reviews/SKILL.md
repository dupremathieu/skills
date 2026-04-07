---
name: fix-pr-reviews
description: "Respond to and fix GitHub PR review comments. Use when: fixing PR remarks, addressing PR feedback, resolving PR review comments, handling code review, processing pull request discussions. Reads PR comments via gh CLI, applies fixes locally, builds, tests, and produces a recap for closing discussions."
argument-hint: "PR number or URL (e.g. 42 or https://github.com/org/repo/pull/42)"
---

# Fix PR Reviews

Respond to GitHub PR review comments locally: apply fixes, build, test, and produce a recap of responses ready to post. **Does NOT commit or push code, and does NOT post replies on GitHub.**

## When to Use

- A PR has review comments that need to be addressed
- You want to process all open review threads in one pass
- You need a draft recap of all responses before posting them manually

## Procedure

### 1. Identify the PR

- If the user provides a PR number or URL, use it directly.
- If not provided, detect the current branch and find its open PR:
  ```
  gh pr list --head "$(git branch --show-current)" --state open --json number,title --jq '.[0].number'
  ```

### 2. Fetch PR Review Comments

Retrieve all review comments (not yet resolved) for the PR:

```bash
gh pr view <PR_NUMBER> --json reviews,reviewThreads,title,body
```

Also fetch individual review thread details:

```bash
gh api "repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments" --paginate
```

Parse and group comments by:
- File path and line number
- Review thread (conversation chain)
- Whether the thread is resolved or unresolved

**Skip resolved/closed threads entirely — do not display, fix, or include them in the recap.**

### 3. Process Each Review Comment

For **each** unresolved review comment, do the following **in order**:

#### 3a. Display the Remark

Print in the chat:
```
---
### Review Comment #N — @reviewer
**File:** `path/to/file.cpp` (line X-Y)
**Comment:** <reviewer's comment text>
---
```

#### 3b. Analyze and Decide

Evaluate whether the comment:
- **Requires a code change** (bug fix, style fix, logic improvement)
- **Is a question** that needs an explanation only
- **Is not relevant** (outdated, already addressed, or disagree with reason)

#### 3c. Apply Fix or Draft Response

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

### 4. Build and Test

After all comments are processed:

1. **Build the project** using the workspace build tooling (e.g., `dev-tools build` task, or `make` in the build directory).
2. **Run the tests** using the workspace test tooling (e.g., `dev-tools test` task, or `ctest` in the build directory).
3. If build or test failures occur:
   - Diagnose and fix the issue
   - Re-run until green
   - Note any additional changes made in the recap

### 5. Final Recap

Once build and tests pass, print a **complete recap** formatted for easy copy-paste into GitHub:

```
============================================================
PR #<NUMBER> — REVIEW RESPONSE RECAP
============================================================

## Thread 1: <file>:<line> — @reviewer
**Comment:** <original comment>
**Action:** <Fixed / Responded / Skipped>
**Response:**
> <the response to post on GitHub>

## Thread 2: ...
(repeat for all threads)

============================================================
SUMMARY
============================================================
- Threads addressed: N
- Code changes made: N
- Responses only: N
- Skipped: N
- Build: PASS ✓
- Tests: PASS ✓

All threads above can be resolved after posting the responses.
============================================================
```

## Important Rules

- **NEVER** run `gh pr review`, `gh pr comment`, or any command that posts to GitHub.
- **NEVER** run `git commit`, `git push`, or modify the remote in any way.
- All responses are **drafts** printed in the chat for the user to review and post manually.
- If the `gh` CLI is not authenticated or unavailable, inform the user and stop.
- Process comments in file order for logical grouping.
