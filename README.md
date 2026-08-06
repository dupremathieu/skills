# dupremathieu-skills — Claude Code plugin marketplace & skill.sh source

A personal collection of Claude Code plugins, packaged so they can be installed either via the Claude Code marketplace mechanism or as individual skills via [`npx skills`](https://skills.sh) (skill.sh).

## Plugins

| Plugin | What it does |
|---|---|
| `gerrit` | `/review-gerrit` to leave draft comments on a Gerrit query, and a `fix-gerrit-reviews` skill that addresses unresolved comments locally. Bundles `gerrit-review.py` (REST API helper, libsecret-backed auth). |
| `github-pr` | `/review-pr` to print a structured review of a GitHub PR, and a `fix-pr-reviews` skill that addresses review threads locally. Uses the `gh` CLI. |
| `cqfd` | Help authoring and troubleshooting cqfd setups (`.cqfdrc`, Dockerfile, build flavors, release archives). |
| `openrouter-image` | Generate/edit images through OpenRouter's Image API. Bundles the `openrouter-image` Python CLI. |
| `slidev-sfl` | Create Savoir-faire Linux branded opening/closing slides for Slidev presentations. |
| `seapath-virtual-cluster` | Provision, boot, and operate the 3-node SEAPATH virtual cluster (QEMU/KVM via Terraform + Ansible). |
| `redmine` | `export-redmine-issues` skill that fetches every issue of a Redmine project and writes Markdown files under `tasks/<target-version>/`. Bundles `redmine.py` (REST helper, libsecret-backed auth). |

All `fix-*` skills are read-only — they apply local edits and print drafts, but never commit, push, amend, or post to remote services.

## Install

In Claude Code, add this repo as a marketplace, then install the plugins you want:

```text
/plugin marketplace add dupremathieu/skills
/plugin install gerrit@dupremathieu-skills
/plugin install github-pr@dupremathieu-skills
/plugin install openrouter-image@dupremathieu-skills
# ...etc
```

To install from a local clone instead of GitHub:

```text
/plugin marketplace add /path/to/this/repo
```

(The marketplace manifest is `.claude-plugin/marketplace.json`; Claude Code finds it automatically given the repo root.)

## Install with `npx skills` (skill.sh)

The `skills` CLI discovers every skill through the same `.claude-plugin/marketplace.json` manifest, so the repo works as a skill.sh source without extra metadata:

```bash
# List the skills available in this repo
npx skills add dupremathieu/skills --list

# Install specific skills (globally, for the agents you use)
npx skills add dupremathieu/skills --skill fix-gerrit-reviews --skill fix-pr-reviews -g
npx skills add dupremathieu/skills --skill export-redmine-issues -g

# Install everything to all detected agents, non-interactively
npx skills add dupremathieu/skills --all

# From a local clone instead of GitHub
npx skills add /path/to/this/repo
```

Skills installed this way are self-contained: bundled helpers (`gerrit-review.py`, `redmine.py`, `openrouter-image`) live inside each skill's `scripts/` directory and are copied with it, so they work outside the Claude Code plugin system. Skills resolve their helper via `CLAUDE_PLUGIN_ROOT` when running as a plugin, and fall back to the standard skill directories (`.claude/skills`, `.agents/skills`, `.config/opencode/skills`) when installed standalone. See the [skills CLI README](https://github.com/vercel-labs/skills) for `--agent`, `--copy`, and the other options.

## External requirements per plugin

Plugins bundle the scripts they ship, but each still has external dependencies:

- **gerrit** — Python 3 with `requests` and `secretstorage` (libsecret keyring). First use: `! python3 "${CLAUDE_PLUGIN_ROOT}/skills/fix-gerrit-reviews/scripts/gerrit-review.py" store-password`.
- **github-pr** — `gh` CLI authenticated against the relevant host.
- **openrouter-image** — Python 3 and an OpenRouter API key in `~/.config/openrouter-image/config` or the `OPENROUTER_API_KEY` environment variable. OpenRouter usage is billed separately from ChatGPT subscriptions.
- **seapath-virtual-cluster** — A local clone of [seapath-virtual-cluster](https://github.com/dupremathieu/seapath-virtual-cluster) and the [seapath/ansible](https://github.com/seapath/ansible) repo, plus libvirt/QEMU/Terraform on the host. See `plugins/seapath-virtual-cluster/skills/seapath-virtual-cluster/references/install.md`.
- **slidev-sfl** — Slidev project where the generated slides are inserted.
- **cqfd** — Docker and (optionally) [`cqfd`](https://github.com/savoirfairelinux/cqfd) on the host.
- **redmine** — Python 3 with `requests` and `secretstorage` (libsecret keyring). First use: `! python3 "${CLAUDE_PLUGIN_ROOT}/skills/export-redmine-issues/scripts/redmine.py" configure` to set the server URL and API key.

## Repo layout

```
.claude-plugin/marketplace.json   # marketplace manifest, lists every plugin and its skills
plugins/<name>/
  .claude-plugin/plugin.json      # per-plugin manifest
  skills/<skill>/
    SKILL.md                      # skill definition (loaded on demand by Claude/other agents)
    scripts/                      # bundled helper scripts (optional, shipped with the skill)
    references/                   # extra docs read on demand (optional)
  commands/<cmd>.md               # slash commands (optional, Claude Code only)
```

Bundled scripts live inside the skill directory (not at the plugin root), so they are included both when Claude Code installs the plugin and when `npx skills` installs the skill standalone. They are referenced from skills/commands via `${CLAUDE_PLUGIN_ROOT}` (set by Claude Code when the plugin is loaded) or resolved from the standard skill directories for standalone installs. Nothing relies on `$PATH` or on scripts being symlinked into `~/.claude/`.
