---
name: nano-banana
description: >-
  Generate or edit images using Nano Banana 2 (Gemini 3.1 Flash Image Preview).

  Use this skill when:
  - The user wants to generate an image from a text prompt
  - The user wants to edit or transform an existing image using AI
  - The user mentions Nano Banana, Gemini image generation, or gemini-3.1-flash-image-preview
  - The user wants to configure their Gemini API key for image generation
argument-hint: '"prompt" [-o output.png] [-i input.png] [-a aspect-ratio] [-s size]'
---

# Nano Banana 2 — Image Generation Skill

Generate and edit images using the `nano-banana` CLI tool, which wraps the Gemini 3.1 Flash Image Preview model.

## Prerequisites

The `nano-banana` binary ships with this plugin at `${CLAUDE_PLUGIN_ROOT}/skills/nano-banana/bin/nano-banana`. Always invoke it through that absolute path — do not assume it is on `$PATH`. For brevity, set once: `NB="${CLAUDE_PLUGIN_ROOT}/skills/nano-banana/bin/nano-banana"`.

The API key must be configured in `~/.config/nano-banana/config`, or via the `GEMINI_API_KEY` environment variable (which takes precedence).

## Commands

### Generate an image from text

```bash
"$NB" generate "A futuristic city at sunset" -o city.png
```

### Edit an existing image

```bash
"$NB" edit "Make the sky purple and add flying cars" -i photo.png -o edited.png
```

### Options

| Option | Description | Default |
|---|---|---|
| `-o, --output FILE` | Output file path | `nano-banana-<timestamp>.png` |
| `-i, --input FILE` | Input image (for edit mode) | — |
| `-a, --aspect-ratio AR` | `1:1`, `16:9`, `9:16`, `4:3`, `3:4` | `1:1` |
| `-s, --size SIZE` | `1K` or `2K` | `1K` |
| `-m, --model MODEL` | Override model name | `gemini-3.1-flash-image-preview` |

## Workflow when invoked

1. Check that the API key is configured. If not, guide the user to set it up.
2. Build and run the appropriate `nano-banana` command based on the user's request.
3. If the user provides an image file, use the `edit` subcommand with `-i`.
4. Display the output file path so the user can open the generated image.
5. If the command fails, show the error and suggest fixes (e.g., invalid key, unsupported format).

## Supported image formats

Input: PNG, JPEG, WebP, GIF
Output: PNG

