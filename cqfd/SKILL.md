---
name: cqfd
description: >-
  Help users work with cqfd (ce qu'il fallait Dockeriser), a tool by
  Savoir-faire Linux that wraps commands in Docker containers.

  Use this skill when:
  - The user wants to create, edit, or troubleshoot a .cqfdrc configuration file
  - The user wants to create or edit a Dockerfile for cqfd
  - The user asks about cqfd commands, options, or environment variables
  - The user wants to set up cqfd in a project
  - The user wants to add or manage build flavors
  - The user wants to configure release archives
argument-hint: [action or question]
---

# cqfd Skill

cqfd wraps commands in per-project Docker containers. It reads a `.cqfdrc` INI config file and a Dockerfile from `.cqfd/docker/` (or a flavor-specific subdirectory).

## Commands Reference

| Command | Description |
|---|---|
| `cqfd init` | Build the Docker image from the project Dockerfile |
| `cqfd deinit` | Remove the current container image |
| `cqfd run [cmd]` | Run the default or given command in the container |
| `cqfd exec <cmd> [args]` | Run an arbitrary command in the container |
| `cqfd shell [args]` | Open an interactive shell in the container |
| `cqfd release [cmd]` | Run command and create a release archive |
| `cqfd flavors` | List available build flavors |
| `cqfd images` | List all cqfd Docker images |
| `cqfd prune` | Remove all cqfd Docker images |

### Common Options

- `-b <flavor>` — target a specific build flavor
- `-f <file>` — use an alternate config file (default: `.cqfdrc`)
- `-d <dir>` — use an alternate cqfd directory (default: `.cqfd`)
- `-C <dir>` — change working directory before running
- `-q` — quiet mode
- `--verbose` — increase verbosity
- `--release` — shorthand for the release command
- `-c <args>` — append args to the default command (for `run`/`release`)

## .cqfdrc Configuration Reference

The `.cqfdrc` file uses INI syntax with `#` comments.

### [project] Section

| Key | Required | Description |
|---|---|---|
| `org` | yes | Organization name (short, lowercase, no spaces) |
| `name` | yes | Project name (short, lowercase, no spaces) |
| `build_context` | no | Directory for Docker build context (default: `.cqfd/docker`) |
| `custom_img_name` | no | Custom Docker image name, optionally with registry URL |

### [build] Section

| Key | Required | Description |
|---|---|---|
| `command` | yes | Default shell command to run in the container |
| `distro` | no | Subdirectory under `.cqfd/` containing the Dockerfile (default: `docker`) |
| `files` | no | Space-separated list of files to include in release archives |
| `archive` | no | Release archive filename template (see template marks below) |
| `tar_transform` | no | `yes`/`true` to store files at archive root |
| `tar_options` | no | Extra options passed to tar |
| `user_extra_groups` | no | Space-separated list of extra groups for the container user |
| `docker_build_args` | no | Extra arguments for `docker build` |
| `docker_run_args` | no | Extra arguments for `docker run` |
| `docker_rmi_args` | no | Extra arguments for `docker rmi` |
| `bind_docker_sock` | no | Set to `true` to forward Docker socket into container |

### Build Flavors

Flavors are additional INI sections that override `[build]` keys. Define a section named after the flavor:

```ini
[build]
command=make

[centos7]
command='make CENTOS=1'
distro='centos7'

[debian]
command='make DEBIAN=1'
distro='debian'
```

Each flavor can override: `command`, `distro`, `files`, `archive`, `tar_transform`, `tar_options`, `user_extra_groups`, `docker_build_args`, `docker_run_args`, `docker_rmi_args`, `bind_docker_sock`.

Usage: `cqfd -b centos7 run`

### Release Archive Template Marks

| Mark | Expands to |
|---|---|
| `%Gh` | Git short hash |
| `%GH` | Git long hash |
| `%D3` | RFC 3339 date |
| `%Du` | Unix timestamp |
| `%Cf` | Current flavor name |
| `%Po` | project.org value |
| `%Pn` | project.name value |
| `%%` | Literal `%` |

Supported formats: `.tar.xz`, `.tar.gz`, `.zip`. Default: `org-name.tar.xz`.

## Environment Variables

| Variable | Description |
|---|---|
| `CQFD_DOCKER` | Container engine command (default: `docker`, set to `podman` for Podman) |
| `CQFD_EXTRA_RUN_ARGS` | Additional `docker run` arguments |
| `CQFD_EXTRA_BUILD_ARGS` | Additional `docker build` arguments |
| `CQFD_EXTRA_RMI_ARGS` | Additional `docker rmi` arguments |
| `CQFD_SHELL` | Shell to use in container (default: `/bin/bash`) |
| `CQFD_DOCKER_GID` | Map host docker group GID |
| `CQFD_NO_SSH_CONFIG` | Disable `/etc/ssh` forwarding |
| `CQFD_NO_USER_SSH_CONFIG` | Disable `~/.ssh` forwarding |
| `CQFD_NO_USER_GIT_CONFIG` | Disable `~/.gitconfig` forwarding |
| `CQFD_NO_SSH_AUTH_SOCK` | Disable SSH auth socket forwarding |
| `CQFD_BIND_DOCKER_SOCK` | Enable Docker socket forwarding |
| `CQFD_DISABLE_SHELL_HISTORY` | Disable shell history bind mounting |

## Docker Image Naming

Unless `custom_img_name` is set, images are named: `cqfd_<username>_<org>_<name>_<hash>`

The hash is derived from the Dockerfile content, so `cqfd init` rebuilds only when the Dockerfile changes.

## How to Help the User

### Creating a new .cqfdrc

1. Ask the user about their project: organization, name, build system, target distro(s)
2. Create the `.cqfdrc` file with `[project]` and `[build]` sections
3. If the user needs multiple target environments, create flavor sections
4. Create the `.cqfd/docker/Dockerfile` (or flavor-specific subdirectories)
5. Remind the user to run `cqfd init` to build the image

### Troubleshooting

- If `cqfd init` fails: check the Dockerfile syntax and that Docker is running
- If permissions are wrong on build artifacts: check `user_extra_groups` or `docker_run_args`
- If SSH/git doesn't work in container: check `CQFD_NO_*` environment variables
- For Podman: set `CQFD_DOCKER=podman`
- To rebuild from scratch: `cqfd deinit && cqfd init`

### Example: Minimal Setup

`.cqfdrc`:
```ini
[project]
org=myorg
name=myproject

[build]
command=make
```

`.cqfd/docker/Dockerfile`:
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y build-essential
```

### Example: Multi-Flavor Setup

`.cqfdrc`:
```ini
[project]
org=myorg
name=myproject

[build]
command=make
files=build/output.bin
archive=%Po-%Pn-%Gh.tar.xz

[ubuntu]
command='make UBUNTU=1'
distro='ubuntu'

[fedora]
command='make FEDORA=1'
distro='fedora'
```

With directories:
```
.cqfd/
  ubuntu/
    Dockerfile
  fedora/
    Dockerfile
```
