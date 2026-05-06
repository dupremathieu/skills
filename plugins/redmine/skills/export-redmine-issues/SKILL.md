---
name: export-redmine-issues
description: "Export all issues of a Redmine project to Markdown files, organized by Target version. Use when: exporting Redmine issues, dumping Redmine tickets to disk, archiving a Redmine project, generating offline Markdown copies of Redmine issues, syncing Redmine tasks into a tasks/ directory. Bundles a Python helper that talks to the Redmine REST API."
argument-hint: "Redmine project identifier (e.g. seapath) and optionally an output directory (default: tasks)"
---

# Export Redmine Issues

Fetch every issue of a Redmine project via the REST API and write each one as a Markdown file. Issues that have a Target version are grouped into a subdirectory named after that version; issues without one land directly in the root output directory.

## When to Use

- A user asks to **export**, **dump**, **archive**, or **sync offline** the issues of a Redmine project.
- A user wants **Markdown copies** of Redmine tickets to read, grep, or commit alongside code.
- A user wants the project's tickets organized **by Target version** on disk.

## Prerequisites

The helper script is bundled with this plugin at `${CLAUDE_PLUGIN_ROOT}/scripts/redmine.py`. Always invoke it through that path — do not assume it is on `$PATH`. It needs Python 3 with the `requests` and `secretstorage` packages.

First-time setup (the user runs this once per Redmine instance):

```bash
! python3 "${CLAUDE_PLUGIN_ROOT}/scripts/redmine.py" configure
```

`configure` prompts for the Redmine base URL (saved to `~/.config/redmine/config`) and the API key (saved to the libsecret keyring under `service=redmine, server=<host>`).

Smoke-test connectivity afterwards:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/redmine.py" projects
```

If this fails with an auth error, ask the user to re-run `configure`.

## Procedure

### 1. Resolve the Project Identifier

- If the user provides a project identifier (slug like `seapath`) or numeric id, use it directly.
- If the user is unsure, list projects and ask:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/redmine.py" projects
  ```

### 2. Confirm the Output Directory

- Default is `tasks/` in the current working directory (per the user's preference).
- Override with `--output <dir>` only if the user explicitly asks for a different location.

### 3. Run the Export

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/redmine.py" export <project> --output tasks
```

Useful flags to pass through when the user asks:

| Flag | Effect |
|---|---|
| `--open-only` | Skip closed issues. |
| `--status <id>` | Only issues with this `status_id`. |
| `--no-journals` | Skip per-issue detail fetch (no journal, no checklist). Much faster on large projects. |
| `--workers N` | Parallel detail fetches (default 8). |

### 4. Summarize the Result

After the script finishes, report back to the user:
- The total number of issues exported.
- The number of Target version subdirectories created.
- The number of unversioned issues placed at the top level.
- The output directory path.

The script prints a one-line summary on stderr that you can paraphrase, e.g. `Exported 142 issue(s) to tasks (5 version dir(s), 9 unversioned).`

### 5. Markdown Layout

Each `<id>-<slug>.md` file contains:

1. **YAML frontmatter** — `id`, `subject`, `tracker`, `status`, `priority`, `author`, `assignee`, `target_version`, `category`, `created_on`, `updated_on`, `done_ratio`, `url`.
2. **`# #<id> — <subject>`** heading.
3. **`## Description`** — the issue body.
4. **`## Checklist`** — GitHub-style task list (`- [x]` / `- [ ]`), only present if the Redmine Checklists plugin returned items for the issue.
5. **`## Journal`** — chronological list of comments and field changes, only present if the issue has any.

## Important Rules

- **Read-only on Redmine.** This skill only ever calls `GET` endpoints. Never use the helper to create, update, or delete issues — that is out of scope by design.
- **Only `export` writes to disk.** `projects`, `versions`, and `issues` print JSON / tables to stdout for inspection.
- **Never amend or push git state.** If the output directory is inside a git repo, leave staging and commits to the user.
- **Honor the user's flags exactly.** If they ask for `--open-only`, do not silently include closed issues — and vice versa.
- If `configure` has not been run (no config file or no API key in libsecret), stop and instruct the user to run it; do not attempt to prompt for credentials yourself.
