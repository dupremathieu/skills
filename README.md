# dupremathieu-skills — Claude Code plugin marketplace

A personal collection of Claude Code plugins, packaged so they can be installed via the Claude Code marketplace mechanism.

## Plugins

| Plugin | What it does |
|---|---|
| `gerrit` | `/review-gerrit` to leave draft comments on a Gerrit query, and a `fix-gerrit-reviews` skill that addresses unresolved comments locally. Bundles `gerrit-review.py` (REST API helper, libsecret-backed auth). |
| `github-pr` | `/review-pr` to print a structured review of a GitHub PR, and a `fix-pr-reviews` skill that addresses review threads locally. Uses the `gh` CLI. |
| `cqfd` | Help authoring and troubleshooting cqfd setups (`.cqfdrc`, Dockerfile, build flavors, release archives). |
| `nano-banana` | Generate/edit images with Nano Banana 2 (Gemini 3.1 Flash Image Preview). Bundles the `nano-banana` CLI wrapper. |
| `slidev-sfl` | Create Savoir-faire Linux branded opening/closing slides for Slidev presentations. |
| `seapath-virtual-sandbox` | Provision, boot, and operate the 3-node SEAPATH virtual sandbox (QEMU/KVM via Terraform + Ansible). |

All `fix-*` skills are read-only — they apply local edits and print drafts, but never commit, push, amend, or post to remote services.

## Install

In Claude Code, add this repo as a marketplace, then install the plugins you want:

```text
/plugin marketplace add dupremathieu/skills
/plugin install gerrit@dupremathieu-skills
/plugin install github-pr@dupremathieu-skills
/plugin install nano-banana@dupremathieu-skills
# ...etc
```

To install from a local clone instead of GitHub:

```text
/plugin marketplace add /path/to/this/repo
```

(The marketplace manifest is `.claude-plugin/marketplace.json`; Claude Code finds it automatically given the repo root.)

## External requirements per plugin

Plugins bundle the scripts they ship, but each still has external dependencies:

- **gerrit** — Python 3 with `requests` and `secretstorage` (libsecret keyring). First use: `! python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gerrit-review.py" store-password`.
- **github-pr** — `gh` CLI authenticated against the relevant host.
- **nano-banana** — A Gemini API key in `~/.config/nano-banana/config` or the `GEMINI_API_KEY` environment variable.
- **seapath-virtual-sandbox** — A local clone of [seapath-virtual-sandbox](https://github.com/dupremathieu/seapath-virtual-sandbox) and the [seapath/ansible](https://github.com/seapath/ansible) repo, plus libvirt/QEMU/Terraform on the host. See `plugins/seapath-virtual-sandbox/skills/seapath-virtual-sandbox/references/install.md`.
- **slidev-sfl** — Slidev project where the generated slides are inserted.
- **cqfd** — Docker and (optionally) [`cqfd`](https://github.com/savoirfairelinux/cqfd) on the host.

## Repo layout

```
.claude-plugin/marketplace.json   # marketplace manifest, lists every plugin
plugins/<name>/
  .claude-plugin/plugin.json      # per-plugin manifest
  skills/<skill>/SKILL.md         # skills (loaded on demand by Claude)
  commands/<cmd>.md               # slash commands (optional)
  scripts/                        # bundled helper scripts (optional)
```

Bundled scripts are referenced from skills/commands via `${CLAUDE_PLUGIN_ROOT}` (the absolute path to the plugin's root, set by Claude Code when the plugin is loaded). Nothing relies on `$PATH` or on scripts being symlinked into `~/.claude/`.
