---
name: openrouter-image
description: >-
  Generate or edit images through OpenRouter's Image API.

  Use this skill when:
  - The user wants to generate an image from a text prompt
  - The user wants to edit or transform an existing image with an AI model
  - The user wants to use OpenRouter image models, GPT Image, Nano Banana,
    or another OpenRouter image provider
  - The user wants to list or select an OpenRouter image-generation model
  - The user wants to configure an OpenRouter API key for image generation
argument-hint: 'generate|edit|models "prompt" [-o output.png] [-m model]'
---

# OpenRouter Image Generation Skill

Generate and edit images with the bundled OpenRouter Image API CLI. OpenRouter
can route requests to models from OpenAI, Google, and other providers.

## Prerequisites

The CLI is bundled at `${CLAUDE_PLUGIN_ROOT}/scripts/openrouter-image`. Always
invoke it through that absolute path. For brevity, set once:

```bash
OR_IMAGE="${CLAUDE_PLUGIN_ROOT}/scripts/openrouter-image"
```

The CLI needs Python 3 and an OpenRouter API key. The key is read from the
`OPENROUTER_API_KEY` environment variable first, then from
`~/.config/openrouter-image/config`.

OpenRouter usage is billed by OpenRouter. A ChatGPT Plus or Pro subscription
does not provide an OpenRouter API key or OpenRouter credits.

## Commands

### Generate an image

```bash
"$OR_IMAGE" generate "A futuristic city at sunset" -o city.png
```

### Edit an existing image

```bash
"$OR_IMAGE" edit "Make the sky purple and add flying cars" \
  -i photo.png -o edited.png
```

### List available image models

```bash
"$OR_IMAGE" models
```

Use `--json` when model metadata or supported parameters need to be inspected
programmatically. Use `--model` to select a model explicitly. The default is
`openai/gpt-image-2`.

## Options

| Option | Description | Default |
|---|---|---|
| `-o, --output FILE` | Output image path | Generated timestamped path |
| `-i, --input FILE` | Input image for edit mode | -- |
| `-m, --model MODEL` | OpenRouter model ID | `openai/gpt-image-2` |
| `-a, --aspect-ratio AR` | Requested aspect ratio | `1:1` |
| `-s, --resolution RES` | `512`, `1K`, `2K`, or `4K` | `1K` |
| `-q, --quality QUALITY` | `auto`, `low`, `medium`, or `high` | Provider default |
| `--output-format FORMAT` | `png`, `jpeg`, `webp`, or `svg` | Provider default |
| `--json` | Print raw model metadata with `models` | Off |

## Configuration

```bash
"$OR_IMAGE" config set-key
"$OR_IMAGE" config show
```

## Workflow when invoked

1. Check that an OpenRouter API key is configured. If not, guide the user to
   set `OPENROUTER_API_KEY` or run `config set-key`.
2. If the user names a model, pass it with `--model`.
3. If the user does not name a model and the default is unsuitable, run
   `models` and choose a model whose metadata supports the requested inputs
   and parameters.
4. Use `edit` with `-i` when the user provides an image to transform.
5. Display the output file path after the image is saved.
6. If the API rejects a parameter, inspect `models --json` and retry with the
   selected model's supported parameters.

## Supported input formats

PNG, JPEG, WebP, and GIF inputs are sent as base64 data URLs. Output format
depends on the selected model and the requested `--output-format`.
