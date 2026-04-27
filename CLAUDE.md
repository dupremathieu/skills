# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This repo is a **Claude Code plugin marketplace**. It bundles several plugins, each containing skills, slash commands, and the scripts they need. There is no build system, no test suite, no package manifest — the artifacts are markdown + JSON manifests + helper scripts consumed by the Claude Code CLI.

## Layout

- `.claude-plugin/marketplace.json` — top-level marketplace manifest. Lists every plugin under `plugins/` with `source: "./plugins/<name>"`. Adding a new plugin means adding both its directory **and** an entry here.
- `plugins/<name>/.claude-plugin/plugin.json` — per-plugin manifest (name, version, description, author, keywords).
- `plugins/<name>/skills/<skill>/SKILL.md` — skill definitions (YAML frontmatter + body).
- `plugins/<name>/commands/<cmd>.md` — slash command definitions.
- `plugins/<name>/scripts/` (and similar) — bundled helper scripts (e.g. `plugins/gerrit/scripts/gerrit-review.py`, `plugins/nano-banana/skills/nano-banana/bin/nano-banana`).
- `README.md` — human-facing index of plugins and install instructions.

## Conventions when editing plugins

- **Reference bundled scripts via `${CLAUDE_PLUGIN_ROOT}`**, not `$PATH` and not `~/.claude/scripts/...`. Claude Code sets this env var to the plugin's absolute root when it loads the plugin. Example: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gerrit-review.py" query "..."`.
- **Frontmatter is load-bearing.** A malformed YAML block makes the skill invisible to the harness. Keep `name` and `description` present and valid.
- **Skill descriptions drive matching.** When adding triggers, list concrete user phrases ("fixing PR remarks", "addressing feedback") rather than abstract capabilities — Claude Code matches on this text.
- **Progressive disclosure.** For multi-file skills (see `plugins/seapath-virtual-sandbox`), keep `SKILL.md` short and gate large reference content behind explicit "read this file when X" instructions.
- **Read-only contract on `fix-*` skills.** `fix-gerrit-reviews` and `fix-pr-reviews` deliberately do **not** post replies, amend commits, or push — they print drafts for the user to apply manually. Preserve this contract.
- **Marketplace and plugin manifests must stay in sync.** When bumping a plugin's version in `plugins/<name>/.claude-plugin/plugin.json`, mirror it in `.claude-plugin/marketplace.json`. When renaming a plugin, update the `source` path too.

## Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with `name`, `version`, `description`.
2. Add skills under `plugins/<name>/skills/<skill>/SKILL.md` and/or commands under `plugins/<name>/commands/<cmd>.md`.
3. If the plugin needs helper scripts, put them inside the plugin directory and reference them through `${CLAUDE_PLUGIN_ROOT}`.
4. Append an entry to `.claude-plugin/marketplace.json`.
5. Update `README.md`.

## Local testing

Add the working tree as a local marketplace inside Claude Code:

```text
/plugin marketplace add /home/mathieu/Documents/skills
/plugin install <plugin-name>@dupremathieu-skills
```

Re-run `/plugin marketplace update dupremathieu-skills` after editing manifests.
